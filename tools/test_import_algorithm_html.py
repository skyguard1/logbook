import json
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

from bs4 import BeautifulSoup
from import_algorithm_html import (
    MANIFEST, POSTS, Scrubber, clean_dom, clean_image_bytes, extract, local_file, run,
)


def png_chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))


def tiny_png():
    return (b'\x89PNG\r\n\x1a\n'
            + png_chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            + png_chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff'))
            + png_chunk(b'IEND', b''))


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        self.repo = self.base / 'repo'
        self.source.mkdir()
        self.repo.mkdir()
        (self.repo / '_config.yml').write_text('url: https://example.org/logbook\n')

    def article(self, name, body):
        path = self.source / name
        path.write_text('<div id="mce_view_content">' + body + '</div><footer>PRIVATE FOOTER</footer>')
        return path

    def test_dom_preserves_intervening_paragraphs_and_code(self):
        path = self.article('测试 - 资金与数据部 - KM平台.html', '')
        soup = BeautifulSoup('<div><p>前文</p><p>算法原理</p><p>参考 <a href="https://km.woa.com/x">论文</a></p><p><span>腾</span><span>讯</span>技术</p><pre><code><span>Map&lt;String, T&gt;</span><br>return x;</code></pre><script>bad()</script></div>', 'html.parser')
        clean_dom(soup.div, Scrubber([path]))
        self.assertIn('前文', soup.get_text())
        self.assertIn('算法原理', soup.get_text())
        self.assertIn('论文', soup.get_text())
        self.assertIn('Map<String, T>\nreturn x;', soup.pre.get_text())
        self.assertNotIn('腾讯', str(soup))
        self.assertNotIn('woa.com', str(soup))
        self.assertIsNone(soup.script)
        self.assertIsNone(soup.pre.span)

    def test_images_topics_idempotence_and_manual_edit_protection(self):
        path = self.article('GNN算法 - 资金与数据部 - KM平台.html', '<p>GNN 原理</p><img src="./图_files/cos-file-url"><img data-src="./图_files/cos-file-url"><img src="./图_files/missing">')
        assets = self.source / '图_files'
        assets.mkdir()
        (assets / 'cos-file-url').write_bytes(tiny_png())
        first = run(self.source, self.repo)
        self.assertEqual(first['unique_images'], 1)
        self.assertEqual(first['images']['resolved_images'], 2)
        self.assertEqual(first['images']['missing_images'], 1)
        self.assertEqual(first['topics'], {'图学习与知识图谱': 1})
        out = self.repo / first['articles'][0]['path']
        text = out.read_text()
        self.assertIn('  - 算法\n  - 图学习与知识图谱', text)
        self.assertIn('/logbook/images/algorithm/', text)
        self.assertNotIn('资金与数据部', text)
        self.assertNotIn('PRIVATE FOOTER', text)
        before = (self.repo / MANIFEST).read_bytes()
        run(self.source, self.repo)
        self.assertEqual(before, (self.repo / MANIFEST).read_bytes())
        out.write_text(text + 'manual edit')
        with self.assertRaisesRegex(ValueError, 'edited file'):
            run(self.source, self.repo)
        self.assertTrue(out.read_text().endswith('manual edit'))

    def test_source_failure_does_not_delete_outputs(self):
        self.article('文章.html', '<p>正文</p>')
        report = run(self.source, self.repo)
        out = self.repo / report['articles'][0]['path']
        with self.assertRaises(ValueError):
            run(self.base / 'missing', self.repo)
        self.assertTrue(out.exists())

    def test_iframe_extraction_and_path_traversal(self):
        nested = self.source / 'page_files'
        nested.mkdir()
        (nested / 'viewpage.html').write_text('<div id="main-content" class="wiki-content">iWiki 正文<img src="pic.png"></div>')
        page = self.source / 'page.html'
        page.write_text('<iframe src="page_files/viewpage.html"></iframe>')
        body, origin = extract(page, self.source)
        self.assertEqual(origin, (nested / 'viewpage.html').resolve())
        self.assertIn('iWiki 正文', body.get_text())
        self.assertIsNone(local_file('../repo/_config.yml', page, self.source))
        self.assertIsNone(local_file('https://example.org/img', page, self.source))
        (nested / 'viewpage.html').write_text('<iframe src="../page.html"></iframe>')
        self.assertIsNone(extract(page, self.source))

    def test_no_placeholder_articles_and_dry_run(self):
        self.article('正文.html', '<p>保留正文</p>')
        (self.source / 'preview.html').write_text('<p>PDF viewer chrome</p>')
        report = run(self.source, self.repo, dry_run=True)
        self.assertEqual(len(report['skipped']), 1)
        self.assertEqual(len(report['articles']), 1)
        self.assertFalse((self.repo / POSTS).exists())
        self.assertFalse((self.repo / MANIFEST).exists())

    def test_collision_and_template_text(self):
        self.article('文章 - 部门A - KM平台.html', '<p>{% endraw %} {{ secret }} Alpha</p>')
        self.article('文章 - 部门B - KM平台.html', '<p>Beta</p>')
        report = run(self.source, self.repo)
        paths = [row['path'] for row in report['articles']]
        self.assertEqual(len(set(paths)), 2)
        self.assertNotIn('{{ secret }}', (self.repo / paths[0]).read_text())
        self.assertEqual(json.loads((self.repo / MANIFEST).read_text())['sources'], 2)

    def test_technical_identifiers_and_department_redaction(self):
        scrub = Scrubber([])
        self.assertEqual(scrub('import google.protobuf; GoogleNet'), 'import google.protobuf; GoogleNet')
        self.assertEqual(scrub('云架构平台部：模型训练'), '：模型训练')
        self.assertNotIn('腾讯', scrub('腾讯提出一种模型'))
        self.assertNotIn('woa.com', scrub('参考 https://km.woa.com/a'))

    def test_unmanaged_file_is_not_overwritten(self):
        self.article('article.html', '<p>正文</p>')
        preview = run(self.source, self.repo, dry_run=True)
        path = self.repo / preview['articles'][0]['path']
        path.parent.mkdir(parents=True)
        path.write_text('personal note')
        with self.assertRaisesRegex(ValueError, 'unmanaged'):
            run(self.source, self.repo)
        self.assertEqual(path.read_text(), 'personal note')

    def test_png_metadata_removal_keeps_pixel_chunks(self):
        original = tiny_png()
        with_metadata = original[:-12] + png_chunk(b'tEXt', b'Company\x00private') + original[-12:]
        self.assertEqual(clean_image_bytes(with_metadata, 'png', Scrubber([])), original)
        with self.assertRaises(ValueError):
            clean_image_bytes(original[:-5], 'png', Scrubber([]))

    def test_svg_stays_valid_xml_and_preserves_case(self):
        data = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><defs><linearGradient id="g"/></defs><rect fill="url(#g)" width="10" height="10"/><script>bad()</script></svg>'
        output = clean_image_bytes(data, 'svg', Scrubber([]))
        root = ET.fromstring(output)
        self.assertEqual(root.get('viewBox'), '0 0 10 10')
        self.assertIsNotNone(root.find('.//{*}linearGradient'))
        self.assertEqual(root.find('.//{*}rect').get('fill'), 'url(#g)')
        self.assertIsNone(root.find('.//{*}script'))


if __name__ == '__main__':
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from import_algorithm_platform_html import AlgorithmPlatformScrubber, MANIFEST, POSTS, run
from import_recommender_system_html import run as import_system
from test_import_algorithm_html import tiny_png


class AlgorithmPlatformTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source, self.repo = self.root / 'html', self.root / 'repo'
        self.source.mkdir()
        self.repo.mkdir()
        (self.repo / '_config.yml').write_text('url: https://example.org/logbook\n')
        self.name = '当图神经网络遇上社交推荐 - PlatoDeep在微信朋友圈广告中应用 - WXG技术架构部 - KM平台.html'
        (self.source / self.name).write_text(
            '<div id="mce_view_content"><p><span>腾讯</span>信息安全部-技术研发中心：技术内容</p>'
            '<p>部门：不应保留</p><p>Google模型 Tencent模型</p>'
            '<img src="./a_files/cos-file-url"><img src="missing.png">'
            '<pre><span>Map&lt;String, T&gt; model;</span><br>google.protobuf</pre>'
            '<a href="https://km.woa.com/private">模型原理</a></div>')
        assets = self.source / 'a_files'
        assets.mkdir()
        (assets / 'cos-file-url').write_bytes(tiny_png())

    def test_subtitle_is_not_learned_as_organisation(self):
        scrub = AlgorithmPlatformScrubber([self.source / self.name])
        subtitle = 'PlatoDeep在朋友圈广告中应用'
        self.assertEqual(scrub.title(Path(self.name)), '当图神经网络遇上社交推荐 - ' + subtitle)
        self.assertEqual(scrub(subtitle), subtitle)
        self.assertEqual(scrub.title(Path('【CVPR 2022】模型 - KM平台.html')), '【CVPR 2022】模型')
        self.assertEqual(scrub.title(Path('【腾讯微创新奖201906期】短视频推荐 - KM平台.html')), '短视频推荐')
        self.assertEqual(scrub.title(Path('【数据分析】KG-BERT - 互娱增值服务部 - 技术&服务藏经阁 - KM平台.html')), '【数据分析】KG-BERT')

    def test_import_content_images_and_redaction(self):
        report = run(self.source, self.repo)
        text = (self.repo / report['articles'][0]['path']).read_text()
        self.assertIn('  - 算法平台\n  - 图学习与图计算\n', text)
        self.assertIn('/logbook/images/algorithm-platform/', text)
        self.assertEqual(report['unique_images'], 1)
        self.assertEqual(report['images']['missing_images'], 1)
        for value in ('技术内容', '模型原理', 'Map&lt;String, T&gt;', 'google.protobuf'):
            self.assertIn(value, text)
        for value in ('腾讯', 'WXG', '信息安全部', '技术研发中心', 'Google模型', 'Tencent模型', 'woa.com', '<span', '不应保留'):
            self.assertNotIn(value, text)

    def test_repeat_import_and_other_category_untouched(self):
        previous = import_system(self.source, self.repo)
        previous_files = {p: (self.repo / p).read_bytes() for p in previous['files']}
        report = run(self.source, self.repo)
        before = (self.repo / MANIFEST).read_bytes()
        self.assertEqual(report, run(self.source, self.repo))
        self.assertEqual(before, (self.repo / MANIFEST).read_bytes())
        for path, data in previous_files.items():
            self.assertEqual((self.repo / path).read_bytes(), data)

    def test_manual_edits_and_empty_source_protected(self):
        report = run(self.source, self.repo)
        post = self.repo / report['articles'][0]['path']
        post.write_text(post.read_text() + '\nmanual note')
        with self.assertRaisesRegex(ValueError, 'edited file'):
            run(self.source, self.repo)
        self.assertTrue(post.read_text().endswith('manual note'))
        (self.source / self.name).unlink()
        with self.assertRaises(ValueError):
            run(self.source, self.repo)
        self.assertTrue(post.exists())

    def test_iwiki_nested_exports_and_dry_run(self):
        (self.source / '设计 - 腾讯iWiki.html').write_text('<div id="main-content" class="wiki-content"><p>设计内容</p></div>')
        (self.source / '预览.html').write_text('<iframe src="https://example.org/doc.pdf"></iframe>')
        (self.source / 'a_files/decoration.html').write_text('<div id="article_content">非文章</div>')
        report = run(self.source, self.repo, True)
        self.assertEqual(report['sources'], 3)
        self.assertEqual(len(report['articles']), 2)
        self.assertEqual(len(report['skipped']), 1)
        self.assertFalse((self.repo / POSTS).exists())

    def test_root_deployment_and_title_collisions(self):
        (self.repo / '_config.yml').write_text('root: /\n')
        for company in ('腾讯', '百度'):
            (self.source / f'{company}模型 - KM平台.html').write_text('<div id="article_content">正文</div>')
        report = run(self.source, self.repo)
        self.assertEqual(len(report['articles']), 3)
        self.assertEqual(len({a['path'] for a in report['articles']}), 3)
        text = (self.repo / report['articles'][0]['path']).read_text()
        self.assertIn('src="/images/algorithm-platform/', text)

    def test_markdown_iframe_uses_rendered_content_not_base64(self):
        folder = self.source / 'page_files'
        folder.mkdir()
        (folder / 'cos-file-url').write_bytes(tiny_png())
        (folder / 'preview.html').write_text('<div class="markdown-body"><h2>可见正文</h2><p>腾讯技术</p><img src="./cos-file-url"><pre>Map&lt;K, V&gt;</pre></div>')
        (self.source / 'Markdown - 腾讯iWiki.html').write_text(
            '<div id="main-content" class="wiki-content"><div data-macro-name="md">'
            '<div class="md-code-placeholder"><pre>SElEREVO</pre></div>'
            '<iframe src="./page_files/preview.html"></iframe></div></div>')
        report = run(self.source, self.repo)
        row = next(a for a in report['articles'] if a['title'] == 'Markdown')
        text = (self.repo / row['path']).read_text()
        self.assertIn('可见正文', text)
        self.assertIn('Map&lt;K, V&gt;', text)
        self.assertNotIn('SElEREVO', text)
        self.assertNotIn('腾讯', text)
        self.assertNotIn('<iframe', text)
        self.assertEqual(row['images']['resolved_images'], 1)

    def test_missing_markdown_preview_does_not_publish(self):
        (self.source / 'Markdown.html').write_text('<div id="article_content"><div data-macro-name="cherry"><pre>SElEREVO</pre><iframe src="https://example.org/private"></iframe></div></div>')
        with self.assertRaisesRegex(ValueError, 'Missing rendered Markdown preview'):
            run(self.source, self.repo)
        self.assertFalse((self.repo / MANIFEST).exists())

    def test_bare_and_malformed_internal_urls(self):
        path = self.source / self.name
        path.write_text(path.read_text().replace('</div>', '<p>code.oa.com/project/file。保留说明</p><a href="http://https//km.woa.com/private">参考文献</a><a href="https://github.com/Tencent/plato">https://github.com/Tencent/plato</a></div>'))
        report = run(self.source, self.repo)
        text = (self.repo / report['articles'][0]['path']).read_text()
        self.assertNotIn('oa.com', text)
        self.assertNotIn('woa.com', text)
        self.assertIn('保留说明', text)
        self.assertIn('参考文献', text)
        self.assertIn('href="https://github.com/Tencent/plato"', text)
        self.assertIn('开源项目：plato', text)


if __name__ == '__main__':
    unittest.main()

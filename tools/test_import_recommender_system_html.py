import tempfile
import unittest
from pathlib import Path

from import_recommendation_html import run as import_recommendation
from import_recommender_system_html import MANIFEST, POSTS, RecommenderSystemScrubber, run
from test_import_algorithm_html import tiny_png


class RecommenderSystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.repo = self.root / 'html', self.root / 'repo'
        self.source.mkdir()
        self.repo.mkdir()
        (self.repo / '_config.yml').write_text('url: https://example.org/logbook\n')
        self.name = '【WeKB系列】一、知识图谱 - TencentKG - KM平台.html'
        (self.source / self.name).write_text(
            '<div id="mce_view_content"><p>腾讯<span>工程效能平台部</span>：保留技术正文</p>'
            '<p>部门：不应保留的归属</p><p>微信视频号团队 IBM PayPal</p>'
            '<img src="./图_files/cos-file-url"><img src="./lost.png">'
            '<a href="https://km.woa.com/private">参考原理</a>'
            '<pre><span>Map&lt;String, T&gt; value;</span><br>google.protobuf</pre>'
            '<script>alert(1)</script></div><footer>平台页脚</footer>')
        assets = self.source / '图_files'
        assets.mkdir()
        (assets / 'cos-file-url').write_bytes(tiny_png())

    def test_content_categories_images_and_redaction(self):
        report = run(self.source, self.repo)
        text = (self.repo / report['articles'][0]['path']).read_text()
        self.assertIn('  - 推荐系统\n  - 知识图谱与图学习\n', text)
        self.assertIn('/logbook/images/recommender-system/', text)
        self.assertEqual(report['unique_images'], 1)
        self.assertEqual(report['images']['missing_images'], 1)
        for value in ('保留技术正文', '参考原理', 'Map&lt;String, T&gt;', 'google.protobuf', '[图片未保存到本地]'):
            self.assertIn(value, text)
        for value in ('腾讯', '工程效能平台部', 'TencentKG', 'KM平台', '微信视频号团队', 'IBM', 'PayPal', 'woa.com', '<script', '<span', '平台页脚', '不应保留的归属'):
            self.assertNotIn(value, text)

    def test_titles_keep_series_and_full_chain(self):
        scrub = RecommenderSystemScrubber([self.source / self.name])
        self.assertEqual(scrub.title(Path(self.name)), '【WeKB系列】一、知识图谱')
        title = '推荐全链路----精粗排一致性'
        self.assertEqual(scrub.title(Path(title + ' - KM平台.html')), title)
        self.assertEqual(scrub('google.protobuf com.ibm.client LinkedIn'), 'google.protobuf com.ibm.client ')
        self.assertEqual(scrub('Google运维解密 PayPal公司'), '运维解密 公司')
        self.assertEqual(scrub.title(Path('【数据分析】KG-BERT - 互娱增值服务部 - 技术&服务藏经阁 - KM平台.html')), '【数据分析】KG-BERT')
        self.assertEqual(scrub('实体表示学习技术及微信中的落地'), '实体表示学习技术及业务中的落地')

    def test_repeatable_and_existing_category_untouched(self):
        old = import_recommendation(self.source, self.repo)
        saved = {p: (self.repo / p).read_bytes() for p in old['files']}
        report = run(self.source, self.repo)
        before = (self.repo / MANIFEST).read_bytes()
        self.assertEqual(report, run(self.source, self.repo))
        self.assertEqual(before, (self.repo / MANIFEST).read_bytes())
        for path, data in saved.items():
            self.assertEqual(data, (self.repo / path).read_bytes())

    def test_manual_edits_protected(self):
        report = run(self.source, self.repo)
        post = self.repo / report['articles'][0]['path']
        post.write_text(post.read_text() + '\nmanual note')
        with self.assertRaisesRegex(ValueError, 'edited file'):
            run(self.source, self.repo)
        self.assertTrue(post.read_text().endswith('manual note'))

    def test_dry_run_and_preview_only(self):
        (self.source / '预览.html').write_text('<iframe src="https://example.com/preview"></iframe>')
        report = run(self.source, self.repo, True)
        self.assertEqual(report['sources'], 2)
        self.assertEqual(len(report['skipped']), 1)
        self.assertFalse((self.repo / POSTS).exists())
        self.assertFalse((self.repo / MANIFEST).exists())

    def test_root_url_and_empty_source(self):
        (self.repo / '_config.yml').write_text('root: /\n')
        report = run(self.source, self.repo)
        self.assertIn('src="/images/recommender-system/', (self.repo / report['articles'][0]['path']).read_text())
        before = (self.repo / MANIFEST).read_bytes()
        (self.source / self.name).unlink()
        with self.assertRaises(ValueError):
            run(self.source, self.repo)
        self.assertEqual(before, (self.repo / MANIFEST).read_bytes())


if __name__ == '__main__':
    unittest.main()

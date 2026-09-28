import tempfile
import unittest
from pathlib import Path

from import_algorithm_html import run as import_algorithms
from import_recommendation_html import MANIFEST, POSTS, RecommendationScrubber, run
from test_import_algorithm_html import tiny_png


class RecommendationImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'html'
        self.repo = self.root / 'repo'
        self.source.mkdir()
        self.repo.mkdir()
        (self.repo / '_config.yml').write_text('url: https://example.org/logbook\n')
        self.name = "【CIKM'20】推荐系统---跨域推荐 - 资金与数据部 - KM平台.html"
        self.source.joinpath(self.name).write_text(
            '<div id="mce_view_content"><p><span>腾讯</span>资金与数据部：模型原理</p>'
            '<img src="./图片_files/cos-file-url"><p>参考<a href="https://km.woa.com/private">技术方案</a></p>'
            '<pre>Map&lt;String, T&gt; values;</pre></div><footer>平台页脚</footer>'
        )
        assets = self.source / '图片_files'
        assets.mkdir()
        assets.joinpath('cos-file-url').write_bytes(tiny_png())

    def test_titles_keep_conferences_years_and_hyphens(self):
        scrub = RecommendationScrubber([self.source / self.name])
        self.assertEqual(scrub.title(self.source / self.name), "【CIKM'20】推荐系统---跨域推荐")
        self.assertEqual(scrub.title(Path('推荐全链路----精粗排一致性.html')), '推荐全链路----精粗排一致性')

    def test_independent_category_and_images(self):
        report = run(self.source, self.repo)
        self.assertEqual(report['sources'], 1)
        self.assertEqual(report['unique_images'], 1)
        self.assertEqual(report['images']['resolved_images'], 1)
        article = self.repo / report['articles'][0]['path']
        text = article.read_text()
        self.assertIn('  - 推荐算法\n  - 跨域推荐与冷启动\n---', text)
        self.assertIn('/logbook/images/recommendation/', text)
        self.assertIn("【CIKM'20】推荐系统---跨域推荐", text)
        self.assertIn('模型原理', text)
        self.assertIn('Map&lt;String, T&gt;', text)
        for identifier in ('腾讯', '资金与数据部', 'woa.com', '平台页脚'):
            self.assertNotIn(identifier, text)

    def test_other_categories_and_reimports_unchanged(self):
        algorithms = import_algorithms(self.source, self.repo)
        other = {p: (self.repo / p).read_bytes() for p in algorithms['files']}
        algorithm_manifest = (self.repo / 'tools/algorithm-import-manifest.json').read_bytes()
        run(self.source, self.repo)
        before = (self.repo / MANIFEST).read_bytes()
        run(self.source, self.repo)
        self.assertEqual(before, (self.repo / MANIFEST).read_bytes())
        self.assertEqual(algorithm_manifest, (self.repo / 'tools/algorithm-import-manifest.json').read_bytes())
        for name, expected in other.items():
            self.assertEqual(expected, (self.repo / name).read_bytes())

    def test_manual_changes_are_not_overwritten(self):
        report = run(self.source, self.repo)
        post = self.repo / report['articles'][0]['path']
        post.write_text(post.read_text() + '\nmanual note')
        with self.assertRaisesRegex(ValueError, 'edited file'):
            run(self.source, self.repo)
        self.assertTrue(post.read_text().endswith('manual note'))

    def test_dry_run_and_preview_only_exports(self):
        self.source.joinpath('产品白皮书.html').write_text('<html><body>PDF预览</body></html>')
        report = run(self.source, self.repo, dry_run=True)
        self.assertEqual(len(report['articles']), 1)
        self.assertEqual(len(report['skipped']), 1)
        self.assertFalse((self.repo / MANIFEST).exists())
        self.assertFalse((self.repo / POSTS).exists())

    def test_nested_article_but_not_asset_html(self):
        chapter = self.source / '图学习'
        chapter.mkdir()
        chapter.joinpath('GNN.html').write_text('<div id="article_content">算法正文</div>')
        self.source.joinpath('图片_files/nested.html').write_text('<div id="article_content">非文章</div>')
        report = run(self.source, self.repo)
        self.assertEqual(report['sources'], 2)
        self.assertEqual(len(report['articles']), 2)


if __name__ == '__main__':
    unittest.main()


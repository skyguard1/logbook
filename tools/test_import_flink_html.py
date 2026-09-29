import tempfile
import unittest
from pathlib import Path

from import_flink_html import FlinkScrubber, MANIFEST, POSTS, classify, run
from test_import_algorithm_html import tiny_png


class FlinkTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source, self.repo = self.root / 'html', self.root / 'repo'
        self.source.mkdir()
        self.repo.mkdir()
        (self.repo / '_config.yml').write_text('url: https://example.org/logbook\n')
        self.name = '【DataMore】Flink监控 - Promethus+Grafana - 互娱增值服务部 - 技术&服务藏经阁 - KM平台.html'
        (self.source / self.name).write_text(
            '<div id="mce_view_content"><p>腾讯云大数据及人工智能 技术正文</p>'
            '<p>部门：智慧零售研发K吧</p><p>IEG增长中台体系</p>'
            '<img src="./a_files/cos-file-url"><img src="missing.png">'
            '<pre><span>Map&lt;String, T&gt;</span><br>google.protobuf</pre>'
            '<a href="https://km.woa.com/private">参考资料</a></div>')
        assets = self.source / 'a_files'
        assets.mkdir()
        (assets / 'cos-file-url').write_bytes(tiny_png())

    def test_titles_and_topics(self):
        scrub = FlinkScrubber([self.source / self.name])
        self.assertEqual(scrub.title(Path(self.name)), 'Flink监控 - Promethus+Grafana')
        self.assertEqual(scrub('Promethus+Grafana'), 'Promethus+Grafana')
        for title, topic in [('Flink监控', '监控与故障排查'), ('ClickHouse SQL优化', 'SQL与查询优化'),
                             ('Flink实时数仓', '实时数仓与工程实践'), ('学习Flink', '基础原理与入门')]:
            self.assertEqual(classify(title), topic)

    def test_content_redaction_and_images(self):
        report = run(self.source, self.repo)
        text = (self.repo / report['articles'][0]['path']).read_text()
        for value in ('  - flink\n', '/logbook/images/flink/', 'Map&lt;String, T&gt;', 'google.protobuf', '参考资料', '技术正文'):
            self.assertIn(value, text)
        for value in ('腾讯', 'IEG', '增长中台体系', '智慧零售', 'DataMore', 'woa.com', '<span'):
            self.assertNotIn(value, text)
        self.assertEqual(report['unique_images'], 1)
        self.assertEqual(report['images']['missing_images'], 1)

    def test_dry_run_repeat_and_other_category(self):
        other = self.repo / 'source/_posts/linux/note.md'
        other.parent.mkdir(parents=True)
        other.write_text('manual note')
        run(self.source, self.repo, True)
        self.assertFalse((self.repo / POSTS).exists())
        report = run(self.source, self.repo)
        manifest = (self.repo / MANIFEST).read_bytes()
        self.assertEqual(run(self.source, self.repo), report)
        self.assertEqual((self.repo / MANIFEST).read_bytes(), manifest)
        self.assertEqual(other.read_text(), 'manual note')

    def test_manual_changes_and_empty_source_protected(self):
        report = run(self.source, self.repo)
        post = self.repo / report['articles'][0]['path']
        post.write_text(post.read_text() + '\nmanual edit')
        with self.assertRaisesRegex(ValueError, 'edited file'):
            run(self.source, self.repo)
        (self.source / self.name).unlink()
        with self.assertRaises(ValueError):
            run(self.source, self.repo)
        self.assertTrue(post.read_text().endswith('manual edit'))

    def test_root_deployment_skipped_pages_and_local_only(self):
        (self.repo / '_config.yml').write_text('root: /\n')
        (self.source / '预览.html').write_text('<iframe src="https://example.org/private"></iframe>')
        (self.source / '安全.html').write_text('<div id="article_content"><img src="../outside.png"></div>')
        (self.root / 'outside.png').write_bytes(tiny_png())
        report = run(self.source, self.repo)
        self.assertEqual(len(report['skipped']), 1)
        self.assertEqual(report['images']['missing_images'], 2)
        text = (self.repo / report['articles'][0]['path']).read_text()
        self.assertIn('src="/images/flink/', text)


if __name__ == '__main__':
    unittest.main()

import json
import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from repair_deep_learning_images import MANIFEST, POSTS, run
from test_import_algorithm_html import tiny_png


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source, self.repo = root / 'html', root / 'repo'
        self.source.mkdir()
        self.repo.mkdir()
        (self.repo / '_config.yml').write_text('url: https://example.org/logbook\n')
        assets = self.source / '腾讯文章_files'
        assets.mkdir()
        (assets / 'cos-file-url').write_bytes(tiny_png())
        self.source.joinpath('腾讯文章 - KM平台.html').write_text(
            '<div id="mce_view_content"><p>模型原理</p><img src="./腾讯文章_files/cos-file-url"><p>后文</p></div>'
        )
        self.post = self.repo / POSTS / '文章.md'
        self.post.parent.mkdir(parents=True)
        self.front = '---\ntitle: "文章"\ndate: 2022-01-01 12:00:00\ncategories:\n  - deep-learning\n---'
        self.post.write_text(self.front + '\n\n<p>旧正文</p>')
        self.git('init', '-q')
        self.git('config', 'user.name', 'test')
        self.git('config', 'user.email', 'test@example.org')
        self.git('add', '.')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)

    def test_repair_preserves_path_frontmatter_and_resolves_original_image_path(self):
        result = run(self.source, self.repo, adopt=True)
        self.assertEqual(result['unique_images'], 1)
        text = self.post.read_text()
        self.assertTrue(text.startswith(self.front))
        self.assertIn('/logbook/images/deep-learning/', text)
        self.assertIn('模型原理', text)
        self.assertIn('后文', text)
        self.assertNotIn('腾讯', text)
        self.assertEqual(len(list((self.repo / '.git/import-backups').glob('*.zip'))), 1)
        before = (self.repo / MANIFEST).read_bytes()
        run(self.source, self.repo)
        self.assertEqual(before, (self.repo / MANIFEST).read_bytes())

    def test_legacy_adoption_requires_clean_files_and_opt_in(self):
        with self.assertRaisesRegex(ValueError, '--adopt-legacy'):
            run(self.source, self.repo)
        self.post.write_text(self.post.read_text() + '\nmanual change')
        with self.assertRaisesRegex(ValueError, 'modified legacy'):
            run(self.source, self.repo, adopt=True)
        self.assertIn('manual change', self.post.read_text())
        self.assertFalse((self.repo / MANIFEST).exists())

    def test_subsequent_manual_edits_protected(self):
        run(self.source, self.repo, adopt=True)
        self.post.write_text(self.post.read_text() + '\nmanual change')
        with self.assertRaisesRegex(ValueError, 'edited generated'):
            run(self.source, self.repo)
        self.assertIn('manual change', self.post.read_text())

    def test_dry_run_does_not_write_or_backup(self):
        old = self.post.read_bytes()
        result = run(self.source, self.repo, adopt=True, dry_run=True)
        self.assertEqual(result['unique_images'], 1)
        self.assertEqual(old, self.post.read_bytes())
        self.assertFalse((self.repo / MANIFEST).exists())
        self.assertFalse((self.repo / '.git/import-backups').exists())

    def test_legacy_importer_refuses_to_replace_repaired_category(self):
        import import_km_html as legacy
        run(self.source, self.repo, adopt=True)
        before = self.post.read_bytes()
        args = Namespace(deep_learning_dir=str(self.source), kubernetes_dir='', linux_dir='',
                         es_dir='', only=['deep-learning'], replace_category=True)
        with patch.object(legacy, 'REPO_ROOT', self.repo), patch.object(legacy, 'parse_args', return_value=args):
            with self.assertRaisesRegex(SystemExit, 'image-preserving importer'):
                legacy.main()
        self.assertEqual(before, self.post.read_bytes())


if __name__ == '__main__':
    unittest.main()


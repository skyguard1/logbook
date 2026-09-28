#!/usr/bin/env python3
"""Restore existing Deep Learning posts from offline HTML, preserving their URLs."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

# The legacy helper has a tracked bytecode cache: never modify it on import.
sys.dont_write_bytecode = True
from import_km_html import clean_title, safe_filename
from import_algorithm_html import (
    REPO, DROP, Scrubber, clean_dom, copy_images, digest, extract,
    publish_stage, site_root, source_files,
)

POSTS = Path('source/_posts/deep-learning')
IMAGES = Path('source/images/deep-learning')
MANIFEST = Path('tools/deep-learning-import-manifest.json')


def legacy_baseline(repo: Path, adopt: bool) -> dict:
    if (repo / MANIFEST).exists():
        return {}
    if not adopt:
        raise ValueError('First repair requires --adopt-legacy (backs up clean, tracked posts)')
    files = sorted((repo / POSTS).rglob('*.md'))
    if not files:
        raise ValueError('No existing Deep Learning posts to repair')
    baseline = {}
    for path in files:
        name = path.relative_to(repo).as_posix()
        tracked = subprocess.run(['git', '-C', str(repo), 'show', 'HEAD:' + name], capture_output=True, check=False)
        if path.is_symlink() or tracked.returncode or tracked.stdout != path.read_bytes():
            raise ValueError(f'Refusing to replace an untracked or modified legacy post: {name}')
        baseline[name] = digest(tracked.stdout)
    return baseline


def backup_posts(repo: Path, baseline: dict):
    git_dir = Path(subprocess.check_output(['git', '-C', str(repo), 'rev-parse', '--absolute-git-dir'], text=True).strip())
    backup = git_dir / 'import-backups' / ('deep-learning-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.zip')
    backup.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(backup, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in baseline:
            archive.write(repo / name, name)
    print('Legacy post backup:', backup)


def run(source: Path, repo: Path, adopt: bool = False, dry_run: bool = False):
    source, repo = source.expanduser().resolve(), repo.resolve()
    files = source_files(source)
    baseline = legacy_baseline(repo, adopt)
    scrub = Scrubber(files)
    existing = sorted((repo / POSTS).rglob('*.md'))
    if (repo / MANIFEST).exists():
        previous = json.loads((repo / MANIFEST).read_text())['files']
        for name, expected in previous.items():
            target = repo / name
            if target.exists() and digest(target.read_bytes()) != expected:
                raise ValueError(f'Refusing to replace an edited generated file: {name}')
    report = {'sources': len(files), 'articles': [], 'skipped': [], 'images': {}, 'files': {}}
    stats = Counter()
    seen, matched = set(), set()
    with tempfile.TemporaryDirectory(prefix='logbook-deep-repair-') as temp:
        stage = Path(temp)
        for path in files:
            # Reproduce the legacy naming only, not its lossy HTML cleanup.
            title = clean_title(path.name)
            slug = safe_filename(title)
            if slug in seen:
                slug += ' (' + hashlib.sha1(path.name.encode()).hexdigest()[:8] + ')'
            seen.add(slug)
            rel = POSTS / (slug + '.md')
            target = repo / rel
            if not target.exists():
                continue  # Do not add unrelated, previously skipped articles.
            matched.add(rel.as_posix())
            current = target.read_text(encoding='utf-8')
            parts = current.split('---', 2)
            if len(parts) != 3 or parts[0].strip():
                raise ValueError(f'Invalid front matter: {rel}')
            result = extract(path, source)
            if not result:
                report['skipped'].append({'title': title, 'path': rel.as_posix(), 'reason': '源文件只有文档预览；保留现有说明，无法从中恢复图片'})
                output = stage / rel
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(current, encoding='utf-8')
                continue
            body, origin = result
            for tag in list(body.select(DROP)):
                if tag.parent:
                    tag.decompose()
            chars_before = len(body.get_text(strip=True))
            images = copy_images(body, origin, source, stage, site_root(repo), scrub, IMAGES)
            stats.update(images)
            clean_dom(body, scrub)
            text = body.decode_contents().replace('{%', '&#123;%').replace('{{', '&#123;{')
            output = stage / rel
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text('---' + parts[1] + '---\n\n{% raw %}\n' + text + '\n{% endraw %}\n', encoding='utf-8')
            report['articles'].append({'title': title, 'path': rel.as_posix(), 'source_chars': chars_before,
                                       'output_chars': len(body.get_text(strip=True)), 'images': dict(images)})
        if matched != {p.relative_to(repo).as_posix() for p in existing}:
            raise ValueError('Some existing posts could not be matched to source HTML; no outputs changed')
        if not report['articles']:
            raise ValueError('No recoverable article bodies')
        report['images'] = dict(stats)
        report['files'] = {p.relative_to(stage).as_posix(): digest(p.read_bytes()) for p in sorted(stage.rglob('*')) if p.is_file()}
        report['unique_images'] = sum(name.startswith(str(IMAGES) + '/') for name in report['files'])
        report['review_required'] = '自动文本清理不等于图片内容脱敏；公开发布前需人工审核截图和资料权限。'
        if not dry_run:
            if baseline:
                backup_posts(repo, baseline)
            publish_stage(stage, repo, report, MANIFEST, POSTS, IMAGES, baseline)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home() / 'Documents/深度学习')
    parser.add_argument('--repo', type=Path, default=REPO)
    parser.add_argument('--adopt-legacy', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        report = run(args.source, args.repo, args.adopt_legacy, args.dry_run)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'Repair failed: {exc}\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'files', 'articles'}}, ensure_ascii=False, indent=2))
    print('Repaired articles:', len(report['articles']))


if __name__ == '__main__':
    main()


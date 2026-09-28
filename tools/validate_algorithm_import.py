#!/usr/bin/env python3
"""Validate managed articles/assets and their rendered Hexo output (after build)."""
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from import_algorithm_html import REPO, MANIFEST, POSTS, IMAGES, Scrubber, digest, site_root


def main():
    report = json.loads((REPO / MANIFEST).read_text(encoding='utf-8'))
    root = site_root(REPO)
    failures = []
    for name, expected in report['files'].items():
        file = REPO / name
        if not file.is_file() or digest(file.read_bytes()) != expected:
            failures.append(f'Changed/missing output: {name}')
    actual_posts = set(p.relative_to(REPO).as_posix() for p in (REPO / POSTS).rglob('*.md'))
    expected_posts = {a['path'] for a in report['articles']}
    if actual_posts != expected_posts:
        failures.append('Article inventory does not match the import manifest')
    rendered = [p for p in (REPO / 'public').rglob('*.html') if 'algorithm' in p.relative_to(REPO / 'public').parts and 'categories' not in p.parts]
    if len(rendered) != len(expected_posts):
        failures.append(f'Expected {len(expected_posts)} rendered articles, found {len(rendered)}')
    scrub = Scrubber([])
    image_refs = 0
    for page in rendered:
        soup = BeautifulSoup(page.read_bytes(), 'html.parser')
        article = soup.select_one('.article-entry')
        if article is None:
            failures.append(f'Missing article body: {page}')
            continue
        plain = article.get_text()
        if scrub(plain) != plain:
            failures.append(f'Unredacted organisation text: {page}')
        if '{% raw %}' in plain or '{% endraw %}' in plain:
            failures.append(f'Unprocessed template wrapper: {page}')
        if article.select('script, iframe, style'):
            failures.append(f'Active imported content: {page}')
        for pre in article.find_all('pre'):
            if '<span style=' in pre.get_text():
                failures.append(f'Literal highlighting markup in code: {page}')
        for img in article.find_all('img'):
            src = img.get('src', '')
            if not src.startswith(root + 'images/algorithm/'):
                failures.append(f'Unexpected article image source: {page}')
                continue
            rel = unquote(urlsplit(src).path.removeprefix(root))
            if not (REPO / 'public' / rel).is_file():
                failures.append(f'Missing rendered image: {page}')
            image_refs += 1
    for topic in report['topics']:
        # Hexo's default category generator uses the category names directly.
        if not (REPO / 'public/categories/算法' / topic / 'index.html').is_file():
            failures.append(f'Missing hierarchical category page: {topic}')
    for image in (REPO / IMAGES).glob('*'):
        public = REPO / 'public/images/algorithm' / image.name
        if not public.is_file() or digest(public.read_bytes()) != digest(image.read_bytes()):
            failures.append(f'Generated image differs: {image.name}')
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f'PASS: {len(rendered)} articles, {len(report["topics"])} topics, {image_refs} rendered image references, {report["unique_images"]} unique assets')
    print(f'Known source limitations: {len(report["skipped"])} skipped exports; {report["images"].get("missing_images", 0)} missing source image references')


if __name__ == '__main__':
    main()


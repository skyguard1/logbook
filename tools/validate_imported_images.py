#!/usr/bin/env python3
"""Validate both imported categories after Hexo build; optionally check HTTP images."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from import_algorithm_html import REPO, digest, site_root


def validate(base_url=None):
    root = site_root(REPO)
    failures, urls, summaries = [], set(), {}
    for category in ('algorithm', 'deep-learning'):
        manifest = json.loads((REPO / f'tools/{category}-import-manifest.json').read_text())
        for rel, expected in manifest['files'].items():
            path = REPO / rel
            if not path.is_file() or digest(path.read_bytes()) != expected:
                failures.append(f'Missing/edited managed file: {rel}')
        pages = [p for p in (REPO / 'public').rglob('*.html')
                 if category in p.relative_to(REPO / 'public').parts and 'categories' not in p.relative_to(REPO / 'public').parts]
        expected_pages = sum(p.startswith(f'source/_posts/{category}/') for p in manifest['files'])
        if len(pages) != expected_pages:
            failures.append(f'{category}: expected {expected_pages} pages, got {len(pages)}')
        refs = 0
        for page in pages:
            body = BeautifulSoup(page.read_bytes(), 'html.parser').select_one('.article-entry')
            if body is None:
                failures.append(f'Missing rendered article: {page}')
                continue
            for img in body.find_all('img'):
                src = img.get('src', '')
                if not src.startswith(root + f'images/{category}/'):
                    failures.append(f'Unexpected image URL: {page}')
                    continue
                public = REPO / 'public' / unquote(urlsplit(src).path.removeprefix(root))
                if not public.is_file():
                    failures.append(f'Missing image asset: {public}')
                elif public.suffix == '.svg':
                    try:
                        ET.parse(public)
                    except ET.ParseError:
                        failures.append(f'Invalid SVG XML: {public}')
                urls.add(src)
                refs += 1
        if manifest['images'].get('resolved_images') != refs:
            failures.append(f'{category}: image references lost during rendering ({refs})')
        summaries[category] = {'pages': len(pages), 'image_references': refs, 'unique_images': manifest['unique_images'],
                               'missing_in_source': manifest['images'].get('missing_images', 0)}
    if base_url:
        def check(src):
            try:
                with urlopen(Request(base_url.rstrip('/') + src, method='HEAD'), timeout=20) as response:
                    if response.status != 200 or not response.headers.get('Content-Type', '').startswith('image/'):
                        return f'Unexpected HTTP image response: {src}'
            except Exception as exc:
                return f'Image request failed: {src}: {exc}'
        with ThreadPoolExecutor(max_workers=8) as pool:
            failures.extend(result for result in pool.map(check, sorted(urls)) if result)
    if failures:
        raise SystemExit('\n'.join(failures))
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    print(f'PASS: {len(urls)} unique referenced image URLs' + (' returned HTTP 200 image/*' if base_url else ' exist in generated output'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', help='Server origin, for example http://127.0.0.1:4000 (no /logbook suffix)')
    args = parser.parse_args()
    validate(args.base_url)


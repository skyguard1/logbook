#!/usr/bin/env python3
"""Validate recommendation metadata, rendered pages/assets, and optional browser layout."""
import argparse
import json
import re
from urllib.parse import quote, unquote
from pathlib import Path

from bs4 import BeautifulSoup
from import_algorithm_html import REPO, digest, site_root, source_files
from import_recommendation_html import MANIFEST, POSTS, IMAGES, RecommendationScrubber


def validate(origin=None):
    report = json.loads((REPO / MANIFEST).read_text())
    root = site_root(REPO)
    source = Path.home() / 'Documents/推荐算法'
    scrub = RecommendationScrubber(source_files(source)) if source.is_dir() else RecommendationScrubber([])
    pages, urls = [], set()
    for rel, expected in report['files'].items():
        path = REPO / rel
        assert path.is_file() and digest(path.read_bytes()) == expected, f'Changed managed file: {rel}'
        if rel.startswith(str(IMAGES) + '/'):
            public = REPO / 'public' / path.relative_to(REPO / 'source')
            assert public.is_file() and public.read_bytes() == path.read_bytes(), f'Missing/changed generated image: {rel}'
    refs = 0
    for row in report['articles']:
        text = (REPO / row['path']).read_text()
        front = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
        assert front, f'Invalid front matter: {row["title"]}'
        title = json.loads(re.search(r'^title: (.+)$', front[1], re.M)[1])
        assert title == row['title'] and scrub(title) == title
        date = re.search(r'^date: (\d{4})-(\d{2})-(\d{2})', front[1], re.M)
        slug = Path(row['path']).relative_to('source/_posts').with_suffix('').as_posix()
        rel = '/'.join(date.groups()) + '/' + slug + '/index.html'
        page = REPO / 'public' / rel
        soup = BeautifulSoup(page.read_bytes(), 'html.parser')
        header = soup.select_one('.article-header .article-title')
        body = soup.select_one('.e-content.article-entry')
        assert header and header.get_text(strip=True) == title, f'Truncated title: {rel}'
        assert body and scrub(body.get_text()) == body.get_text(), f'Residual org text: {rel}'
        assert not body.select('script, iframe, style'), f'Executable imported content: {rel}'
        for img in body.find_all('img'):
            url = img.get('src', '')
            assert url.startswith(root + 'images/recommendation/'), f'Unexpected image URL: {rel}'
            assert (REPO / 'public' / unquote(url.removeprefix(root))).is_file()
            urls.add(url)
            refs += 1
        pages.append((root + quote(rel), title))
    assert refs == report['images'].get('resolved_images', 0), 'Lost image references during rendering'
    for topic in report['topics']:
        assert (REPO / 'public/categories/推荐算法' / topic / 'index.html').is_file(), topic
    print(f'PASS: {len(pages)} complete titles, {len(report["topics"])} categories, {refs} image references, {len(urls)} unique assets')
    if origin:
        from playwright.sync_api import sync_playwright
        chrome = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**({'executable_path': str(chrome)} if chrome.exists() else {}))
            page = browser.new_page()
            page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin + '/') else route.abort())
            for width in (1440, 800, 390):
                page.set_viewport_size({'width': width, 'height': 1000})
                for url, title in pages:
                    page.goto(origin + url, wait_until='load')
                    assert page.locator('.article-header .article-title').inner_text().strip() == title
                    errors = page.evaluate('''async () => {
                        const errors=[];
                        const h=document.querySelector('.article-header .article-title');
                        if(h.scrollWidth>h.clientWidth+2) errors.push('title clipped');
                        const main=document.querySelector('#main'), side=document.querySelector('#sidebar'), outer=document.querySelector('.main-outer');
                        if(main.parentElement!==outer || side.parentElement!==outer) errors.push('sidebar escaped');
                        const m=main.getBoundingClientRect(),s=side.getBoundingClientRect();
                        if(innerWidth>=800 && (s.x<m.right-1 || Math.abs(s.y-m.y)>2)) errors.push('sidebar not right-aligned');
                        if(document.documentElement.scrollWidth>innerWidth+2) errors.push('horizontal page overflow');
                        const imgs=[...document.querySelectorAll('.article-entry img')];
                        await Promise.all(imgs.map(async img=>{img.loading='eager'; try {await img.decode();}catch {errors.push('image decode failed');}}));
                        if(imgs.some(img=>!img.naturalWidth))errors.push('empty image');
                        return errors;
                    }''')
                    assert not errors, (width, title, errors)
                print(f'Chrome: {len(pages)} pages at {width}px PASS', flush=True)
            browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', help='Optional browser test origin, e.g. http://127.0.0.1:4000')
    args = parser.parse_args()
    validate(args.origin)


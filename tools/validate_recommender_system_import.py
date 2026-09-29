#!/usr/bin/env python3
"""Validate imported files, built pages and optional desktop/mobile layout."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup
from import_algorithm_html import REPO, digest, site_root, source_files
from import_recommender_system_html import MANIFEST, IMAGES, RecommenderSystemScrubber


def validate(origin=None, *, manifest=MANIFEST, images=IMAGES, category='推荐系统',
             scrubber_class=RecommenderSystemScrubber, source=None):
    report = json.loads((REPO / manifest).read_text())
    root = site_root(REPO)
    source = source or Path.home() / 'Documents' / category
    scrub = scrubber_class(source_files(source) if source.is_dir() else [])
    for rel, expected in report['files'].items():
        path = REPO / rel
        assert path.is_file() and digest(path.read_bytes()) == expected, rel
        if rel.startswith(str(images) + '/'):
            generated = REPO / 'public' / path.relative_to(REPO / 'source')
            assert generated.is_file() and generated.read_bytes() == path.read_bytes(), rel
    pages, refs = [], 0
    for row in report['articles']:
        text = (REPO / row['path']).read_text()
        front = re.match(r'\A---\n(.*?)\n---\n', text, re.S)[1]
        title = json.loads(re.search(r'^title: (.+)$', front, re.M)[1])
        assert title == row['title'] and scrub(title) == title
        assert f'\ncategories:\n  - {category}\n' in '\n' + front
        date = re.search(r'^date: (\d{4})-(\d{2})-(\d{2})', front, re.M)
        slug = Path(row['path']).relative_to('source/_posts').with_suffix('').as_posix()
        rel = '/'.join(date.groups()) + '/' + slug + '/index.html'
        soup = BeautifulSoup((REPO / 'public' / rel).read_bytes(), 'html.parser')
        header = soup.select_one('.article-header .article-title')
        body = soup.select_one('.e-content.article-entry')
        assert header and header.get_text(strip=True) == title, rel
        assert body and scrub(body.get_text()) == body.get_text(), rel
        assert not body.select('script, iframe, style'), rel
        main, side = soup.select_one('#main'), soup.select_one('#sidebar')
        assert main.parent is side.parent and 'main-outer' in main.parent.get('class', []), rel
        for img in body.find_all('img'):
            url = img.get('src', '')
            assert url.startswith(root + images.relative_to('source').as_posix() + '/'), (rel, url)
            assert (REPO / 'public' / unquote(url.removeprefix(root))).is_file(), url
            refs += 1
        pages.append((root + quote(rel), title))
    assert refs == report['images'].get('resolved_images', 0), 'Lost image references'
    for topic in report['topics']:
        assert (REPO / 'public/categories' / category / topic / 'index.html').is_file(), topic
    print(f'PASS: {len(pages)} titles and pages; {refs} image references; {len(report["topics"])} topics')
    if origin:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
            page = browser.new_page()
            page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin + '/') else route.abort())
            for width in (1440, 800, 390):
                page.set_viewport_size({'width': width, 'height': 1000})
                for url, title in pages:
                    page.goto(origin + url, wait_until='load')
                    assert page.locator('.article-header .article-title').inner_text().strip() == title
                    errors = page.evaluate('''async () => {
                        const errors = [], main = document.querySelector('#main').getBoundingClientRect(), side = document.querySelector('#sidebar').getBoundingClientRect();
                        if (innerWidth >= 800 && (side.x < main.right - 1 || Math.abs(side.y - main.y) > 2)) errors.push('sidebar not right-aligned');
                        if (document.documentElement.scrollWidth > innerWidth + 2) errors.push('page overflow');
                        const title = document.querySelector('.article-title');
                        if (title.scrollWidth > title.clientWidth + 2) errors.push('title clipped');
                        await Promise.all([...document.querySelectorAll('.article-entry img')].map(async img => {
                            img.loading = 'eager'; try { await img.decode(); } catch { errors.push('image decode failed'); }
                        }));
                        return errors;
                    }''')
                    assert not errors, (width, title, errors)
                print(f'PASS: Chrome {len(pages)} pages at {width}px', flush=True)
            browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', help='Optional local Hexo origin, e.g. http://127.0.0.1:4000')
    validate(parser.parse_args().origin)

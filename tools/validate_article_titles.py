#!/usr/bin/env python3
"""Verify imported title metadata, all rendered titles, and responsive list/detail styles.

Run a clean Hexo build and local server first. Optional dependencies: BeautifulSoup
and Playwright (uses installed Chrome on macOS, otherwise Playwright Chromium).
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
HEADER = re.compile(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', re.S)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', default='http://127.0.0.1:4000')
    args = parser.parse_args()
    public = REPO / 'public'
    expected = {}
    for category in ('algorithm', 'deep-learning'):
        for path in (REPO / 'source/_posts' / category).rglob('*.md'):
            match = HEADER.match(path.read_text())
            assert match, f'Broken front matter: {path}'
            title_match = re.search(r'^title:\s*(.+)$', match[1], re.M)
            assert title_match, f'Missing title: {path}'
            title = json.loads(title_match[1])
            date = re.search(r'^date:\s*(\d{4})-(\d{2})-(\d{2})', match[1], re.M)
            assert date, f'Missing date: {path}'
            slug = path.relative_to(REPO / 'source/_posts').with_suffix('').as_posix()
            relative = '/'.join(date.groups()) + '/' + slug + '/index.html'
            expected[relative] = title
            html = BeautifulSoup((public / relative).read_bytes(), 'html.parser')
            heading = html.select_one('.article-detail > .article-inner > .article-header .article-title')
            assert heading and heading.get_text(strip=True) == title, (relative, title)
            assert not html.select('.article-detail.article-list-item')
    index_pages = [public / 'index.html'] + sorted((public / 'page').glob('*/index.html'))
    list_pages = []
    for path in index_pages:
        html = BeautifulSoup(path.read_bytes(), 'html.parser')
        cards = html.select('#main > article')
        assert cards, f'No article cards: {path}'
        for card in cards:
            assert 'article-list-item' in card.get('class', [])
            heading = card.select_one('.article-header .article-title')
            assert heading and heading.get_text(strip=True), f'Missing list title: {path}'
            excerpt = card.select_one('.article-excerpt')
            assert not excerpt or not excerpt.get_text(strip=True).startswith('title:'), f'Leaked metadata: {path}'
        list_pages.append(path)
    print(f'Full titles/metadata verified: {len(expected)} imported articles; {len(index_pages)} index pages', flush=True)
    # Every recommendation-pipeline article plus pages containing their list cards.
    selected = [public / rel for rel in expected if '推荐全链路' in rel]
    lists = [p for p in list_pages if p == public / 'index.html' or '推荐全链路' in p.read_text()]
    chrome = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**({'executable_path': str(chrome)} if chrome.exists() else {}))
        page = browser.new_page()
        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(args.origin + '/') else route.abort())
        for width in (1440, 800, 390):
            page.set_viewport_size({'width': width, 'height': 1000})
            for path in lists + selected:
                page.goto(args.origin + '/logbook/' + quote(path.relative_to(public).as_posix()), wait_until='load')
                page.mouse.move(0, 0)
                errors = page.evaluate('''() => {
                    const failures=[];
                    for (const article of document.querySelectorAll('#main > article')) {
                        const h=article.querySelector('.article-header .article-title');
                        if (!h) {failures.push('missing title');continue;}
                        const style=getComputedStyle(h), rect=h.getBoundingClientRect(), range=document.createRange();
                        range.selectNodeContents(h);
                        const box=range.getBoundingClientRect();
                        if (h.scrollWidth>h.clientWidth+2 || box.right>rect.right+2 || box.bottom>rect.bottom+2) failures.push('clipped title');
                        if (style.whiteSpace==='nowrap' || style.textOverflow==='ellipsis') failures.push('truncated title rule');
                        const size=parseFloat(style.fontSize), card=article.classList.contains('article-list-item');
                        if (card && size>=24) failures.push('detail font leaked into card');
                        if (!card && size<(innerWidth<480?22:28)-0.1) failures.push('card font leaked into detail');
                        if (!card && getComputedStyle(article.querySelector('.article-inner')).transform!=='none') failures.push('card animation on detail');
                    }
                    if (document.documentElement.scrollWidth>innerWidth+2) failures.push('horizontal page overflow');
                    const main=document.querySelector('#main'),sidebar=document.querySelector('#sidebar'),outer=document.querySelector('.main-outer');
                    if (main.parentElement!==outer || sidebar.parentElement!==outer) failures.push('sidebar escaped container');
                    return failures;
                }''')
                assert not errors, (width, path, errors)
            print(f'Title wrapping, list/detail separation and page width: {width}px PASS', flush=True)
        page.goto(args.origin + '/logbook/', wait_until='load')
        page.locator('.nav-search-btn').click()
        page.locator('.search-form-input').wait_for(state='visible')
        page.locator('.search-form-input').fill('推荐全链路')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'), 'Search creates overflow'
        browser.close()
    print('PASS: full titles on home lists and article pages, search remains usable')


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""Browser regression: main/sidebar remain siblings for legacy article pages.

Optional tooling: pip install playwright; use installed Google Chrome on macOS,
otherwise run playwright install chromium. Run Hexo build and server first.
"""
import argparse
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]


def main():
    args_parser = argparse.ArgumentParser(description=__doc__)
    args_parser.add_argument('--origin', default='http://127.0.0.1:4000')
    args = args_parser.parse_args()
    public = REPO / 'public'
    paths = [public / 'index.html'] + sorted(
        p for p in public.rglob('index.html')
        if p.relative_to(public).parts[0].isdigit()
        and any(c in p.relative_to(public).parts for c in ('es', 'linux', 'kubernetes'))
    )
    assert len(paths) > 1, 'Run Hexo build first'
    chrome = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    failures = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**({'executable_path': str(chrome)} if chrome.exists() else {}))
        page = browser.new_page()
        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(args.origin + '/') else route.abort())
        for width in (1440, 800, 390):
            page.set_viewport_size({'width': width, 'height': 1000})
            for path in paths:
                relative = path.relative_to(public).as_posix()
                page.goto(args.origin + '/logbook/' + quote(relative), wait_until='load')
                result = page.evaluate('''() => {
                    const outer = document.querySelector('.main-outer');
                    const main = document.querySelector('#main');
                    const side = document.querySelector('#sidebar');
                    if (!outer || !main || !side) return {missing: true};
                    const m = main.getBoundingClientRect(), s = side.getBoundingClientRect();
                    return {siblings: main.parentElement === outer && side.parentElement === outer,
                        sideX:s.x, mainRight:m.right, sideY:s.y, mainY:m.y, mainBottom:m.bottom,
                        display:getComputedStyle(side).display};
                }''')
                ok = result.get('siblings', False)
                if width >= 800:
                    ok = ok and result['sideX'] >= result['mainRight'] - 1 and abs(result['sideY'] - result['mainY']) < 2
                else:
                    ok = ok and (result['display'] == 'none' or result['sideY'] >= result['mainBottom'] - 2)
                if not ok:
                    failures.append((width, relative, result))
            print(f'Checked {len(paths)} pages at {width}px', flush=True)
        browser.close()
    assert not failures, failures
    print('PASS: desktop sidebar stays right; narrow screens retain responsive layout')


if __name__ == '__main__':
    main()


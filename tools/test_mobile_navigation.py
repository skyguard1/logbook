#!/usr/bin/env python3
"""With Hexo serving, run: python tools/test_mobile_navigation.py --origin http://127.0.0.1:4017

Requires Playwright and local Google Chrome. No external requests are made.
"""
import argparse
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, expect
from import_algorithm_html import REPO, site_root


def validate(origin):
    home = origin + site_root(REPO)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
        page = browser.new_page(has_touch=True)
        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin + '/') else route.abort())
        page.goto(home, wait_until='load')
        article = page.locator('a.article-title-link').first.get_attribute('href')
        assert article, 'Homepage must contain an article link'
        for url in (home, urljoin(home, article)):
            for width in (320, 390, 479, 480, 800, 1440):
                page.set_viewport_size({'width': width, 'height': 900})
                page.goto(url, wait_until='load')
                toggle = page.locator('#main-nav-toggle')
                nav = page.locator('#mobile-nav')
                expect(nav).to_be_hidden()
                expect(toggle).to_have_attribute('aria-expanded', 'false')
                if width >= 480:
                    expect(toggle).to_be_hidden()
                    expect(page.locator('#main-nav .main-nav-link', has_text='Home')).to_be_visible()
                    expect(page.locator('#main-nav .main-nav-link', has_text='Archives')).to_be_visible()
                else:
                    expect(toggle).to_be_visible()
                    assert toggle.bounding_box()['height'] >= 44
                    expect(page.locator('#main-nav .main-nav-link').first).to_be_hidden()
                    toggle.tap()
                    expect(toggle).to_have_attribute('aria-expanded', 'true')
                    expect(nav.get_by_role('link', name='Home', exact=True)).to_be_visible()
                    expect(nav.get_by_role('link', name='Archives', exact=True)).to_be_visible()
                    page.wait_for_timeout(250)
                    assert nav.bounding_box()['x'] == 0
                    assert page.locator('#wrap').bounding_box()['x'] > 0
                    toggle.click()
                    expect(nav).to_be_hidden()
                    toggle.focus()
                    page.keyboard.press('Enter')
                    expect(nav).to_be_visible()
                    page.keyboard.press('Escape')
                    expect(nav).to_be_hidden()
                    expect(toggle).to_be_focused()
                    toggle.click()
                    page.wait_for_timeout(250)
                    page.mouse.click(width - 5, 150)
                    expect(nav).to_be_hidden()
                    toggle.click()
                    page.set_viewport_size({'width': 800, 'height': 900})
                    expect(nav).to_be_hidden()
                    expect(toggle).to_have_attribute('aria-expanded', 'false')
                    page.set_viewport_size({'width': width, 'height': 900})
                    expect(nav).to_be_hidden()
                page.wait_for_timeout(250)
                assert abs(page.locator('#wrap').bounding_box()['x']) < 1
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'), (url, width)
            print('PASS: mobile/desktop navigation:', url, flush=True)
        page.set_viewport_size({'width': 390, 'height': 900})
        page.goto(home, wait_until='load')
        page.locator('#main-nav-toggle').tap()
        link = page.locator('#mobile-nav').get_by_role('link', name='Archives', exact=True)
        target = urljoin(home, link.get_attribute('href'))
        link.tap()
        page.wait_for_url(target.rstrip('/') + '/**')
        expect(page.locator('#mobile-nav')).to_be_hidden()
        print('PASS: mobile Archives navigation', flush=True)
        browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', default='http://127.0.0.1:4017')
    validate(parser.parse_args().origin.rstrip('/'))

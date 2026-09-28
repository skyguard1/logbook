import unittest
from import_km_html import ElementInnerHTMLExtractor


class LegacyLayoutTests(unittest.TestCase):
    def test_void_tags_do_not_capture_platform_footer(self):
        parser = ElementInnerHTMLExtractor('article_content')
        inner = '<p>first<br>line<img src="x"><br/><hr></p><div>nested</div>'
        parser.feed('<div><div id="article_content">' + inner + '</div><aside>PRIVATE FOOTER</aside></div>')
        parser.close()
        self.assertEqual(parser.inner_html(), inner)

    def test_extractor_ignores_duplicate_target_and_optional_p_end(self):
        parser = ElementInnerHTMLExtractor('article_content')
        parser.feed('<div id="article_content"><p>one<p>two</div><div id="article_content">duplicate</div>')
        self.assertEqual(parser.inner_html(), '<p>one<p>two')



if __name__ == '__main__':
    unittest.main()


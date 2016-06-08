from __future__ import unicode_literals

import unittest
from hypothesis import given, example
from hypothesis.strategies import text
import CommonMark
from CommonMark.blocks import Parser
from CommonMark.render.html import HtmlRenderer
from CommonMark.inlines import InlineParser
from CommonMark.node import NodeWalker, Node
from CommonMark.utils import to_camel_case


class TestCommonmark(unittest.TestCase):
    def test_output(self):
        s = CommonMark.commonmark('*hello!*')
        self.assertEqual(s, '<p><em>hello!</em></p>\n')

    def test_unicode(self):
        s = CommonMark.commonmark('<div>\u2020</div>\n')
        self.assertEqual(s, '<div>\u2020</div>\n',
                         'Unicode works in an HTML block.')
        CommonMark.commonmark('* unicode: \u2020')
        CommonMark.commonmark('# unicode: \u2020')
        CommonMark.commonmark('```\n# unicode: \u2020\n```')

    def test_null_string_bug(self):
        s = CommonMark.commonmark('>     sometext\n>\n\n')
        self.assertEqual(
            s,
            '<blockquote>\n<pre><code>sometext\n</code></pre>'
            '\n</blockquote>\n')

    def test_dumpAST_orderedlist(self):
        md = '1.'
        ast = Parser().parse(md)
        CommonMark.dumpAST(ast)

    @given(text())
    def test_random_text(self, s):
        CommonMark.commonmark(s)


class TestHtmlRenderer(unittest.TestCase):
    def test_init(self):
        HtmlRenderer()


class TestInlineParser(unittest.TestCase):
    def test_init(self):
        InlineParser()


class TestNode(unittest.TestCase):
    def test_doc_node(self):
        Node('document', [[1, 1], [0, 0]])


class TestNodeWalker(unittest.TestCase):
    def test_node_walker(self):
        node = Node('document', [[1, 1], [0, 0]])
        NodeWalker(node)

    def test_node_walker_iter(self):
        node = Node('document', [[1, 1], [0, 0]])
        for subnode, entered in node.walker():
            pass


class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    @given(text())
    @example('')
    @example('* unicode: \u2020')
    def test_text(self, s):
        self.parser.parse(s)


class TestUtils(unittest.TestCase):
    def test_to_camel_case(self):
        self.assertEqual(to_camel_case('snake_case'), 'SnakeCase')
        self.assertEqual(to_camel_case(''), '')
        self.assertEqual(to_camel_case('word'), 'Word')

    @given(text())
    def test_random_text(self, s):
        to_camel_case(s)

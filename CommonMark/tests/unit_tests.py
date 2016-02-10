from __future__ import unicode_literals

import unittest
import CommonMark
from CommonMark.blocks import Parser
from CommonMark.html import HtmlRenderer
from CommonMark.inlines import InlineParser
from CommonMark.node import NodeWalker, Node


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


class TestHtmlRenderer(unittest.TestCase):
    def test_init(self):
        HtmlRenderer()


class TestInlineParser(unittest.TestCase):
    def test_init(self):
        InlineParser()


class TestNode(unittest.TestCase):
    def test_doc_node(self):
        Node('Document', [[1, 1], [0, 0]])


class TestNodeWalker(unittest.TestCase):
    def test_node_walker(self):
        node = Node('Document', [[1, 1], [0, 0]])
        NodeWalker(node)

    def test_node_walker_iter(self):
        node = Node('Document', [[1, 1], [0, 0]])
        for subnode, entered in node.walker():
            pass


class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def test_empty_string(self):
        self.parser.parse('')

    def test_unicode(self):
        self.parser.parse('* unicode: \u2020')

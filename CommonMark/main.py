# 2014 - Bibek Kafle & Roland Shoemaker
# 2015-2016 - Nik Nyby
# Port of @jgm's commonmark.js implementation of the CommonMark spec.

# Basic usage:
#
# import CommonMark
# parser = CommonMark.Parser()
# renderer = CommonMark.HtmlRenderer()
# print(renderer.render(parser.parse('Hello *world*')))

from __future__ import absolute_import, unicode_literals

from CommonMark.blocks import Parser
from CommonMark.dump import dumpAST, dumpJSON
from CommonMark.render.html import HtmlRenderer


def commonmark(text, format="html"):
    """Render CommonMark into HTML, JSON or AST
    Optional keyword arguments:
    format:     'html' (default), 'json' or 'ast'

    >>> commonmark("*hello!*")
    '<p><em>hello</em></p>\\n'
    """
    parser = Parser()
    ast = parser.parse(text)
    if format not in ["html", "json", "ast"]:
        raise ValueError("format must be 'html', 'json' or 'ast'")
    if format == "html":
        renderer = HtmlRenderer()
        return renderer.render(ast)
    if format == "json":
        return dumpJSON(ast)
    if format == "ast":
        return dumpAST(ast)

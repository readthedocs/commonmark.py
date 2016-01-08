#!/usr/bin/env python
# 2014 - Bibek Kafle & Roland Shoemaker
# Port of @jgm's JavaScript stmd.js implementation of the CommonMark spec

# Basic usage:
#
# import CommonMark
# parser = CommonMark.Parser()
# renderer = CommonMark.HtmlRenderer()
# print(renderer.render(parser.parse('Hello *world*')))
from __future__ import absolute_import, unicode_literals
import json
from builtins import str
from CommonMark.blocks import Parser
from CommonMark.html import HtmlRenderer


# Utility functions


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
        return ASTtoJSON(ast)
    if format == "ast":
        return dumpAST(ast)


def prepare(block):
    """ Strips circular 'parent' references and trims empty
    block elements."""
    to_remove = [
        'parent', 'nxt', 'prv', 'first_child', 'last_child',
    ]
    for r in to_remove:
        block.__dict__[r] = None
    if block.is_open is not None:
        block.__dict__['open'] = block.is_open
        del(block.is_open)
    # trim empty elements...
    for attr in dir(block):
        if not callable(attr) and not attr.startswith("__") and \
           attr not in ['pretty', 'is_container',
                        'append_child', 'prepend_child', 'unlink',
                        'insert_after', 'insert_before', 'walker']:
            if block.__dict__[attr] in ["", [], None, {}]:
                del(block.__dict__[attr])
    return block


def ASTtoJSON(block):
    """ Output AST in JSON form, this is destructive of block."""
    # sort_keys=True) # indent=4)
    return json.dumps(prepare(block), default=lambda o: o.__dict__)


def dumpAST(obj, ind=0, topnode=False):
    """ Print out a block/entire AST."""
    indChar = ("\t" * ind) + "-> " if ind else ""
    print(indChar + "[" + obj.t + "]")
    if not obj.title == "":
        print("\t" + indChar + "Title: " + (obj.title or ''))
    if not obj.info == "":
        print("\t" + indChar + "Info: " + (obj.info or ''))
    if not obj.destination == "":
        print("\t" + indChar + "Destination: " + (obj.destination or ''))
    if obj.is_open:
        print("\t" + indChar + "Open: " + str(obj.is_open))
    if obj.last_line_blank:
        print(
            "\t" + indChar + "Last line blank: " + str(obj.last_line_blank))
    if obj.sourcepos:
        print("\t" + indChar + "Sourcepos: " + str(obj.sourcepos))
    if not obj.string_content == "":
        print("\t" + indChar + "String content: " + (obj.string_content or ''))
    if not obj.info == "":
        print("\t" + indChar + "Info: " + (obj.info or ''))
    if not obj.literal == "":
        print("\t" + indChar + "Literal: " + (obj.literal or ''))
    if obj.list_data.get('type'):
        print("\t" + indChar + "List Data: ")
        print("\t\t" + indChar + "[type] = " + obj.list_data.get('type'))
        if obj.list_data.get('bullet_char'):
            print(
                "\t\t" + indChar + "[bullet_char] = " +
                obj.list_data['bullet_char'])
        if obj.list_data.get('start'):
            print("\t\t" + indChar + "[start] = " + obj.list_data.get('start'))
        if obj.list_data.get('delimiter'):
            print(
                "\t\t" + indChar + "[delimiter] = " +
                obj.list_data.get('delimiter'))
        if obj.list_data.get('padding'):
            print(
                "\t\t" + indChar + "[padding] = " +
                str(obj.list_data.get('padding')))
        if obj.list_data.get('marker_offset'):
            print(
                "\t\t" + indChar + "[marker_offset] = " +
                str(obj.list_data.get('marker_offset')))
    if obj.walker:
        print("\t" + indChar + "Children:")
        walker = obj.walker()
        nxt = walker.nxt()
        while nxt is not None and topnode is False:
            dumpAST(nxt['node'], ind + 2, topnode=True)
            nxt = walker.nxt()

#!/usr/bin/env python
# 2014 - Bibek Kafle & Roland Shoemaker
# Port of @jgm's JavaScript stmd.js implementation of the CommonMark spec

# Basic usage:
#
# import CommonMark
# parser = CommonMark.Parser()
# renderer = CommonMark.HtmlRenderer()
# print(renderer.render(parser.parse('Hello *world*')))
from __future__ import absolute_import
import re
import json
from CommonMark import common
from CommonMark.blocks import Parser
from CommonMark.html import HTMLRenderer


reEscapedChar = re.compile('^\\\\(' + common.ESCAPABLE + ')')
reAllTab = re.compile("\t")


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
        renderer = HTMLRenderer()
        return renderer.render(ast)
    if format == "json":
        return ASTtoJSON(ast)
    if format == "ast":
        return dumpAST(ast)


def ASTtoJSON(block):
    """ Output AST in JSON form, this is destructive of block."""
    def prepare(block):
        """ Strips circular 'parent' references and trims empty
        block elements."""
        if block.parent:
            block.parent = None
        if not block.__dict__['is_open'] is None:
            block.__dict__['open'] = block.is_open
            del(block.is_open)
        # trim empty elements...
        for attr in dir(block):
            if not callable(attr) and not attr.startswith("__") and \
               attr != "makeNode" and attr != "pretty":
                if block.__dict__[attr] in ["", [], None, {}]:
                    del(block.__dict__[attr])
        if 'children' in block.__dict__ and len(block.children) > 0:
            for i, child in enumerate(block.children):
                block.children[i] = prepare(child)
        if 'inline_content' in block.__dict__ and \
           len(block.inline_content) > 0:
            for i, child in enumerate(block.inline_content):
                block.inline_content[i] = prepare(child)
        if 'label' in block.__dict__ and len(block.label) > 0:
            for i, child in enumerate(block.label):
                block.label[i] = prepare(child)
        if 'c' in block.__dict__ and type(block.c) is list and \
           len(block.c) > 0:
            for i, child in enumerate(block.c):
                block.c[i] = prepare(child)
        return block
    # sort_keys=True) # indent=4)
    return json.dumps(prepare(block), default=lambda o: o.__dict__)


def dumpAST(obj, ind=0):
    """ Print out a block/entire AST."""
    indChar = ("\t" * ind) + "-> " if ind else ""
    print(indChar + "[" + obj.t + "]")
    if not obj.title == "":
        print("\t" + indChar + "Title: " + obj.title)
    if not obj.info == "":
        print("\t" + indChar + "Info: " + obj.info)
    if not obj.destination == "":
        print("\t" + indChar + "Destination: " + obj.destination)
    if obj.is_open:
        print("\t" + indChar + "Open: " + str(obj.is_open))
    if obj.last_line_blank:
        print(
            "\t" + indChar + "Last line blank: " + str(obj.last_line_blank))
    if obj.start_line:
        print("\t" + indChar + "Start line: " + str(obj.start_line))
    if obj.start_column:
        print("\t" + indChar + "Start Column: " + str(obj.start_column))
    if obj.end_line:
        print("\t" + indChar + "End line: " + str(obj.end_line))
    if not obj.string_content == "":
        print("\t" + indChar + "String content: " + obj.string_content)
    if not obj.info == "":
        print("\t" + indChar + "Info: " + obj.info)
    if len(obj.strings) > 0:
        print("\t" + indChar + "Strings: ['" + "', '".join(obj.strings) +
              "'']")
    if obj.c:
        if type(obj.c) is list:
            print("\t" + indChar + "c:")
            for b in obj.c:
                dumpAST(b, ind + 2)
        else:
            print("\t" + indChar + "c: "+obj.c)
    if obj.label:
        print("\t" + indChar + "Label:")
        for b in obj.label:
            dumpAST(b, ind + 2)
    if hasattr(obj.list_data, "type"):
        print("\t" + indChar + "List Data: ")
        print("\t\t" + indChar + "[type] = " + obj.list_data['type'])
        if hasattr(obj.list_data, "bullet_char"):
            print(
                "\t\t" + indChar + "[bullet_char] = " +
                obj.list_data['bullet_char'])
        if hasattr(obj.list_data, "start"):
            print("\t\t" + indChar + "[start] = " + obj.list_data['start'])
        if hasattr(obj.list_data, "delimiter"):
            print(
                "\t\t" + indChar + "[delimiter] = " +
                obj.list_data['delimiter'])
        if hasattr(obj.list_data, "padding"):
            print(
                "\t\t" + indChar + "[padding] = " + obj.list_data['padding'])
        if hasattr(obj.list_data, "marker_offset"):
            print(
                "\t\t" + indChar + "[marker_offset] = " +
                obj.list_data['marker_offset'])
    if len(obj.inline_content) > 0:
        print("\t" + indChar + "Inline content:")
        for b in obj.inline_content:
            dumpAST(b, ind + 2)
    if len(obj.children) > 0:
        print("\t" + indChar + "Children:")
        for b in obj.children:
            dumpAST(b, ind + 2)
    if len(obj.attributes):
        print("\t" + indChar + "Attributes:")
        for key, val in obj.attributes.iteritems():
            print("\t\t" + indChar + "[{0}] = {1}".format(key, val))

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
import sys
import json
from warnings import warn
from CommonMark import common
from CommonMark.blocks import Parser


# if python3 use html.parser and urllib.parse, else use HTMLParser and urllib
if sys.version_info >= (3, 0):
    import urllib.parse
    if sys.version_info >= (3, 4):
        import html.parser
        HTMLunescape = html.parser.HTMLParser().unescape
    else:
        from .entitytrans import _unescape
        HTMLunescape = _unescape
    HTMLquote = urllib.parse.quote
    HTMLunquote = urllib.parse.unquote
    URLparse = urllib.parse.urlparse
else:
    import urllib
    import urlparse
    from CommonMark import entitytrans
    HTMLunescape = entitytrans._unescape
    HTMLquote = urllib.quote
    HTMLunquote = urllib.unquote
    URLparse = urlparse.urlparse


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
        if not block.__dict__['isOpen'] is None:
            block.__dict__['open'] = block.isOpen
            del(block.isOpen)
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
    if obj.isOpen:
        print("\t" + indChar + "Open: " + str(obj.isOpen))
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


class HTMLRenderer(object):
    blocksep = "\n"
    innersep = "\n"
    softbreak = "\n"
    escape_pairs = (("[&]", '&amp;'),
                    ("[<]", '&lt;'),
                    ("[>]", '&gt;'),
                    ('["]', '&quot;'))

    @staticmethod
    def inTags(tag, attribs, contents, selfclosing=None):
        """ Helper function to produce content in a pair of HTML tags."""
        result = "<" + tag
        if (len(attribs) > 0):
            i = 0
            while (len(attribs) > i) and (not attribs[i] is None):
                attrib = attribs[i]
                result += (" " + attrib[0] + '="' + attrib[1] + '"')
                i += 1
        if (len(contents) > 0):
            result += ('>' + contents + '</' + tag + '>')
        elif (selfclosing):
            result += " />"
        else:
            result += ('></' + tag + '>')
        return result

    def __init__(self):
        pass

    def URLescape(self, s):
        """ Escape href URLs."""
        if not re.search("mailto|MAILTO", s):
            if sys.version_info >= (3, 0):
                return re.sub(
                    "[&](?![#](x[a-f0-9]{1,8}|[0-9]{1,8});" +
                    "|[a-z][a-z0-9]{1,31};)",
                    "&amp;",
                    HTMLquote(
                        HTMLunescape(s),
                        ":/=*%?&)(#"),
                    re.IGNORECASE)
            else:
                return re.sub(
                    "[&](?![#](x[a-f0-9]{1,8}|[0-9]{1,8});" +
                    "|[a-z][a-z0-9]{1,31};)",
                    "&amp;",
                    HTMLquote(
                        HTMLunescape(s).encode("utf-8"),
                        ":/=*%?&)(#"),
                    re.IGNORECASE)
        else:
            return s

    def escape(self, s, preserve_entities=None):
        """ Escape HTML entities."""
        if preserve_entities:
            e = self.escape_pairs[1:]
            s = re.sub(
                "[&](?![#](x[a-f0-9]{1,8}|[0-9]{1,8});|[a-z][a-z0-9]{1,31};)",
                "&amp;", HTMLunescape(s), re.IGNORECASE)
        else:
            e = self.escape_pairs
        for r in e:
            s = re.sub(r[0], r[1], s)
        return s

    def renderInline(self, inline):
        """ Render an inline element as HTML."""
        attrs = None
        if (inline.t == "Str"):
            return self.escape(inline.c)
        elif (inline.t == "Softbreak"):
            return self.softbreak
        elif inline.t == "Hardbreak":
            return self.inTags('br', [], "", True) + "\n"
        elif inline.t == "Emph":
            return self.inTags('em', [], self.renderInlines(inline.c))
        elif inline.t == "Strong":
            return self.inTags("strong", [], self.renderInlines(inline.c))
        elif inline.t == "Html":
            return inline.c
        elif inline.t == "Entity":
            if inline.c == "&nbsp;":
                return " "
            else:
                return self.escape(inline.c, True)
        elif inline.t == "Link":
            attrs = [['href', self.URLescape(inline.destination)]]
            if inline.title:
                attrs.append(['title', self.escape(inline.title, True)])
            return self.inTags('a', attrs, self.renderInlines(inline.label))
        elif inline.t == "Image":
            attrs = [['src', self.escape(inline.destination, True)], [
                     'alt', self.escape(self.renderInlines(inline.label))]]
            if inline.title:
                attrs.append(['title', self.escape(inline.title, True)])
            return self.inTags('img', attrs, "", True)
        elif inline.t == "Code":
            return self.inTags('code', [], self.escape(inline.c))
        else:
            warn("Unknown inline type " + inline.t)
            return ""

    def renderInlines(self, inlines):
        """ Render a list of inlines."""
        result = ''
        for i in range(len(inlines)):
            result += self.renderInline(inlines[i])
        return result

    def renderBlock(self,  block, in_tight_list):
        """ Render a single block element."""
        tag = attr = info_words = None
        if (block.t == "Document"):
            whole_doc = self.renderBlocks(block.children)
            if (whole_doc == ""):
                return ""
            else:
                return (whole_doc + "\n")
        elif (block.t == "Paragraph"):
            if (in_tight_list):
                return self.renderInlines(block.inline_content)
            else:
                return self.inTags('p', [],
                                   self.renderInlines(block.inline_content))
        elif (block.t == "BlockQuote"):
            filling = self.renderBlocks(block.children)
            if (filling == ""):
                a = self.innersep
            else:
                a = self.innersep + \
                    self.renderBlocks(block.children) + self.innersep
            return self.inTags('blockquote', [], a)
        elif (block.t == "Item"):
            return self.inTags("li", [],
                               self.renderBlocks(block.children,
                                                 in_tight_list).strip())
        elif (block.t == "List"):
            if (block.list_data['type'] == "Bullet"):
                tag = "ul"
            else:
                tag = "ol"
            attr = [] if (not block.list_data.get('start')) or block.list_data[
                'start'] == 1 else [['start', str(block.list_data['start'])]]
            return self.inTags(tag, attr,
                               self.innersep +
                               self.renderBlocks(block.children, block.tight) +
                               self.innersep)
        elif ((block.t == "ATXHeader") or (block.t == "SetextHeader")):
            tag = "h" + str(block.level)
            return self.inTags(tag, [],
                               self.renderInlines(block.inline_content))
        elif (block.t == "IndentedCode"):
            return HTMLRenderer.inTags('pre', [], HTMLRenderer.inTags('code',
                                       [], self.escape(block.string_content)))
        elif (block.t == "FencedCode"):
            info_words = []
            if block.info:
                info_words = re.split(r" +", block.info)
            attr = [] if len(info_words) == 0 else [
                ["class", "language-" + self.escape(info_words[0], True)]]
            return self.inTags('pre', [], self.inTags('code',
                               attr, self.escape(block.string_content)))
        elif (block.t == "HtmlBlock"):
            return block.string_content
        elif (block.t == "ReferenceDef"):
            return ""
        elif (block.t == "HorizontalRule"):
            return self.inTags("hr", [], "", True)
        else:
            warn("Unknown block type" + block.t)
            return ""

    def renderBlocks(self, blocks, in_tight_list=None):
        """ Render a list of block elements, separated by this.blocksep."""
        result = []
        for i in range(len(blocks)):
            if not blocks[i].t == "ReferenceDef":
                result.append(self.renderBlock(blocks[i], in_tight_list))
        return self.blocksep.join(result)

    def render(self,  block, in_tight_list=None):
        """ Pass through for renderBlock"""
        return self.renderBlock(block, in_tight_list)

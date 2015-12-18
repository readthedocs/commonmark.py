from __future__ import absolute_import

import re
import sys

from CommonMark.common import escape_xml

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


reHtmlTag = re.compile(r'\<[^>]*\>')
reUnsafeProtocol = re.compile(
    r'^javascript:|vbscript:|file:|data:', re.IGNORECASE)
reSafeDataProtocol = re.compile(
    r'^data:image\/(?:png|gif|jpeg|webp)', re.IGNORECASE)


def tag(name, attrs=[], selfclosing=False):
    """Helper function to produce an HTML tag."""
    result = u'<' + name
    for attr in attrs:
        result += u' {}="{}"'.format(attr[0], attr[1])
    if selfclosing:
        result += u' /'

    result += u'>'
    return result


def potentially_unsafe(url):
    return re.match(reUnsafeProtocol, url) and not \
        re.match(reSafeDataProtocol, url)


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

    @staticmethod
    def URLescape(s):
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

    def renderInlines(self, inlines):
        """ Render a list of inlines."""
        result = ''
        for i in range(len(inlines)):
            result += self.renderInline(inlines[i])
        return result

    def out(self, s):
        if self.disable_tags > 0:
            self.buf += re.sub(reHtmlTag, '', s)
        else:
            self.buf += s
        self.last_out = s

    def cr(self):
        if self.last_out != '\n':
            self.buf += '\n'
            self.last_out = '\n'

    def renderNodes(self, block):
        walker = block.walker()
        self.buf = ''
        self.last_out = '\n'
        self.disable_tags = 0

        event = walker.nxt()
        while event is not None:
            attrs = []
            entering = event['entering']
            node = event['node']
            if node.t == 'Text' or node.t == 'Str':
                self.out(escape_xml(node.literal, False))
            elif node.t == 'Softbreak':
                self.out(self.softbreak)
            elif node.t == 'Hardbreak':
                self.out(tag('br', [], True))
                self.cr()
            elif node.t == 'Emph':
                self.out(tag('em' if entering else '/em'))
            elif node.t == 'Strong':
                self.out(tag('strong' if entering else '/strong'))
            elif node.t == 'HtmlInline':
                self.out(node.literal)
            elif node.t == 'Link':
                if entering:
                    if not potentially_unsafe(node.destination):
                        attrs.insert(
                            0,
                            ['href', escape_xml(node.destination, True)])
                    if node.title:
                        attrs.insert(
                            0,
                            ['title', escape_xml(node.title, True)])
                    self.out(tag('a', attrs))
                else:
                    self.out(tag('/a'))
            elif node.t == 'Image':
                if entering:
                    if self.disable_tags == 0:
                        self.out(
                            '<img src="{}" alt="'.format(
                                escape_xml(node.destination, True)))
                    self.disable_tags += 1
                else:
                    self.disable_tags -= 1
                    if self.disable_tags == 0:
                        if node.title:
                            self.out('" title="' +
                                     escape_xml(node.title, True))
                        self.out('" />')
            elif node.t == 'Code':
                self.out(
                    tag('code') +
                    escape_xml(node.literal, False) +
                    tag('/code'))
            elif node.t == 'Document':
                pass
            elif node.t == 'Paragraph':
                grandparent = node.parent.parent
                if grandparent is not None and \
                   grandparent.t == 'List' and \
                   grandparent.list_data.get('tight'):
                    pass
                else:
                    if entering:
                        self.cr()
                        self.out(tag('p', attrs))
                    else:
                        self.out(tag('/p'))
                        self.cr()
            elif node.t == 'BlockQuote':
                if entering:
                    self.cr()
                    self.out(tag('blockquote', attrs))
                    self.cr()
                else:
                    self.cr()
                    self.out(tag('/blockquote', attrs))
                    self.cr()
            elif node.t == 'Item':
                if entering:
                    self.out(tag('li', attrs))
                else:
                    self.out(tag('/li'))
                    self.cr()
            elif node.t == 'List':
                if node.list_data['type'] == 'Bullet':
                    tagname = 'ul'
                else:
                    tagname = 'ol'
                if entering:
                    try:
                        start = node.list_data['start']
                    except KeyError:
                        start = None
                    if start is not None and start != 1:
                        attrs.append(['start', str(start)])
                    self.cr()
                    self.out(tag(tagname, attrs))
                    self.cr()
                else:
                    self.cr()
                    self.out(tag('/' + tagname))
                    self.cr()
            elif (node.t == 'Heading' or node.t == 'ATXHeader' or
                  node.t == 'SetextHeader'):
                tagname = 'h' + str(node.level)
                if entering:
                    self.cr()
                    self.out(tag(tagname, attrs))
                else:
                    self.out(tag('/' + tagname))
                    self.cr()
            elif node.t == 'CodeBlock' or node.t == 'FencedCode':
                if node.info:
                    info_words = re.split(r'\s+', node.info)
                else:
                    info_words = []
                if len(info_words) > 0 and len(info_words[0]) > 0:
                    attrs.append([
                        'class',
                        'language-' + escape_xml(info_words[0], True)
                    ])
                self.cr()
                self.out(tag('pre') + tag('code', attrs))
                self.out(escape_xml(node.literal, False))
                self.out(tag('/code') + tag('/pre'))
                self.cr()
            elif node.t == 'HtmlBlock':
                self.out(str(node.literal))
            elif node.t == 'ThematicBreak':
                self.cr()
                self.out(tag('hr', attrs, True))
                self.cr()
            else:
                raise ValueError('Unknown node type {}'.format(node.t))
            event = walker.nxt()
        return self.buf

    render = renderNodes

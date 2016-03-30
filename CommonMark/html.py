from __future__ import absolute_import, unicode_literals

import re
from builtins import str
from CommonMark.common import escape_xml


reHtmlTag = re.compile(r'\<[^>]*\>')
reUnsafeProtocol = re.compile(
    r'^javascript:|vbscript:|file:|data:', re.IGNORECASE)
reSafeDataProtocol = re.compile(
    r'^data:image\/(?:png|gif|jpeg|webp)', re.IGNORECASE)


def tag(name, attrs=[], selfclosing=False):
    """Helper function to produce an HTML tag."""
    result = '<' + name
    for attr in attrs:
        result += ' {0}="{1}"'.format(attr[0], attr[1])
    if selfclosing:
        result += ' /'

    result += '>'
    return result


def potentially_unsafe(url):
    return re.search(reUnsafeProtocol, url) and not \
        re.search(reSafeDataProtocol, url)


class HtmlRenderer(object):

    def __init__(self, options={}, softbreak='\n'):
        # by default, soft breaks are rendered as newlines in HTML.
        # set to "<br />" to make them hard breaks
        # set to " " if you want to ignore line wrapping in source
        self.softbreak = softbreak
        self.options = options

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
            entering = event['entering']
            node = event['node']

            attrs = []
            if self.options.get('sourcepos'):
                pos = node.sourcepos
                if pos:
                    attrs.push([
                        'data-sourcepos',
                        pos[0][0] + ':' + pos[0][1] + '-' +
                        pos[1][0] + ':' + pos[1][1]])

            if node.t == 'text':
                self.out(escape_xml(node.literal, False))
            elif node.t == 'softbreak':
                self.out(self.softbreak)
            elif node.t == 'linebreak':
                self.out(tag('br', [], True))
                self.cr()
            elif node.t == 'emph':
                self.out(tag('em' if entering else '/em'))
            elif node.t == 'strong':
                self.out(tag('strong' if entering else '/strong'))
            elif node.t == 'html_inline':
                if self.options.get('safe'):
                    self.out('<!-- raw HTML omitted -->')
                else:
                    self.out(node.literal)
            elif node.t == 'custom_inline':
                if entering and node.on_enter:
                    self.out(node.on_enter)
                elif not entering and node.on_exit:
                    self.out(node.on_exit)
            elif node.t == 'link':
                if entering:
                    if not (self.options.get('safe') and
                            potentially_unsafe(node.destination)):
                        attrs.append([
                            'href',
                            escape_xml(node.destination, True)
                        ])
                    if node.title:
                        attrs.append(['title', escape_xml(node.title, True)])
                    self.out(tag('a', attrs))
                else:
                    self.out(tag('/a'))
            elif node.t == 'image':
                if entering:
                    if self.disable_tags == 0:
                        if self.options.get('safe') and \
                           potentially_unsafe(node.destination):
                            self.out('<img src="" alt="')
                        else:
                            self.out(
                                '<img src="{0}" alt="'.format(
                                    escape_xml(node.destination, True)))
                    self.disable_tags += 1
                else:
                    self.disable_tags -= 1
                    if self.disable_tags == 0:
                        if node.title:
                            self.out('" title="' +
                                     escape_xml(node.title, True))
                        self.out('" />')
            elif node.t == 'code':
                self.out(
                    tag('code') +
                    escape_xml(node.literal, False) +
                    tag('/code'))
            elif node.t == 'document':
                pass
            elif node.t == 'paragraph':
                grandparent = node.parent.parent
                if grandparent is not None and \
                   grandparent.t == 'list' and \
                   grandparent.list_data.get('tight'):
                    pass
                else:
                    if entering:
                        self.cr()
                        self.out(tag('p', attrs))
                    else:
                        self.out(tag('/p'))
                        self.cr()
            elif node.t == 'block_quote':
                if entering:
                    self.cr()
                    self.out(tag('blockquote', attrs))
                    self.cr()
                else:
                    self.cr()
                    self.out(tag('/blockquote'))
                    self.cr()
            elif node.t == 'item':
                if entering:
                    self.out(tag('li', attrs))
                else:
                    self.out(tag('/li'))
                    self.cr()
            elif node.t == 'list':
                tagname = 'ul' if node.list_data['type'] == 'bullet' else 'ol'
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
            elif node.t == 'heading':
                tagname = 'h' + str(node.level)
                if entering:
                    self.cr()
                    self.out(tag(tagname, attrs))
                else:
                    self.out(tag('/' + tagname))
                    self.cr()
            elif node.t == 'code_block':
                info_words = re.split(r'\s+', node.info) if node.info else []
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
            elif node.t == 'html_block':
                if self.options.get('safe'):
                    self.out('<!-- raw HTML omitted -->')
                else:
                    self.out(str(node.literal))
                self.cr()
            elif node.t == 'custom_block':
                self.cr()
                if entering and node.on_enter:
                    self.out(node.on_enter)
                elif not entering and node.on_exit:
                    self.out(node.on_exit)
                self.cr()
            elif node.t == 'thematic_break':
                self.cr()
                self.out(tag('hr', attrs, True))
                self.cr()
            else:
                raise ValueError('Unknown node type {0}'.format(node.t))
            event = walker.nxt()
        return self.buf

    render = renderNodes

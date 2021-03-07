""" Renders to SSML spec subset, compatible with AWS Polly and Google Cloud Text-to-Speech """
from __future__ import unicode_literals

import re
from builtins import str
from commonmark.common import escape_xml
from commonmark.render.renderer import Renderer

reUnsafeProtocol = re.compile(
    r'^javascript:|vbscript:|file:|data:', re.IGNORECASE)
reSafeDataProtocol = re.compile(
    r'^data:image\/(?:png|gif|jpeg|webp)', re.IGNORECASE)


def potentially_unsafe(url):
    return re.search(reUnsafeProtocol, url) and \
           (not re.search(reSafeDataProtocol, url))


class SsmlRenderer(Renderer):
    def __init__(self, options={}):
        #  by default, soft breaks are rendered as newlines in HTML
        options['softbreak'] = options.get('softbreak') or '\n'
        # set to "<br />" to make them hard breaks
        # set to " " if you want to ignore line wrapping in source

        # SSML document start with a tag
        self.disable_tags = 0
        self.last_out = '\n'
        self.options = options

    def document(self, node, entering):
        """
        Starts and stops a SSML document
        """
        if entering:
            self.buf = '<speak>'
        else:
            self.buf += '</speak>'

    def escape(self, text):
        return escape_xml(text)

    def tag(self, name, attrs=None, selfclosing=None):
        """Helper function to produce an HTML tag."""
        if self.disable_tags > 0:
            return

        self.buf += '<' + name
        if attrs and len(attrs) > 0:
            for attrib in attrs:
                self.buf += ' ' + attrib[0] + '="' + attrib[1] + '"'

        if selfclosing:
            self.buf += ' /'

        self.buf += '>'
        self.last_out = '>'

    # Node methods #

    def text(self, node, entering=None):
        self.out(node.literal)

    def softbreak(self, node=None, entering=None):
        self.lit(self.options['softbreak'])

    def linebreak(self, node=None, entering=None):
        # self.tag('br', [], True)
        self.cr()

    def link(self, node, entering):
        attrs = self.attrs(node)
        if entering:
            if not (self.options.get('safe') and
                    potentially_unsafe(node.destination)):
                attrs.append(['href', self.escape(node.destination)])

            if node.title:
                attrs.append(['title', self.escape(node.title)])

            self.tag('a', attrs)
        else:
            self.tag('/a')

    def image(self, node, entering):
        if entering:
            if self.disable_tags == 0:
                if self.options.get('safe') and \
                        potentially_unsafe(node.destination):
                    self.lit('<img src="" alt="')
                else:
                    self.lit('<img src="' +
                             self.escape(node.destination) +
                             '" alt="')
            self.disable_tags += 1
        else:
            self.disable_tags -= 1
            if self.disable_tags == 0:
                if node.title:
                    self.lit('" title="' + self.escape(node.title))
                self.lit('" />')

    def emph(self, node, entering):
        if entering:
            self.tag('emphasis', attrs=[('level', 'moderate')])
        else:
            self.tag('/emphasis')

    def strong(self, node, entering):
        if entering:
            self.tag('emphasis', attrs=[('level', 'strong')])
        else:
            self.tag('/emphasis')

    def paragraph(self, node, entering):
        grandparent = node.parent.parent
        attrs = self.attrs(node)
        if grandparent is not None and grandparent.t == 'list':
            if grandparent.list_data['tight']:
                return

        if entering:
            self.cr()
            # self.tag('p', attrs)
        else:
            # self.tag('/p')
            self.cr()

    def heading(self, node, entering):
        # Headings render as prosody with -1 semitone per level
        tagname = 'prosody'
        attrs = self.attrs(node)
        attrs.append(('pitch', '-' + str(node.level) + 'st'))
        attrs.append(('rate', 'slow'))
        attrs.append(('volume', 'loud'))
        # print(f"heading attrs: {attrs}")
        if entering:
            self.cr()
            self.tag('break', attrs=[('time', '200ms')], selfclosing=True)
            self.tag(tagname, attrs)
        else:
            self.tag('/' + tagname)
            self.tag('break', attrs=[('time', '200ms')], selfclosing=True)
            self.cr()

    def code(self, node, entering):
        tagname = 'prosody'
        attrs = self.attrs(node)
        attrs.append(('pitch', '+2st'))
        # code blocks only have `entering=True`
        self.tag(tagname, attrs)
        self.out(node.literal)
        self.tag('/' + tagname)


    def code_block(self, node, entering):
        tagname = 'prosody'
        attrs = self.attrs(node)
        attrs.append(('pitch', '+2st'))

        self.tag('break', attrs=[('time', '200ms')], selfclosing=True)
        self.tag(tagname, attrs)
        self.out(node.literal)
        self.tag('/' + tagname)
        self.tag('break', attrs=[('time', '200ms')], selfclosing=True)


    def thematic_break(self, node, entering):
        self.tag('break', attrs=[('time', '2s')], selfclosing=True)

    def block_quote(self, node, entering):
        tagname = 'prosody'
        attrs = self.attrs(node)
        attrs.append(('pitch', '-2st'))

        if entering:
            self.tag('break', attrs=[('time', '200ms')], selfclosing=True)
            self.tag(tagname, attrs)
        else:
            self.tag('/' + tagname)
            self.tag('break', attrs=[('time', '200ms')], selfclosing=True)
        self.out(node.literal)

    # Pause before starting to read off a list
    list_counter = 0
    def list(self, node, entering):
        if entering:
            # self.tag('break', attrs=[('time', '500ms')], selfclosing=True)
            self.cr()
            global list_counter
            list_counter = 1
        else:
            self.tag('break', attrs=[('time', '500ms')], selfclosing=True)
            self.cr()

    def item(self, node, entering):
        attrs = self.attrs(node)
        attrs.append(('interpret-as', 'cardinal'))
        if entering:
            self.cr()
            self.tag('say-as', attrs)
            global list_counter
            # self.out(f"{list_counter}")
            list_counter += 1
            self.tag('/say-as')
            self.tag('break', attrs=[('time', '200ms')], selfclosing=True)
        else:
            self.cr()

    # def html_inline(self, node, entering):
    #     if self.options.get('safe'):
    #         self.lit('<!-- raw HTML omitted -->')
    #     else:
    #         self.lit(node.literal)
    #
    # def html_block(self, node, entering):
    #     self.cr()
    #     if self.options.get('safe'):
    #         self.lit('<!-- raw HTML omitted -->')
    #     else:
    #         self.lit(node.literal)
    #     self.cr()
    #
    # def custom_inline(self, node, entering):
    #     if entering and node.on_enter:
    #         self.lit(node.on_enter)
    #     elif (not entering) and node.on_exit:
    #         self.lit(node.on_exit)
    #
    # def custom_block(self, node, entering):
    #     self.cr()
    #     if entering and node.on_enter:
    #         self.lit(node.on_enter)
    #     elif (not entering) and node.on_exit:
    #         self.lit(node.on_exit)
    #     self.cr()

    # Helper methods #

    def out(self, s):
        self.lit(self.escape(s))

    def attrs(self, node):
        att = []
        if self.options.get('sourcepos'):
            pos = node.sourcepos
            if pos:
                att.append(['data-sourcepos', str(pos[0][0]) + ':' +
                            str(pos[0][1]) + '-' + str(pos[1][0]) + ':' +
                            str(pos[1][1])])

        return att

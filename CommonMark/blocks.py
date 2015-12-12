from __future__ import absolute_import

import re
from CommonMark import common
from CommonMark.common import unescape
from CommonMark.inlines import InlineParser
from CommonMark.node import Node


reATXHeaderMarker = re.compile(r'^#{1,6}(?: +|$)')
reBulletListMarker = re.compile(r'^[*+-]( +|$)')
reOrderedListMarker = re.compile(r'^(\d+)([.)])( +|$)')
reHtmlBlockOpen = re.compile(r'^' + common.HTMLBLOCKOPEN, re.IGNORECASE)
reHrule = re.compile(r'^(?:(?:\* *){3,}|(?:_ *){3,}|(?:- *){3,}) *$')
reCodeFence = re.compile(r'^`{3,}(?!.*`)|^~{3,}(?!.*~)')
reClosingCodeFence = re.compile(r'^(?:`{3,}|~{3,})(?= *$)')
reLineEnding = re.compile(r'\r\n|\n|\r')
reSetextHeaderLine = re.compile(r'^(?:=+|-+) *$')


def detabLine(text):
    """ Convert tabs to spaces on each line using a 4-space tab stop."""
    if re.match('\t', text) and text.index('\t') == -1:
        return text
    else:
        def tabber(m):
            result = "    "[(m.end() - 1 - tabber.lastStop) % 4:]
            tabber.lastStop = m.end()
            return result
        tabber.lastStop = 0
        text = re.sub("\t", tabber, text)
        return text


def isBlank(s):
    """ Returns True if string contains only space characters."""
    return bool(re.compile("^\s*$").match(s))


def matchAt(pattern, s, offset):
    """ Attempt to match a regex in string s at offset offset.
    Return index of match or None."""
    matched = re.search(pattern, s[offset:])
    if matched:
        return offset + s[offset:].index(matched.group(0))
    else:
        return None


class Parser:

    def __init__(self, subject=None, pos=0):
        self.doc = Node.makeNode("Document", 1, 1)
        self.subject = subject
        self.pos = pos
        self.tip = self.doc
        self.refmap = {}
        self.inlineParser = InlineParser()

    def acceptsLines(self, block_type):
        """ Returns true if block type can accept lines of text."""
        return block_type == 'Paragraph' or \
            block_type == 'IndentedCode' or \
            block_type == 'FencedCode' or \
            block_type == 'HtmlBlock'

    def endsWithBlankLine(self, block):
        """ Returns true if block ends with a blank line,
        descending if needed into lists and sublists."""
        if block.last_line_blank:
            return True
        if (block.t == "List" or block.t == "Item") and \
           len(block.children) > 0:
            return self.endsWithBlankLine(block.children[-1])
        else:
            return False

    def breakOutOfLists(self, block, line_number):
        """ Break out of all containing lists, resetting the tip of the
        document to the parent of the highest list, and finalizing
        all the lists.  (This is used to implement the "two blank lines
        break out of all lists" feature.)"""
        b = block
        last_list = None
        while True:
            if (b.t == "List"):
                last_list = b
            b = b.parent
            if not b:
                break

        if (last_list):
            while block != last_list:
                self.finalize(block, line_number)
                block = block.parent
            self.finalize(last_list, line_number)
            self.tip = last_list.parent

    def addLine(self, ln, offset):
        """ Add a line to the block at the tip.  We assume the tip
        can accept lines -- that check should be done before calling this."""
        s = ln[offset:]
        if not self.tip.is_open:
            raise Exception(
                "Attempted to add line (" + ln + ") to closed container.")
        self.tip.strings.append(s)

    def addChild(self, tag, line_number, offset):
        """ Add block of type tag as a child of the tip.  If the tip can't
        accept children, close and finalize it and try its parent,
        and so on til we find a block that can accept children."""
        while not (self.tip.t == "Document" or
                   self.tip.t == "BlockQuote" or
                   self.tip.t == "Item" or
                   (self.tip.t == "List" and tag == "Item")):
            self.finalize(self.tip, line_number - 1)
        column_number = offset + 1
        newNode = Node.makeNode(tag, line_number, column_number)
        self.tip.children.append(newNode)
        newNode.parent = self.tip
        self.tip = newNode
        return newNode

    def listsMatch(self, list_data, item_data):
        """ Returns true if the two list items are of the same type,
        with the same delimiter and bullet character.  This is used
        in agglomerating list items into lists."""
        return (list_data.get("type", None) ==
                item_data.get("type", None) and
                list_data.get("delimiter", None) ==
                item_data.get("delimiter", None) and
                list_data.get("bullet_char", None) ==
                item_data.get("bullet_char", None))

    def parseListMarker(self, ln, offset):
        """ Parse a list marker and return data on the marker (type,
        start, delimiter, bullet character, padding) or None."""
        rest = ln[offset:]
        data = {}
        blank_item = bool()
        if re.match(reHrule, rest):
            return None
        match = re.search(reBulletListMarker, rest)
        match2 = re.search(reOrderedListMarker, rest)
        if match:
            spaces_after_marker = len(match.group(1))
            data['type'] = 'Bullet'
            data['bullet_char'] = match.group(0)[0]
            blank_item = match.group(0) == len(rest)
        elif match2:
            spaces_after_marker = len(match2.group(3))
            data['type'] = 'Ordered'
            data['start'] = int(match2.group(1))
            data['delimiter'] = match2.group(2)
            blank_item = match2.group(0) == len(rest)
        else:
            return None
        if spaces_after_marker >= 5 or spaces_after_marker < 1 or blank_item:
            if match:
                data['padding'] = len(match.group(0)) - spaces_after_marker + 1
            elif match2:
                data['padding'] = len(
                    match2.group(0)) - spaces_after_marker + 1
        else:
            if match:
                data['padding'] = len(match.group(0))
            elif match2:
                data['padding'] = len(match2.group(0))
        return data

    def parseIAL(self, ln):
        values = []
        css_class = re.findall(r"\.(\w+) *", ln)
        if css_class:
            values.append(("class", " ".join(css_class)))
        css_id = re.findall(r"\#.(\w+) *", ln)
        if css_id:
            values.append(("id", css_id[0]))
        keyed_values = re.findall(r"(\w+)(?:=(\w+))? *", ln)
        if keyed_values:
            values += keyed_values

        return dict(values)

    def incorporateLine(self, ln, line_number):
        """ Analyze a line of text and update the document appropriately.
        We parse markdown text by calling this on each line of input,
        then finalizing the document."""
        all_matched = True
        offset = 0
        CODE_INDENT = 4
        blank = None
        already_done = False

        container = self.doc
        oldtip = self.tip

        ln = detabLine(ln)

        while len(container.children) > 0:
            last_child = container.children[-1]
            if not last_child.is_open:
                break
            container = last_child

            match = matchAt(r"[^ ]", ln, offset)
            if match is None:
                first_nonspace = len(ln)
                blank = True
            else:
                first_nonspace = match
                blank = False
            indent = first_nonspace - offset
            if container.t == "BlockQuote":
                matched = bool()
                if len(ln) > first_nonspace and len(ln) > 0:
                    matched = ln[first_nonspace] == ">"
                matched = indent <= 3 and matched
                if matched:
                    offset = first_nonspace + 1
                    try:
                        if ln[offset] == " ":
                            offset += 1
                    except IndexError:
                        pass
                else:
                    all_matched = False
            elif container.t == "Item":
                if (indent >= container.list_data['marker_offset'] +
                   container.list_data['padding']):
                    offset += container.list_data[
                        'marker_offset'] + container.list_data['padding']
                elif blank:
                    offset = first_nonspace
                else:
                    all_matched = False
            elif container.t == "IndentedCode":
                if indent >= CODE_INDENT:
                    offset += CODE_INDENT
                elif blank:
                    offset = first_nonspace
                else:
                    all_matched = False
            elif container.t in ["ATXHeader",
                                 "SetextHeader",
                                 "HorizontalRule"]:
                all_matched = False
            elif container.t == "FencedCode":
                i = container.fence_offset
                while i > 0 and len(ln) > offset and ln[offset] == " ":
                    offset += 1
                    i -= 1
            elif container.t == "HtmlBlock":
                if blank:
                    all_matched = False
            elif container.t == "Paragraph":
                if blank:
                    container.last_line_blank = True
                    all_matched = False
            if not all_matched:
                container = container.parent
                break
        last_matched_container = container

        def closeUnmatchedBlocks(self, already_done, oldtip):
            """ This function is used to finalize and close any unmatched
            blocks.  We aren't ready to do this now, because we might
            have a lazy paragraph continuation, in which case we don't
            want to close unmatched blocks.  So we store this closure for
            use later, when we have more information."""
            while not already_done and not oldtip == last_matched_container:
                self.finalize(oldtip, line_number)
                oldtip = oldtip.parent
            return True, oldtip

        if blank and container.last_line_blank:
            self.breakOutOfLists(container, line_number)

        while container.t != "ExtensionBlock" and \
                container.t != "FencedCode" and \
                container.t != "IndentedCode" and \
                container.t != "HtmlBlock" and \
                matchAt(r"^[ #`~*+_=<>0-9-{]", ln, offset) is not None:
            match = matchAt("[^ ]", ln, offset)
            if match is None:
                first_nonspace = len(ln)
                blank = True
            else:
                first_nonspace = match
                blank = False
            ATXmatch = re.search(reATXHeaderMarker, ln[first_nonspace:])
            FENmatch = re.search(reCodeFence, ln[first_nonspace:])
            PARmatch = re.search(reSetextHeaderLine, ln[first_nonspace:])
            IALmatch = re.search(r"^{:((\}|[^}])*)} *$", ln[first_nonspace:])
            EXTmatch = re.search(r"^{::((\\\}|[^\\}])*)/?} *$",
                                 ln[first_nonspace:])
            data = self.parseListMarker(ln, first_nonspace)

            indent = first_nonspace - offset
            if data:
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                data['marker_offset'] = indent
                offset = first_nonspace + data['padding']
                if not container.t == "List" or not self.listsMatch(
                   container.list_data, data):
                    container = self.addChild(
                        "List", line_number, first_nonspace)
                    container.list_data = data
                container = self.addChild(
                    "Item", line_number, first_nonspace)
                container.list_data = data
            elif indent >= CODE_INDENT:
                if not self.tip.t == "Paragraph" and not blank:
                    offset += CODE_INDENT
                    already_done, oldtip = closeUnmatchedBlocks(
                        self, already_done, oldtip)
                    container = self.addChild(
                        'IndentedCode', line_number, offset)
                else:
                    break
            elif len(ln) > first_nonspace and ln[first_nonspace] == ">":
                offset = first_nonspace + 1
                try:
                    if ln[offset] == " ":
                        offset += 1
                except IndexError:
                    pass
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild("BlockQuote", line_number, offset)
            elif EXTmatch:
                args = EXTmatch.group(1)
                keyed_values = re.findall(r"(\w+)(?:=(\w+))? *", args)
                offset = first_nonspace + len(EXTmatch.group(0))
                print("EXT {} {}".format(args, offset))
                already_done, oldtip = closeUnmatchedBlocks(self,
                                                            already_done,
                                                            oldtip)
                container = self.addChild("ExtensionBlock", line_number,
                                          first_nonspace)
                container.title = keyed_values.pop(0)[0]
                container.attributes = dict(keyed_values)
                print(EXTmatch.group(0))
                print(args)
                if (EXTmatch.group(0)[-2] == '/'):
                    self.finalize(container, line_number)

                break
            elif IALmatch:
                offset = first_nonspace + len(IALmatch.group(0))
                print("Found {}".format(IALmatch.group(0)))
                print("blank {}".format(blank))
                print("container {} {}".format(
                    self.tip.t,
                    container.last_line_blank))
                if blank:
                    # FIXME
                    # attributes.update(self.parseIAL(IALmatch.group(1)))
                    pass
                else:
                    self.tip.attributes = self.parseIAL(IALmatch.group(1))
                break
            elif ATXmatch:
                offset = first_nonspace + len(ATXmatch.group(0))
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild(
                    "ATXHeader", line_number, first_nonspace)
                container.level = len(ATXmatch.group(0).strip())
                if not re.search(r'\\#', ln[offset:]) is None:
                    container.strings = [
                        re.sub(r'(?:(\\#) *#*| *#+) *$', '\g<1>', ln[offset:])]
                else:
                    container.strings = [
                        re.sub(r'(?:(\\#) *#*| *#+) *$', '', ln[offset:])]
                break
            elif FENmatch:
                fence_length = len(FENmatch.group(0))
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild(
                    "FencedCode", line_number, first_nonspace)
                container.fence_length = fence_length
                container.fence_char = FENmatch.group(0)[0]
                container.fence_offset = first_nonspace - offset
                offset = first_nonspace + fence_length
                break
            elif not matchAt(reHtmlBlockOpen, ln, first_nonspace) is None:
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild(
                    'HtmlBlock', line_number, first_nonspace)
                break
            elif container.t == "Paragraph" and \
                    len(container.strings) == 1 and PARmatch:
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container.t = "SetextHeader"
                container.level = 1 if PARmatch.group(0)[0] == '=' else 2
                offset = len(ln)
            elif not matchAt(reHrule, ln, first_nonspace) is None:
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild(
                    "HorizontalRule", line_number, first_nonspace)
                offset = len(ln) - 1
                break
            else:
                break
            if self.acceptsLines(container.t):
                break

        match = matchAt(r"[^ ]", ln, offset)
        if match is None:
            first_nonspace = len(ln)
            blank = True
        else:
            first_nonspace = match
            blank = False
        indent = first_nonspace - offset

        if not self.tip == last_matched_container and \
           not blank and self.tip.t == "Paragraph" and \
           len(self.tip.strings) > 0:
            self.last_line_blank = False
            self.addLine(ln, offset)
        else:
            already_done, oldtip = closeUnmatchedBlocks(
                self, already_done, oldtip)
            container.last_line_blank = \
                blank and \
                not (container.t == "BlockQuote" or
                     container.t == "FencedCode" or
                     (container.t == "Item" and
                      len(container.children) == 0 and
                      container.start_line == line_number))
            cont = container
            while cont.parent:
                cont.parent.last_line_blank = False
                cont = cont.parent
            if container.t == "IndentedCode" or container.t == "HtmlBlock":
                self.addLine(ln, offset)
            if container.t == "ExtensionBlock":
                EXTmatch = re.search(r"^{:/((\\\}|[^\\}])*)} *$",
                                     ln[first_nonspace:])
                if EXTmatch:
                    self.finalize(container, line_number)
                else:
                    self.addLine(ln, offset)
            elif container.t == "FencedCode":
                match = bool()
                if len(ln) > 0:
                    match = len(ln) > first_nonspace and \
                        ln[first_nonspace] == container.fence_char and \
                        re.match(
                            r"^(?:`{3,}|~{3,})(?= *$)",
                            ln[first_nonspace:])
                match = indent <= 3 and match
                FENmatch = re.search(
                    r"^(?:`{3,}|~{3,})(?= *$)", ln[first_nonspace:])
                if match and len(FENmatch.group(0)) >= container.fence_length:
                    self.finalize(container, line_number)
                else:
                    self.addLine(ln, offset)
            elif container.t in ["ATXHeader", "SetextHeader", "HtmlBlock"]:
                # nothing to do; we already added the contents.
                pass
            else:
                if self.acceptsLines(container.t):
                    self.addLine(ln, first_nonspace)
                elif blank:
                    pass
                elif container.t != "HorizontalRule" and \
                        container.t != "SetextHeader":
                    container = self.addChild(
                        "Paragraph", line_number, first_nonspace)
                    self.addLine(ln, first_nonspace)
                else:
                    # print("Line " + str(line_number) +
                    #       " with container type " +
                    #       container.t + " did not match any condition.")
                    pass

    def finalize(self, block, line_number):
        """ Finalize a block.  Close it and do any necessary postprocessing,
        e.g. creating string_content from strings, setting the 'tight'
        or 'loose' status of a list, and parsing the beginnings
        of paragraphs for reference definitions.  Reset the tip to the
        parent of the closed block."""
        if (not block.is_open):
            return 0

        block.is_open = False
        if (line_number > block.start_line):
            block.end_line = line_number - 1
        else:
            block.end_line = line_number

        if (block.t == "Paragraph"):
            block.string_content = ""
            for i, line in enumerate(block.strings):
                block.strings[i] = re.sub(r'^  *', '', line, re.MULTILINE)
            block.string_content = '\n'.join(block.strings)

            pos = self.inlineParser.parseReference(
                block.string_content, self.refmap)
            while (block.string_content[0] == "[" and pos):
                block.string_content = block.string_content[pos:]
                if (isBlank(block.string_content)):
                    block.t = "ReferenceDef"
                    break
                pos = self.inlineParser.parseReference(
                    block.string_content, self.refmap)
        elif (block.t in ["ATXHeader", "SetextHeader", "HtmlBlock"]):
            block.string_content = "\n".join(block.strings)
        elif (block.t == "IndentedCode"):
            block.string_content = re.sub(
                r"(\n *)*$", "\n", "\n".join(block.strings))
        elif (block.t == "FencedCode"):
            block.info = unescape(block.strings[0].strip())
            if (len(block.strings) == 1):
                block.string_content = ""
            else:
                block.string_content = "\n".join(block.strings[1:]) + "\n"
        elif (block.t == "List"):
            block.tight = True

            numitems = len(block.children)
            i = 0
            while (i < numitems):
                item = block.children[i]
                last_item = (i == numitems-1)
                if (self.endsWithBlankLine(item) and not last_item):
                    block.tight = False
                    break
                numsubitems = len(item.children)
                j = 0
                while (j < numsubitems):
                    subitem = item.children[j]
                    last_subitem = j == (numsubitems - 1)
                    if (self.endsWithBlankLine(subitem) and
                       not (last_item and last_subitem)):
                        block.tight = False
                        break
                    j += 1
                i += 1
        else:
            pass

        self.tip = block.parent

    def processInlines(self, block):
        """ Walk through a block & children recursively, parsing string content
        into inline content where appropriate."""
        if block.t in ["ATXHeader", "Paragraph", "SetextHeader"]:
            block.inline_content = self.inlineParser.parse(
                block.string_content.strip(), self.refmap)
            block.string_content = ""

        if block.children:
            for i in block.children:
                self.processInlines(i)

    def parse(self, my_input):
        """ The main parsing function.  Returns a parsed document AST."""
        self.doc = Node.makeNode("Document", 1, 1)
        self.tip = self.doc
        self.refmap = {}
        lines = re.split(reLineEnding, re.sub(r'\n$', '', my_input))
        length = len(lines)
        for i in range(length):
            self.incorporateLine(lines[i], i + 1)
        while (self.tip):
            self.finalize(self.tip, length)
        self.processInlines(self.doc)
        return self.doc

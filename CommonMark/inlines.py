from __future__ import absolute_import

import re
from CommonMark import common
from CommonMark.common import unescape
from CommonMark.node import Node


reLinkTitle = re.compile(
    '^(?:"(' + common.ESCAPED_CHAR + '|[^"\\x00])*"' +
    '|' +
    '\'(' + common.ESCAPED_CHAR + '|[^\'\\x00])*\'' +
    '|' +
    '\\((' + common.ESCAPED_CHAR + '|[^)\\x00])*\\))')
reLinkDestinationBraces = re.compile(
    '^(?:[<](?:[^<>\\n\\\\\\x00]' + '|' + common.ESCAPED_CHAR + '|' +
    '\\\\)*[>])')
reLinkDestination = re.compile(
    '^(?:' + common.REG_CHAR + '+|' + common.ESCAPED_CHAR + '|\\\\|' +
    common.IN_PARENS_NOSP + ')*')
reEscapable = re.compile('^' + common.ESCAPABLE)
reEntityHere = re.compile('^' + common.ENTITY, re.IGNORECASE)
reTicks = re.compile(r'`+')
reTicksHere = re.compile(r'^`+')
reEmailAutolink = re.compile(
    r"^<([a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>")
reAutolink = re.compile(
    r'^<(?:coap|doi|javascript|aaa|aaas|about|acap|cap|cid|crid|data|'
    r'dav|dict|dns|file|ftp|geo|go|gopher|h323|http|https|iax|icap|im|'
    r'imap|info|ipp|iris|iris.beep|iris.xpc|iris.xpcs|iris.lwz|ldap|'
    r'mailto|mid|msrp|msrps|mtqp|mupdate|news|nfs|ni|nih|nntp|'
    r'opaquelocktoken|pop|pres|rtsp|service|session|shttp|sieve|'
    r'sip|sips|sms|snmp|soap.beep|soap.beeps|tag|tel|telnet|tftp|'
    r'thismessage|tn3270|tip|tv|urn|vemmi|ws|wss|xcon|xcon-userid|'
    r'xmlrpc.beep|xmlrpc.beeps|xmpp|z39.50r|z39.50s|adiumxtra|afp|afs|'
    r'aim|apt|attachment|aw|beshare|bitcoin|bolo|callto|chrome|'
    r'chrome-extension|com-eventbrite-attendee|content|cvs|dlna-playsingle|'
    r'dlna-playcontainer|dtn|dvb|ed2k|facetime|feed|finger|fish|gg|git|'
    r'gizmoproject|gtalk|hcp|icon|ipn|irc|irc6|ircs|itms|jar|jms|keyparc|'
    r'lastfm|ldaps|magnet|maps|market|message|mms|ms-help|msnim|mumble|mvn|'
    r'notes|oid|palm|paparazzi|platform|proxy|psyc|query|res|resource|rmi|'
    r'rsync|rtmp|secondlife|sftp|sgn|skype|smb|soldat|spotify|ssh|steam|svn|'
    r'teamspeak|things|udp|unreal|ut2004|ventrilo|view-source|webcal|wtai|'
    r'wyciwyg|xfire|xri|ymsgr):[^<>\x00-\x20]*>',
    re.IGNORECASE)
reSpnl = re.compile(r'^ *(?:\n *)?')
reWhitespace = re.compile(r'\s+')
reFinalSpace = re.compile(r' *$')

# Matches a character with a special meaning in markdown,
# or a string of non-special characters.
reMain = re.compile(r'^(?:[\n`\[\]\\!<&*_]|[^\n`\[\]\\!<&*_]+)', re.MULTILINE)
# Matches a string of non-special characters.
# reMain = re.compile(r'^[^\n`\[\]\\!<&*_\'"]+', re.MULTILINE);


def normalizeReference(s):
    """ Normalize reference label: collapse internal whitespace to
    single space, remove leading/trailing whitespace, case fold."""
    return re.sub(r'\s+', ' ', s.strip()).upper()


class InlineParser:
    """INLINE PARSER

    These are methods of an InlineParser class, defined below.
    An InlineParser keeps track of a subject (a string to be
    parsed) and a position in that subject.
    """

    def __init__(self):
        self.subject = ""
        self.label_nest_level = 0
        self.pos = 0
        self.refmap = {}

    def match(self, regexString, reCompileFlags=0):
        """
        If regexString matches at current position in the subject, advance
        position in subject and return the match; otherwise return None.
        """
        match = re.search(
            regexString, self.subject[self.pos:], flags=reCompileFlags)
        if match is None:
            return None
        else:
            self.pos += match.end(0)
            return match.group()

    def peek(self):
        """ Returns the character at the current subject position, or None if
        there are no more characters."""
        try:
            return self.subject[self.pos]
        except IndexError:
            return None

    def spnl(self):
        """ Parse zero or more space characters, including at
        most one newline."""
        self.match(reSpnl)
        return 1

    # All of the parsers below try to match something at the current position
    # in the subject.  If they succeed in matching anything, they
    # push an inline element onto the 'inlines' list.  They return the
    # number of characters parsed (possibly 0).

    def parseBackticks(self, inlines):
        """ Attempt to parse backticks, adding either a backtick code span or a
        literal sequence of backticks to the 'inlines' list."""
        ticks = self.match(reTicksHere)
        if ticks is None:
            return 0
        afterOpenTicks = self.pos
        matched = self.match(reTicks)
        while matched is not None:
            if (matched == ticks):
                c = self.subject[afterOpenTicks:(self.pos - len(ticks))]
                c = c.strip()
                c = re.subn(reWhitespace, ' ', c)[0]
                inlines.append(Node(t='Code', c=c))
                return True
            matched = self.match(reTicks)
        # If we got here, we didn't match a closing backtick sequence.
        self.pos = afterOpenTicks
        inlines.append(Node(t='Str', c=ticks))
        return True

    def parseEscaped(self, inlines):
        """ Parse a backslash-escaped special character, adding either the
        escaped character, a hard line break (if the backslash is followed
        by a newline), or a literal backslash to the 'inlines' list."""
        subj = self.subject
        pos = self.pos
        if (subj[pos] == "\\"):
            if len(subj) > pos + 1 and (subj[pos + 1] == "\n"):
                inlines.append(Node(t="Hardbreak"))
                self.pos += 2
                return 2
            elif (reEscapable.search(subj[pos + 1:pos + 2])):
                inlines.append(Node(t="Str", c=subj[pos + 1:pos + 2]))
                self.pos += 2
                return 2
            else:
                self.pos += 1
                inlines.append(Node(t="Str", c="\\"))
                return 1
        else:
            return 0

    def parseAutoLink(self, inlines):
        """ Attempt to parse an autolink (URL or email in pointy brackets)."""
        m = self.match(reEmailAutolink)
        if m:
            # email
            dest = m[1:-1]
            inlines.append(
                Node(
                    t='Link',
                    title='',
                    label=[Node(t='Str', c=dest)],
                    destination='mailto:' + dest))
            return len(m)

        m = self.match(reAutolink)
        if m:
            # link
            dest = m[1:-1]
            inlines.append(
                Node(
                    t='Link',
                    title='',
                    label=[Node(t='Str', c=dest)],
                    destination=dest))
            return len(m)

        return 0

    def parseHtmlTag(self, inlines):
        """ Attempt to parse a raw HTML tag."""
        m = self.match(common.reHtmlTag)
        if (m):
            inlines.append(Node(t="Html", c=m))
            return len(m)
        else:
            return 0

    def scanDelims(self, c):
        """ Scan a sequence of characters == c, and return information about
        the number of delimiters and whether they are positioned such that
        they can open and/or close emphasis or strong emphasis.  A utility
        function for strong/emph parsing."""
        numdelims = 0
        char_before = char_after = None
        startpos = self.pos

        char_before = '\n' if self.pos == 0 else self.subject[self.pos - 1]

        while (self.peek() == c):
            numdelims += 1
            self.pos += 1

        a = self.peek()
        char_after = a if a else "\\n"

        can_open = (numdelims > 0) and (
            numdelims <= 3) and (not re.match("\s", char_after))
        can_close = (numdelims > 0) and (
            numdelims <= 3) and (not re.match("\s", char_before))

        if (c == "_"):
            can_open = can_open and (
                not re.match("[a-z0-9]", char_before, re.IGNORECASE))
            can_close = can_close and (
                not re.match("[a-z0-9]", char_after, re.IGNORECASE))
        self.pos = startpos
        return {
            "numdelims": numdelims,
            "can_open": can_open,
            "can_close": can_close
        }

    def parseEmphasis(self, inlines):
        """ Attempt to parse emphasis or strong emphasis in an efficient way,
        with no backtracking."""
        startpos = self.pos
        first_close = 0
        nxt = self.peek()
        if ((nxt == "*") or (nxt == "_")):
            c = nxt
        else:
            return 0

        res = self.scanDelims(c)
        numdelims = res["numdelims"]
        self.pos += numdelims
        if startpos > 0:
            inlines.append(
                Node(
                    t="Str",
                    c=self.subject[self.pos - numdelims:numdelims + startpos]))
        else:
            inlines.append(
                Node(t="Str", c=self.subject[self.pos - numdelims:numdelims]))
        delimpos = len(inlines) - 1

        if ((not res["can_open"]) or (numdelims == 0)):
            return 0

        first_close_delims = 0

        if (numdelims == 1):
            while (True):
                res = self.scanDelims(c)
                if (res["numdelims"] >= 1 and res["can_close"]):
                    self.pos += 1
                    inlines[delimpos].t = "Emph"
                    inlines[delimpos].c = inlines[delimpos + 1:]
                    if len(inlines) > 1:
                        for x in range(delimpos + 1, len(inlines)):
                            inlines.pop(len(inlines) - 1)
                    break
                else:
                    if (self.parseInline(inlines) == 0):
                        break
            return (self.pos - startpos)
        elif (numdelims == 2):
            while (True):
                res = self.scanDelims(c)
                if (res["numdelims"] >= 2 and res["can_close"]):
                    self.pos += 2
                    inlines[delimpos].t = "Strong"
                    inlines[delimpos].c = inlines[delimpos + 1:]
                    if len(inlines) > 1:
                        for x in range(delimpos + 1, len(inlines)):
                            inlines.pop(len(inlines) - 1)
                    break
                else:
                    if (self.parseInline(inlines) == 0):
                        break
            return (self.pos - startpos)
        elif (numdelims == 3):
            while (True):
                res = self.scanDelims(c)
                if (res["numdelims"] >= 1 and res["numdelims"] <= 3 and
                        res["can_close"] and
                        res["numdelims"] != first_close_delims):
                    if first_close_delims == 1 and numdelims > 2:
                        res["numdelims"] = 2
                    elif first_close_delims == 2:
                        res['numdelims'] = 1
                    elif res['numdelims'] == 3:
                        res['numdelims'] = 1
                    self.pos += res['numdelims']

                    if first_close > 0:
                        if first_close_delims == 1:
                            inlines[delimpos].t = "Strong"
                        else:
                            inlines[delimpos].t = "Emph"
                        temp = "Emph" if first_close_delims == 1 else "Strong"
                        inlines[delimpos].c = [Node(
                            t=temp,
                            c=inlines[delimpos + 1:first_close])] + \
                            inlines[first_close + 1:]  # error on 362?
                        if len(inlines) > 1:
                            for x in range(delimpos + 1, len(inlines)):
                                inlines.pop(len(inlines) - 1)
                        break
                    else:
                        inlines.append(
                            Node(
                                t="Str",
                                c=self.subject[
                                    self.pos - res["numdelims"]:self.pos]))
                        first_close = len(inlines) - 1
                        first_close_delims = res["numdelims"]
                else:
                    if self.parseInline(inlines) == 0:
                        break
            return (self.pos - startpos)
        else:
            return res

        return 0

    def parseLinkTitle(self):
        """ Attempt to parse link title (sans quotes), returning the string
        or None if no match."""
        title = self.match(reLinkTitle)
        if title:
            return unescape(title[1:len(title)-1])
        else:
            return None

    def parseLinkDestination(self):
        """ Attempt to parse link destination, returning the string or
        None if no match."""
        res = self.match(reLinkDestinationBraces)
        if res is not None:
            return unescape(res[1:len(res) - 1])
        else:
            res2 = self.match(reLinkDestination)
            if res2 is not None:
                return unescape(res2)
            else:
                return None

    def parseLinkLabel(self):
        """ Attempt to parse a link label, returning number of
        characters parsed."""
        if not self.peek() == "[":
            return 0
        startpos = self.pos
        nest_level = 0
        if self.label_nest_level > 0:
            self.label_nest_level -= 1
            return 0
        self.pos += 1
        c = self.peek()
        while ((not c == "]") or (nest_level > 0)) and c is not None:
            if c == "`":
                self.parseBackticks([])
            elif c == "<":
                self.parseAutoLink([]) or self.parseHtmlTag(
                    []) or self.parseString([])
            elif c == "[":
                nest_level += 1
                self.pos += 1
            elif c == "]":
                nest_level -= 1
                self.pos += 1
            elif c == "\\":
                self.parseEscaped([])
            else:
                self.parseString([])
            c = self.peek()
        if c == "]":
            self.label_nest_level = 0
            self.pos += 1
            return self.pos - startpos
        else:
            if c is None:
                self.label_nest_level = nest_level
            self.pos = startpos
            return 0

    def parseRawLabel(self, s):
        """ Parse raw link label, including surrounding [], and return
        inline contents.  (Note:  this is not a method of InlineParser.)"""
        return InlineParser().parse(s[1:-1])

    def parseLink(self, inlines):
        """ Attempt to parse a link.  If successful, add the link to
        inlines."""
        startpos = self.pos
        n = self.parseLinkLabel()

        if n == 0:
            return 0

        rawlabel = self.subject[startpos:n+startpos]

        if self.peek() == "(":
            self.pos += 1
            if self.spnl():
                dest = self.parseLinkDestination()
                if dest is not None and self.spnl():
                    if re.match(r"^\s", self.subject[self.pos - 1]):
                        title = self.parseLinkTitle()
                    else:
                        title = ""
                    if self.spnl() and self.match(r"^\)"):
                        inlines.append(
                            Node(
                                t="Link",
                                destination=dest,
                                title=title,
                                label=self.parseRawLabel(rawlabel)))
                        return self.pos - startpos
                    else:
                        self.pos = startpos
                        return 0
                else:
                    self.pos = startpos
                    return 0
            else:
                self.pos = startpos
                return 0

        savepos = self.pos
        self.spnl()
        beforelabel = self.pos
        n = self.parseLinkLabel()
        if n == 2:
            reflabel = rawlabel
        elif n > 0:
            reflabel = self.subject[beforelabel:beforelabel + n]
        else:
            self.pos = savepos
            reflabel = rawlabel
        if normalizeReference(reflabel) in self.refmap:
            link = self.refmap[normalizeReference(reflabel)]
        else:
            link = None
        if link:
            if link.get("title", None):
                title = link['title']
            else:
                title = ""
            if link.get("destination", None):
                destination = link['destination']
            else:
                destination = ""
            inlines.append(
                Node(
                    t="Link",
                    destination=destination,
                    title=title,
                    label=self.parseRawLabel(rawlabel)))
            return self.pos - startpos
        else:
            self.pos = startpos
            return 0
        self.pos = startpos
        return 0

    def parseEntity(self, inlines):
        """ Attempt to parse an entity, adding to inlines if successful."""
        m = self.match(reEntityHere)
        if m:
            inlines.append(Node(t="Entity", c=m))
            return len(m)
        else:
            return 0

    def parseString(self, inlines):
        """Parse a run of ordinary characters, or a single character with
        a special meaning in markdown, as a plain string, adding to inlines."""
        m = self.match(reMain)
        if m:
            inlines.append(Node(t="Str", c=m))
            return len(m)
        else:
            return 0

    def parseNewline(self, inlines):
        """ Parse a newline.  If it was preceded by two spaces, return a hard
        line break; otherwise a soft line break."""
        if (self.peek() == '\n'):
            self.pos += 1
            last = inlines and inlines[-1]
            if last and last.t == 'Str' and last.c[-1] == ' ':
                hardbreak = last.c[-2] == ' '
                last.c = re.sub(reFinalSpace, '', last.c)
                if hardbreak:
                    myblock = Node(t='Hardbreak')
                else:
                    myblock = Node(t='Softbreak')
                inlines.append(myblock)
            else:
                inlines.append(Node(t='Softbreak'))
            return True
        else:
            return False

    def parseImage(self, inlines):
        """ Attempt to parse an image.  If the opening '!' is not followed
        by a link, add a literal '!' to inlines."""
        if (self.match("^!")):
            n = self.parseLink(inlines)
            if (n == 0):
                inlines.append(Node(t="Str", c="!"))
                return 1
            elif (inlines[len(inlines) - 1] and
                    (inlines[len(inlines) - 1].t == "Link")):
                inlines[len(inlines) - 1].t = "Image"
                return n + 1
            else:
                raise Exception("Shouldn't happen")
        else:
            return 0

    def parseReference(self, s, refmap):
        """ Attempt to parse a link reference, modifying refmap."""
        self.subject = s
        self.pos = 0
        self.label_nest_level = 0

        startpos = self.pos

        matchChars = self.parseLinkLabel()
        if (matchChars == 0):
            return 0
        else:
            rawlabel = self.subject[:matchChars]

        test = self.peek()
        if (test == ":"):
            self.pos += 1
        else:
            self.pos = startpos
            return 0
        self.spnl()

        dest = self.parseLinkDestination()
        if (dest is None or len(dest) == 0):
            self.pos = startpos
            return 0

        beforetitle = self.pos
        self.spnl()
        title = self.parseLinkTitle()
        if (title is None):
            title = ""
            self.pos = beforetitle

        if (self.match(r"^ *(?:\n|$)") is None):
            self.pos = startpos
            return 0

        normlabel = normalizeReference(rawlabel)
        if (not refmap.get(normlabel, None)):
            refmap[normlabel] = {
                "destination": dest,
                "title": title
            }
        return (self.pos - startpos)

    def parseInline(self, inlines):
        """ Parse the next inline element in subject, advancing subject position
        and adding the result to 'inlines'."""
        c = self.peek()
        res = None
        if c == -1:
            return False
        if (c == '\n'):
            res = self.parseNewline(inlines)
        elif (c == '\\'):
            res = self.parseEscaped(inlines)
        elif (c == '`'):
            res = self.parseBackticks(inlines)
        elif ((c == '*') or (c == '_')):
            res = self.parseEmphasis(inlines)
        elif (c == '['):
            res = self.parseLink(inlines)
        elif (c == '!'):
            res = self.parseImage(inlines)
        elif (c == '<'):
            res = self.parseAutoLink(inlines) or self.parseHtmlTag(inlines)
        elif (c == '&'):
            res = self.parseEntity(inlines)

        return res or self.parseString(inlines)

    def parseInlines(self, s, refmap={}):
        """ Parse s as a list of inlines, using refmap to resolve
        references."""
        self.subject = s
        self.pos = 0
        self.refmap = refmap
        inlines = []
        while (self.parseInline(inlines)):
            pass
        return inlines

    def parse(self, s, refmap={}):
        """ Pass through to parseInlines."""
        return self.parseInlines(s, refmap)

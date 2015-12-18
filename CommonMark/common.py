from __future__ import absolute_import

import re
import sys

if sys.version_info >= (3, 0):
    if sys.version_info >= (3, 4):
        import html.parser
        HTMLunescape = html.parser.HTMLParser().unescape
    else:
        from .entitytrans import _unescape
        HTMLunescape = _unescape
else:
    from CommonMark import entitytrans
    HTMLunescape = entitytrans._unescape

# Some of the regexps used in inline parser :<

ENTITY = '&(?:#x[a-f0-9]{1,8}|#[0-9]{1,8}|[a-z][a-z0-9]{1,31});'
ESCAPABLE = '[!"#$%&\'()*+,./:;<=>?@[\\\\\\]^_`{|}~-]'
ESCAPED_CHAR = '\\\\' + ESCAPABLE
IN_DOUBLE_QUOTES = '"(' + ESCAPED_CHAR + '|[^"\\x00])*"'
IN_SINGLE_QUOTES = '\'(' + ESCAPED_CHAR + '|[^\'\\x00])*\''
IN_PARENS = '\\((' + ESCAPED_CHAR + '|[^)\\x00])*\\)'
REG_CHAR = '[^\\\\()\\x00-\\x20]'
IN_PARENS_NOSP = '\\((' + REG_CHAR + '|' + ESCAPED_CHAR + ')*\\)'
TAGNAME = '[A-Za-z][A-Za-z0-9]*'
BLOCKTAGNAME = '(?:article|header|aside|hgroup|iframe|blockquote|hr|body|' + \
               'li|map|button|object|canvas|ol|caption|output|col|p|' + \
               'colgroup|pre|dd|progress|div|section|dl|table|td|dt|' + \
               'tbody|embed|textarea|fieldset|tfoot|figcaption|th|' + \
               'figure|thead|footer|footer|tr|form|ul|h1|h2|h3|h4|' + \
               'h5|h6|video|script|style)'
ATTRIBUTENAME = '[a-zA-Z_:][a-zA-Z0-9:._-]*'
UNQUOTEDVALUE = "[^\"'=<>`\\x00-\\x20]+"
SINGLEQUOTEDVALUE = "'[^']*'"
DOUBLEQUOTEDVALUE = '"[^"]*"'
ATTRIBUTEVALUE = "(?:" + UNQUOTEDVALUE + "|" + \
    SINGLEQUOTEDVALUE + "|" + DOUBLEQUOTEDVALUE + ")"
ATTRIBUTEVALUESPEC = "(?:" + "\\s*=" + "\\s*" + ATTRIBUTEVALUE + ")"
ATTRIBUTE = "(?:" + "\\s+" + ATTRIBUTENAME + ATTRIBUTEVALUESPEC + "?)"
OPENTAG = "<" + TAGNAME + ATTRIBUTE + "*" + "\\s*/?>"
CLOSETAG = "</" + TAGNAME + "\\s*[>]"
OPENBLOCKTAG = "<" + BLOCKTAGNAME + ATTRIBUTE + "*" + "\\s*/?>"
CLOSEBLOCKTAG = "</" + BLOCKTAGNAME + "\\s*[>]"
# HTML comments are more complex than something between <!-- and -->
# http://www.w3.org/TR/html5/syntax.html#comments
HTMLCOMMENT = '<!---->|<!--(?:-?[^>-])(?:-?[^-])*-->'
PROCESSINGINSTRUCTION = "[<][?].*?[?][>]"
DECLARATION = "<![A-Z]+" + "\\s+[^>]*>"
CDATA = '<!\\[CDATA\\[[\\s\\S]*?\\]\\]>'
HTMLTAG = "(?:" + OPENTAG + "|" + CLOSETAG + "|" + HTMLCOMMENT + \
    "|" + PROCESSINGINSTRUCTION + "|" + DECLARATION + "|" + CDATA + ")"
reHtmlTag = re.compile('^' + HTMLTAG, re.IGNORECASE)
HTMLBLOCKOPEN = "<(?:" + BLOCKTAGNAME + \
    "[\\s/>]" + "|" + "/" + \
    BLOCKTAGNAME + "[\\s>]" + "|" + "[?!])"
reAllEscapedChar = '\\\\(' + ESCAPABLE + ')'

XMLSPECIAL = '[&<>"]'
reXmlSpecial = re.compile(XMLSPECIAL)
reXmlSpecialOrEntity = re.compile(
    '{}|{}'.format(ENTITY, XMLSPECIAL), re.IGNORECASE)
reBackslashOrAmp = re.compile(r'[\\&]')
reEntityOrEscapedChar = re.compile(
    '\\\\' + ESCAPABLE + '|' + ENTITY, re.IGNORECASE)


def unescape(s):
    """ Replace backslash escapes with literal characters."""
    return re.sub(reAllEscapedChar, r"\g<1>", s)


def unescape_char(s):
    if s[0] == '\\':
        return s[1]
    else:
        HTMLunescape(s)


def unescape_string(s):
    """Replace entities and backslash escapes with literal characters."""
    if re.match(reBackslashOrAmp, s):
        return re.sub(
            reEntityOrEscapedChar,
            lambda m: unescape_char(m))
    else:
        return s


def replace_unsafe_char(s):
    if s == '&':
        return '&amp;'
    elif s == '<':
        return '&lt;'
    elif s == '>':
        return '&gt;'
    elif s == '"':
        return '&quot;'
    else:
        return s


def escape_xml(s, preserve_entities):
    if s is None:
        return ''
    if re.match(reXmlSpecial, s):
        if preserve_entities:
            return re.sub(
                reXmlSpecialOrEntity,
                lambda m: replace_unsafe_char(m.group()),
                s)
        else:
            return re.sub(
                reXmlSpecial,
                lambda m: replace_unsafe_char(m.group()),
                s)
    else:
        return s

#!/usr/bin/env python
# 2014 - Bibek Kafle & Roland Shoemaker
# Based on @jgm's JavaScript stmd.js implementation of the CommonMark spec

import re

# all the regexps :<

ESCAPABLE = '[!"#$%&\'()*+,./:;<=>?@[\\\\\\]^_`{|}~-]'
ESCAPED_CHAR = '\\\\' + ESCAPABLE
IN_DOUBLE_QUOTES = '"(' + ESCAPED_CHAR + '|[^"\\x00])*"'
IN_SINGLE_QUOTES = '\'(' + ESCAPED_CHAR + '|[^\'\\x00])*\''
IN_PARENS = '\\((' + ESCAPED_CHAR + '|[^)\\x00])*\\)'
REG_CHAR = '[^\\\\()\\x00-\\x20]'
IN_PARENS_NOSP = '\\((' + REG_CHAR + '|' + ESCAPED_CHAR + ')*\\)'
TAGNAME = '[A-Za-z][A-Za-z0-9]*'
BLOCKTAGNAME = '(?:article|header|aside|hgroup|iframe|blockquote|hr|body|li|map|button|object|canvas|ol|caption|output|col|p|colgroup|pre|dd|progress|div|section|dl|table|td|dt|tbody|embed|textarea|fieldset|tfoot|figcaption|th|figure|thead|footer|footer|tr|form|ul|h1|h2|h3|h4|h5|h6|video|script|style)'
ATTRIBUTENAME = '[a-zA-Z_:][a-zA-Z0-9:._-]*'
UNQUOTEDVALUE = "[^\"'=<>`\\x00-\\x20]+"
SINGLEQUOTEDVALUE = "'[^']*'"
DOUBLEQUOTEDVALUE = '"[^"]*"'
ATTRIBUTEVALUE = "(?:" + UNQUOTEDVALUE + "|" + SINGLEQUOTEDVALUE + "|" + DOUBLEQUOTEDVALUE + ")"
ATTRIBUTEVALUESPEC = "(?:" + "\\s*=" + "\\s*" + ATTRIBUTEVALUE + ")"
ATTRIBUTE = "(?:" + "\\s+" + ATTRIBUTENAME + ATTRIBUTEVALUESPEC + "?)"
OPENTAG = "<" + TAGNAME + ATTRIBUTE + "*" + "\\s*/?>"
CLOSETAG = "</" + TAGNAME + "\\s*[>]"
OPENBLOCKTAG = "<" + BLOCKTAGNAME + ATTRIBUTE + "*" + "\\s*/?>"
CLOSEBLOCKTAG = "</" + BLOCKTAGNAME + "\\s*[>]"
HTMLCOMMENT = "<!--([^-]+|[-][^-]+)*-->"
PROCESSINGINSTRUCTION = "[<][?].*?[?][>]"
DECLARATION = "<![A-Z]+" + "\\s+[^>]*>"
CDATA = "<!\\[CDATA\\[([^\\]]+|\\][^\\]]|\\]\\][^>])*\\]\\]>"
HTMLTAG = "(?:" + OPENTAG + "|" + CLOSETAG + "|" + HTMLCOMMENT + "|" + PROCESSINGINSTRUCTION + "|" + DECLARATION + "|" + CDATA + ")"
HTMLBLOCKOPEN = "<(?:" + BLOCKTAGNAME + "[\\s/>]" + "|" + "/" + BLOCKTAGNAME + "[\\s>]" + "|" + "[?!])"

reHtmlTag = re.compile('^' + HTMLTAG, re.IGNORECASE)
reHtmlBlockOpen = re.compile('^' + HTMLBLOCKOPEN, re.IGNORECASE)
reLinkTitle = re.compile('^(?:"(' + ESCAPED_CHAR + '|[^"\\x00])*"' + '|' + '\'(' + ESCAPED_CHAR + '|[^\'\\x00])*\'' + '|' + '\\((' + ESCAPED_CHAR + '|[^)\\x00])*\\))')
reLinkDestinationBraces = re.compile('^(?:[<](?:[^<>\\n\\\\\\x00]' + '|' + ESCAPED_CHAR + '|' + '\\\\)*[>])')
reLinkDestination = re.compile('^(?:' + REG_CHAR + '+|' + ESCAPED_CHAR + '|' + IN_PARENS_NOSP + ')*')
reEscapable = re.compile(ESCAPABLE)
reAllEscapedChar = re.compile('\\\\(' + ESCAPABLE + ')')
reEscapedChar = re.compile('^\\\\(' + ESCAPABLE + ')')
reAllTab = re.compile("\t")
reHrule = re.compile("^(?:(?:\* *){3,}|(?:_ *){3,}|(?:- *){3,}) *$")
reMain = re.compile("^(?:[\n`\[\]\\!<&*_]|[^\n`\[\]\\!<&*_]+)/", re.MULTILINE)

# utility functions

def unescape(s):
  return reAllEscapedChar.sub('$1', s, 0)

def isBlank(s):
  return bool(re.compile("^\s*$").match(s))

def normalizeReference(s):
	return re.sub('\s+', ' ', s.strip())

def matchAt(pattern, s, offset):
	matched = re.match(pattern, s[offset:])
	if matched.group(0):
		return s.index(matched.group(0))
	else:
		return None

def detabLine(text):
	return re.sub(reAllTab, ' '*4, text)

def spnl(regex):
	regex.match(r"^ *(?:\n *)?")
	return 1

class Block(object):

	@staticmethod
	def makeBlock(tag,start_line, start_column):
		self.t =  tag
		self.isOpen =  true
		self.last_line_blank =  false
		self.start_line =  start_line
		self.start_column =  start_column
		self.end_line =  start_line
		self.children =  []
		self.parent =  null
		self.string_content =  ""
		self.strings =  []
		self.inline_content =  []

	def __init__(self, t="", c=""):
		self.t = t
		self.c = c


class InlineParser(object):

	def __init__(self):
		self.subject = ""
		self.label_nest_level = 0
		self.pos = 0
		self.refmap = {}

	def match(self, regexString, reCompileFlags):
		regex = re.compile(regexString, flags=reCompileFlags)
		match = regex.search(subject, pos)
		if match:
			self.pos = match.end()
		else:
			return None

	def peek(self):
		try:
			return self.subject[self.pos]
		except IndexError:
			return None

	def spnl(self):
		self.match(r"^ *(?:\n *)?")
		return 1

	def parseBackticks(self, inlines):
		startpos = self.pos
		ticks = self.match("^`+")
		if not ticks:
			return 0
		afterOpenTicks = this.pos
		foundCode = false
		match = None
		while ((not foundCode) and (match == self.match("`+", re.MULTILINE))):
			if (match == ticks):
				c = self.subject[afterOpenTicks:(self.pos-len(ticks))]
				c = re.sub(r"[ \n]+", ' ', c)
				c = c.strip()
				inlines.append(Block(t="Code", c=c))
				return (self.pos - startpos)
		inlines.append(Block(t="Str", c=ticks))
		self.pos = afterOpenTicks
		return (self.pos - startpos)
	

	def parseEscaped(self, inlines):
		subj = self.subject
		pos = self.pos
		if (subj[pos] == "\\"):
			if (subj[pos+1] == "\n"):
				inlines.append(Block(t="Hardbreak"))
				self.pos += 2
				return 2
			elif (reEscapable.search(subj[pos+1])):
				inlines.append(Block(t="Str", c=subj[pos+1]))
				self.pos += 2
				return 2
			else:
				self.pos +=1
				inlines.append(Block(t="Str", c="\\"))
				return 1
		else:
			return 0

	def parseAutoLink(self, inlines):
		pass

	def parseHtmlTag(self, inlines):
		m = self.match(reHtmlTag)
		if (m):
			inlines.append(Block(t="Html", c=m))
			return len(m)
		else:
			return 0

	def scanDelims(self):
		pass

	def parseEmphasis(self):
		pass

	def parseLinkTitle(self):
		pass

	def parseLinkDestination(self):
		pass

	def parseLinkLabel(self):
		pass

	def parseLink(self):
		pass

	def parseEntity(self):
		pass

	def parseString(self):
		pass

	def parseNewline(self):
		pass

	def parseImage(self):
		pass

	def parseReference(self):
		pass

	def parseInline(self, inlines):
		c = self.peek()
		res = None
		if (c == "\n"):
			res = self.parseNewline(inlines)
		elif (c == "\\"):
			res = self.parseEscaped(inlines)
		elif (c == "`"):
			res = self.parseBackticks(inlines)
		elif ((c == "*") or (c == "_")):
			res = self.parseEmphasis(inlines)
		elif (c == "["):
			res = self.parseImage(inlines)
		elif (c == "!"):
			res = self.parseImage(inlines)
		elif (c == "<"):
			res = self.parseAutoLink(inlines)
			if not res:
				res = self.parseHtmlTag(inlines)
		elif (c == "&"):
			res = self.parseEntity(inlines)
		else:
			pass
		if not res:
			res = self.parseString(inlines)
		return res

	def parseInlines(self, s, refmap = {}):
		self.subject = s
		self.pos = 0
		self.refmap = refmap
		inlines = []
		while (self.parseInline(inlines)):
			pass


	def parse(self, **kwargs):
		return self.parseInline(self, **kwargs)



class DocParser:

	def __init__(self, subject=None, pos=0):
		self.doc = Block.makeBlock("Document", 1, 1)
		self.subject = subject
		self.pos = pos
		self.tip = self.doc
		self.refmap = {}
		self.inlineParser = InlineParser()

	def breakOutOfLists(self):
		pass

	def addLine(self):
		pass

	def addLine(self):
		pass

	def addChild(self):
		pass

	def incorporateLine(self):
		pass

	def finalize(self):
		pass

	def processInlines(self):
		pass

	def parse(self):
		pass

class HTMLRenderer(object):
	blocksep = "\n"
	innersep = "\n"
	softbreak = "\n"
	escape_pairs = (("[&](?![#](x[a-f0-9]{1,8}|[0-9]{1,8});|[a-z][a-z0-9]{1,31};)", '&amp;'),
			("[<]", '&lt;'),
			("[>]", '&gt;'),
			(r'["]', '&quot;'))

	@staticmethod
	def inTags(tag, attribs, contents, selfclosing):
		result = "<" + tag
		if (len(attribs) > 0):
			i = 0
			attrib = attribs[i]
			while (len(attribs) > i):
				result += (" " + attrib[0] + '="' + atttrib[1] + '"')
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

	def escape(self, s, preserve_entities):
		if preserve_entities:
			e = this.escape_pairs
		else:
			e = this.escape_pairs[1:]
		for r in e:
			s = re.compile(r[0]).sub(s, r[1])

	def renderInline(self, inline):
		attrs = None
		if (inline.t == "Str"):
			return self.escape(inline.c)
		elif (inline.t == "Softbreak"):
			pass

	def renderInlines(self, inlines):
		result = ''
		for i in range(len(inlines)):
			result += self.renderInline(inlines[i])
		return result

	def renderBlock(self,  block, in_tight_list):
		tag = attr = info_words = None
		if (block.t == "Document"):
			whole_doc = self.renderBlocks(block.inline_content)
			if (whole_doc == ""):
				return ""
			else:
				return (whole_doc + "\n")
		elif (block.t == "Paragraph"):
			if (in_tight_list):
				return self.render(block.inline_content)
			else:
				return self.inTags('p', [], self.renderInlines(block.inline_content))
		elif (block.t == "BlockQuote"):
			filling = self.renderBlocks(block.children)
			if (filling == ""):
				a = self.innersep
			else:
				a = self.innersep + self.renderBlocks(block.children) + self.innersep
			return self.inTags('blockquote', [], a)
		elif (block.t == "ListItem"):
			return self.inTags("li", [], self.renderBlocks(block.children, in_tight_list).strip())
		elif (block.t == "List"):
			if (block.list_data.type == "Bullet"):
				tag = "ul"
			else:
				tag = "ol"
			pass
		elif ((block.t == "ATXHeader") or (block.t == "SetextHeader")):
			tag = "h" + block.level
			return self.inTags(tag, [], self.renderInlines(block.inline_content))
		elif (block.t == "IndentedCode"):
			pass
		elif (block.t == "FencedCode"):
			pass
		elif (block.t == "HtmlBlock"):
			pass
		elif (block.t == "ReferenceDef"):
			pass
		elif (block.t == "HorizontalRule"):
			return inTags("hr", [], "", True)
		else:
			print "Unknown block type" + block.t
			return ""

	def renderBlocks(self, blocks, in_tight_list):
		result = []
		for i in range(len(blocks)):
			if blocks[i].t != "ReferenceDef":
				result.append(self.renderBlock(blocks[i], in_tight_list))
		return self.blocksep.join(result)

	def render(self):
		pass



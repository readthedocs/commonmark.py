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

	def __init__(self, t="", c="", destination="", label=""):
		self.t = t
		self.c = c
		self.destination = destination
		self.label = label


class InlineParser(object):

	def __init__(self):
		self.subject = ""
		self.label_nest_level = 0
		self.pos = 0
		self.refmap = {}

	def match(self, regexString, reCompileFlags):
		#regex = re.compile(regexString, flags=reCompileFlags)
		match = regex.search(subject, pos)
		if match:
			self.pos = match.end()
			return match.group(0)
		else:
			return None

	def peek(self):
		try:
			return self.subject[self.pos]
		except IndexError:
			return None

	def spnl(self):
		self.match(re.compile("^ *(?:\n *)?"))
		return 1

	def parseBackticks(self, inlines):
		startpos = self.pos
		ticks = self.match(re.compile("^`+"))
		if not ticks:
			return 0
		afterOpenTicks = this.pos
		foundCode = false
		match = None
		while ((not foundCode) and (match == self.match(re.compile("`+", [re.MULTILINE])))):
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
		m = self.match(re.compile("^<([a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>"))
		m2 = self.match(re.compile("^<(?:coap|doi|javascript|aaa|aaas|about|acap|cap|cid|crid|data|dav|dict|dns|file|ftp|geo|go|gopher|h323|http|https|iax|icap|im|imap|info|ipp|iris|iris.beep|iris.xpc|iris.xpcs|iris.lwz|ldap|mailto|mid|msrp|msrps|mtqp|mupdate|news|nfs|ni|nih|nntp|opaquelocktoken|pop|pres|rtsp|service|session|shttp|sieve|sip|sips|sms|snmp|soap.beep|soap.beeps|tag|tel|telnet|tftp|thismessage|tn3270|tip|tv|urn|vemmi|ws|wss|xcon|xcon-userid|xmlrpc.beep|xmlrpc.beeps|xmpp|z39.50r|z39.50s|adiumxtra|afp|afs|aim|apt|attachment|aw|beshare|bitcoin|bolo|callto|chrome|chrome-extension|com-eventbrite-attendee|content|cvs|dlna-playsingle|dlna-playcontainer|dtn|dvb|ed2k|facetime|feed|finger|fish|gg|git|gizmoproject|gtalk|hcp|icon|ipn|irc|irc6|ircs|itms|jar|jms|keyparc|lastfm|ldaps|magnet|maps|market|message|mms|ms-help|msnim|mumble|mvn|notes|oid|palm|paparazzi|platform|proxy|psyc|query|res|resource|rmi|rsync|rtmp|secondlife|sftp|sgn|skype|smb|soldat|spotify|ssh|steam|svn|teamspeak|things|udp|unreal|ut2004|ventrilo|view-source|webcal|wtai|wyciwyg|xfire|xri|ymsgr):[^<>\x00-\x20]*>", [re.IGNORECASE])) 
		if m:
			# email
			dest = m[1:-1]
			inlines.append(Block(t="Link", label=Block(t="Str", c=dest, destination="mailto:"+dest)))
			return len(m)
		elif m2:
			# link
			dest2 = m2[1:-1]
			inlines.append(Block(t="Link", label=Block(t="Str", c=dest2, destination=dest2)))
			return len(m2)
		else:
			return 0

	def parseHtmlTag(self, inlines):
		m = self.match(reHtmlTag)
		if (m):
			inlines.append(Block(t="Html", c=m))
			return len(m)
		else:
			return 0

	def scanDelims(self, c):
		numdelims = 0
		first_close_delims = 0
		char_before, char_after = None
		startpos = self.pos

		char_before = "\n" if self.pos == 0 else self.subject[self.pos - 1]

		while (self.peek() == c):
			numdelims += 1
			self.pos += 1 

		a = self.peek()
		char_after = a if a else "\\n"

		can_open = (numdelims > 0) and (numdelims <=3) and (not re.search(r"\s", char_after))
		can_close = (numdelims > 0) and (numdelims <=3) and (not re.search(r"\s", char_before))

		if (c == "_"):
			can_open = can_open and (not re.search("[a-z0-9]", re.IGNORECASE), char_before)
			can_close = can_close and (not re.search("[a-z0-9]", re.IGNORECASE), char_after)
		self.pos = startpos
		return {
			"numdelims": numdelims,
			"can_open": can_open,
			"can_close": can_close
		}

	def parseEmphasis(self, inlines):
		startpos = self.pos
		first_close = 0
		nxt = self.peek()
		if ((nxt == "*") or (nxt == "_")):
			c = nxt
		else:
			return 0

		res = self.scanDelims(c)
		numdelims = res.numdelims
		self.pos += numdelims
		inlines.append(Block(t="Str", c=self.subject[self.pos - numdelims:numdelims]))
		delimpos = len(inlines) - 1

		if ((not res["can_open"]) or (numdelims == 0)):
			return 0

		first_close_delims = 0

		if (numdelims == 1):
			while (True):
				res = self.scanDelims(c)
				if (res.numdelims >= 1 and res.can_close):
					self.pos += 1
					inlines[delimpos].t = "Emph"
					inlines[delimpos].c = inlines[delimpos+1:]
					inlines = inlines[:delimpos+1]
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
					inlines[delimpos].t = "Strong";
					inlines[delimpos].c = inlines[delimpos+1:]
					inlines = inlines[:delimpos+1]
					break
				else:
					if (self.parseInline(inlines) == 0):
						break
			return (self.pos - startpos)
		elif (numdelims == 3):
			while (True):
				res = self.scanDelims(c)
				if (res["numdelims"] >= 1 and res["numdelims"] >= 3 and res["can_close"] and res["num_delims"] != first_close_delims):
					if first_close_delims == 1 and numdelims > 2:
						res["numdelims"] = 2
					elif first_close_delims == 2:
						res['numdelims'] = 1
					elif res['numdelims'] == 3:
						res['numdelims'] = 1
					self.pos += res['numdelims']

					if first_close > 0:
						inlines[delimpos].t = "Emph" if first_close_delims == 1 else "Strong"
						inlines[delimpos].c = [Block(t="Emph" if first_close_delims == 1 else "Strong", c=inlines[delimpos+1, first_close]), inlines[first_close+1:]]
						inlines = inlines[:delimpos+1]
						break
					else:
						inlines.append(Block(t="Str", c=self.subject[self.pos-res["numdelims"]:self.pos]))
						first_close = len(inlines)-1
						first_close_delims = res["numdelims"]
				else:
					if self.parseInline(inlines) == 0:
						break
			return (self.pos-startpos)
		else:
			return res
		




	def parseLinkTitle(self):
		title = self.match(reLinkTitle)
		if title:
			return unescape(title[1:-1])
		else:
			return None

	def parseLinkDestination(self):
		res = self.match(reLinkDestinationBraces)
		if res:
			return unescape(res[1:-1])
		else:
			res2 = self.match(reLinkDestination)
			if res2:
				return unescape(res2)
			else:
				return None

	def parseLinkLabel(self):
		pass

	def parseRawLabel(self, s):
		return InlineParser().parse(s[1:-1])

	def parseLink(self):
		pass

	def parseEntity(self, inlines):
		m = self.match(re.compile("^&(?:#x[a-f0-9]{1,8}|#[0-9]{1,8}|[a-z][a-z0-9]{1,31});", [re.IGNORECASE]))
		if m:
			inlines.append(Block(t="Entity", c=m))
			return len(m)
		else:
			return 0

	def parseString(self):
		m = self.match(reMain)
		if m:
			inlines.push(Block(t="Str", c=m))
			return len(m)
		else:
			return 0

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
		return inlines


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

	def addLine(self, ln, offset):
		s = ln[offset:]
		if self.tip.isOpen:
			# something?
			pass
		this.tip.strings.append(s)

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
			print("Unknown block type" + block.t)
			return ""

	def renderBlocks(self, blocks, in_tight_list):
		result = []
		for i in range(len(blocks)):
			if blocks[i].t != "ReferenceDef":
				result.append(self.renderBlock(blocks[i], in_tight_list))
		return self.blocksep.join(result)

	def render(self):
		pass



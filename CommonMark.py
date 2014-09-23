#!/usr/bin/env python
# 2014 - Bibek Kafle & Roland Shoemaker
# Port of @jgm's JavaScript stmd.js implementation of the CommonMark spec

# Basic usage:
#
# import CommonMark
# parser = CommonMark.DocParser()
# renderer = CommonMark.HtmlRenderer()
# print(renderer.render(parser.parse('Hello *world*')))


import re

#debug#
def dump(obj):
  for attr in dir(obj):
    print("obj.%s = %s" % (attr, getattr(obj, attr)))
 #debug#

# Some of the regexps used in inline parser :<

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
reAllEscapedChar = '\\\\(' + ESCAPABLE + ')'
reEscapedChar = re.compile('^\\\\(' + ESCAPABLE + ')')
reAllTab = re.compile("\t")
reHrule = re.compile(r"^(?:(?:\* *){3,}|(?:_ *){3,}|(?:- *){3,}) *$")

# Matches a character with a special meaning in markdown,
# or a string of non-special characters.
reMain = r"^(?:[\n`\[\]\\!<&*_]|[^\n`\[\]\\!<&*_]+)"

# Utility functions

def unescape(s):
	""" Replace backslash escapes with literal characters."""
	return re.sub(reAllEscapedChar, r"\g<1>", s)

def isBlank(s):
  """ Returns True if string contains only space characters."""
  return bool(re.compile("^\s*$").match(s))

def normalizeReference(s):
	""" Normalize reference label: collapse internal whitespace to
	 single space, remove leading/trailing whitespace, case fold."""
	return re.sub(r'\s+', ' ', s.strip()).upper()

def matchAt(pattern, s, offset):
	""" Attempt to match a regex in string s at offset offset.
	Return index of match or None."""
	matched = re.search(pattern, s[offset:])
	if matched:
		return offset+s[offset:].index(matched.group(0))
	else:
		return None

def detabLine(text):
	""" Convert tabs to spaces on each line using a 4-space tab stop."""
	if re.match('\t', text) and text.index('\t') == -1:
		return text
	else:
		def tabber(m):
			result = "    "[(m.end()-1-tabber.lastStop)%4:]
			tabber.lastStop = m.end()
			return result
		tabber.lastStop = 0
		text = re.sub("\t", tabber, text)
		return text


class Block(object):

	@staticmethod
	def makeBlock(tag,start_line, start_column):
		# self.t =  tag
		# self.isOpen =  true
		# self.last_line_blank =  false
		# self.start_line =  start_line
		# self.start_column =  start_column
		# self.end_line =  start_line
		# self.children =  []
		# self.parent =  None
		# self.string_content =  ""
		# self.strings =  []
		# self.inline_content =  []
		return Block(t=tag, start_line=start_line, start_column=start_column)

	def __init__(self, t="", c="", destination="", label=[], start_line="", start_column="", title=""):
		self.t = t
		self.c = c
		self.destination = destination
		self.label = label
		self.isOpen =  True
		self.last_line_blank =  False
		self.start_line =  start_line
		self.start_column =  start_column
		self.end_line =  start_line
		self.children =  []
		self.parent =  None
		self.string_content =  ""
		self.strings =  []
		self.inline_content =  []
		self.list_data = {}
		self.title = ""
		self.info = ""


class InlineParser(object):
	"""  INLINE PARSER

	 These are methods of an InlineParser class, defined below.
	 An InlineParser keeps track of a subject (a string to be
	 parsed) and a position in that subject.

	 If re matches at current position in the subject, advance
	 position in subject and return the match; otherwise return null."""

	def __init__(self):
		self.subject = ""
		self.label_nest_level = 0
		self.pos = 0
		self.refmap = {}

	def match(self, regexString, reCompileFlags=0):
		#regex = re.compile(regexString, flags=reCompileFlags)
		match = re.search(regexString, self.subject[self.pos:], flags=reCompileFlags)
		if match:
			self.pos += match.end()
			return match.group(0)
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
		ticks = self.match(r"^`+")
		if not ticks:
			return 0
		afterOpenTicks = self.pos
		foundCode = False
		match = self.match(r"`+", re.MULTILINE)
		while (not foundCode) and (match != None):
			if (match == ticks):
				c = self.subject[afterOpenTicks:(self.pos-len(ticks))]
				c = re.sub(r"[ \n]+", ' ', c)
				c = c.strip()
				inlines.append(Block(t="Code", c=c))
				return (self.pos - startpos)
			match = self.match(r"`+", re.MULTILINE)
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
			elif (reEscapable.search(subj[pos:pos+1])):
				inlines.append(Block(t="Str", c=subj[pos:pos+1]))
				self.pos += 2
				return 2
			else:
				self.pos +=1
				inlines.append(Block(t="Str", c="\\"))
				return 1
		else:
			return 0

	def parseAutoLink(self, inlines):
		m = self.match(r"^<([a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>")
		m2 = self.match(r"^<(?:coap|doi|javascript|aaa|aaas|about|acap|cap|cid|crid|data|dav|dict|dns|file|ftp|geo|go|gopher|h323|http|https|iax|icap|im|imap|info|ipp|iris|iris.beep|iris.xpc|iris.xpcs|iris.lwz|ldap|mailto|mid|msrp|msrps|mtqp|mupdate|news|nfs|ni|nih|nntp|opaquelocktoken|pop|pres|rtsp|service|session|shttp|sieve|sip|sips|sms|snmp|soap.beep|soap.beeps|tag|tel|telnet|tftp|thismessage|tn3270|tip|tv|urn|vemmi|ws|wss|xcon|xcon-userid|xmlrpc.beep|xmlrpc.beeps|xmpp|z39.50r|z39.50s|adiumxtra|afp|afs|aim|apt|attachment|aw|beshare|bitcoin|bolo|callto|chrome|chrome-extension|com-eventbrite-attendee|content|cvs|dlna-playsingle|dlna-playcontainer|dtn|dvb|ed2k|facetime|feed|finger|fish|gg|git|gizmoproject|gtalk|hcp|icon|ipn|irc|irc6|ircs|itms|jar|jms|keyparc|lastfm|ldaps|magnet|maps|market|message|mms|ms-help|msnim|mumble|mvn|notes|oid|palm|paparazzi|platform|proxy|psyc|query|res|resource|rmi|rsync|rtmp|secondlife|sftp|sgn|skype|smb|soldat|spotify|ssh|steam|svn|teamspeak|things|udp|unreal|ut2004|ventrilo|view-source|webcal|wtai|wyciwyg|xfire|xri|ymsgr):[^<>\x00-\x20]*>", re.IGNORECASE) 
		if m:
			# email
			dest = m[1:-1]
			inlines.append(Block(t="Link", label=[Block(t="Str", c=dest, destination="mailto:"+dest)]))
			return len(m)
		elif m2:
			# link
			dest2 = m2[1:-1]
			inlines.append(Block(t="Link", label=[Block(t="Str", c=dest2, destination=dest2)]))
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
		char_before = char_after = None
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
			can_open = can_open and (not re.search("[a-z0-9]", char_before, re.IGNORECASE))
			can_close = can_close and (not re.search("[a-z0-9]", char_after, re.IGNORECASE))
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
		numdelims = res["numdelims"]
		self.pos += numdelims
		inlines.append(Block(t="Str", c=self.subject[self.pos - numdelims:numdelims]))
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
					inlines[delimpos].t = "Strong"
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
				if (res["numdelims"] >= 1 and res["numdelims"] >= 3 and res["can_close"] and res["numdelims"] != first_close_delims):
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
		if not self.peek() == "[":
			return 0
		startpos = self.pos
		nest_level = 0
		if self.label_nest_level > 0:
			self.label_nest_level -= 1
			return 0
		self.pos += 1
		c = self.peek()
		while ((not c == "]") or (nest_level > 0)) and not c == None: # and (c = self.peek()):
			if c == "`":
				self.parseBackticks([])
				break
			elif c == "<":
				self.parseAutoLink([]) or self.parseHtmlTag([]) or self.parseString([])
				break
			elif c == "[":
				nest_level += 1
				self.pos += 1
				break
			elif c == "]":
				nest_level -= 1
				self.pos += 1
				break
			elif c == "\\":
				self.parseEscaped([])
				break
			else:
				self.parseString([])
			c = self.peek()
		if c == "]":
			self.label_nest_level = 0
			self.pos += 1
			return self.pos-startpos
		else:
			if c == None:
				self.label_nest_level = nest_level
			self.pos = startpos
			return 0

	def parseRawLabel(self, s):
		return InlineParser().parse(s[1:-1])

	def parseLink(self, inlines):
		startpos = self.pos
		n = self.parseLinkLabel()

		if n == 0:
			return 0

		afterlabel = self.pos
		rawlabel = self.subject[startpos:n]

		if self.peek() == "(":
			self.pos += 1
			if self.spnl():
				dest = self.parseLinkDestination()
				if dest and self.spnl():
					title = self.parseLinkTitle() or ''
					if re.match(r"^\s", self.subject[self.pos-1]) and (not title == None) or True:
						if (title or True) and self.spnl() and self.match(r"^\)"):
							inlines.append(Block(t="Link", destination=dest, title=title, label=self.parseRawLabel(rawlabel)))
							return self.pos-startpos
						else:
							self.pos = startpos
							return 0
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
		print(self.refmap)
		if n == 2:
			reflabel = rawlabel
		elif n > 0:
			reflabel = self.subject[beforelabel:beforelabel+n]
		else:
			self.pos = savepos
			reflabel = rawlabel
		if normalizeReference(reflabel) in self.refmap:
			link = self.refmap[normalizeReference(reflabel)]
		else: 
			link = None
		if link:
			print(link)
			print("i has link!")
			if link.get("title", None):
			 	title = link['title']
			else:
			 	title = ""
			if link.get("destination", None):
				destination = link['destination']
			else:
				destination = ""
			inlines.append(Block(t="Link", destination=destination, title=title, label=self.parseRawLabel(rawlabel)))
			return self.pos-startpos
		else:
			self.pos = startpos
			return 0
		self.pos = startpos
		return 0


	def parseEntity(self, inlines):
		m = self.match(r"^&(?:#x[a-f0-9]{1,8}|#[0-9]{1,8}|[a-z][a-z0-9]{1,31});", re.IGNORECASE)
		if m:
			inlines.append(Block(t="Entity", c=m))
			return len(m)
		else:
			return 0

	def parseString(self, inlines):
		m = self.match(reMain, re.MULTILINE)
		if m:
			inlines.append(Block(t="Str", c=m))
			return len(m)
		else:
			return 0

	def parseNewline(self, inlines):
		if (self.peek() == r'\n'):
			self.pos += 1
			last = inlines[len(inlines)-1]
			if last and last.t == "Str" and last.c[-2:] == "  ":
				last.c = re.sub(' *$', '', last.c)
				inlines.append(Block(t="Hardbreak"))
			else:
				if last and last.t == "Str" and last.c[-2] == " ":
					last.c = last.c[0:-1]
				inlines.append(Block(t="Softbreak"))
			return 1
		else:
			return 0

	def parseImage(self, inlines):
		if (self.match(r"^!")):
			n = self.parseLink(inlines)
			if (n == 0):
				inlines.append(Block(t="Str", c="!"))
				return 1
			elif (inlines[len(inlines) - 1] and
				(inlines[len(inlines)-1].t == "Link")):
				inlines[len(inlines)-1].t = "Image"
				return n+1
			else:
				raise Exception("Shouldn't happen")
		else:
			return 0

	def parseReference(self, s, refmap):
		self.subject = s
		self.pos = 0
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
		if (dest == None or len(dest) == 0):
			self.pos = startpos
			return 0

		beforetitle = self.pos
		self.spnl()
		title = self.parseLinkTitle()
		if (title == None):
			title = ""
			self.pos = beforetitle

		if (self.match(r"^ *(?:\n|$)") == None):
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
			res = self.parseLink(inlines)
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

	def parse(self, s, refmap = {}):
		return self.parseInlines(s, refmap)

class DocParser:

	def __init__(self, subject=None, pos=0):
		self.doc = Block.makeBlock("Document", 1, 1)
		self.subject = subject
		self.pos = pos
		self.tip = self.doc
		self.refmap = {}
		self.inlineParser = InlineParser()

	def dumpAST(self, obj, ind=0):
		#for attr in dir(obj):
		#	print("obj.%s = %s" % (attr, getattr(obj, attr)))
		indChar = ("\t"*ind)+"-> " if ind else ""
		print(indChar+"["+obj.t+"]")
		if not obj.title == "": print("\t"+indChar+"Title: "+obj.title)
		if not obj.c == "": print("\t"+indChar+"c: "+obj.c)
		if not obj.info == "": print("\t"+indChar+"Info: "+obj.info)
		if not obj.destination == "": print("\t"+indChar+"Destination: "+obj.destination)
		#if obj.label: print("\t"+indChar+"Label: "+", ".join(obj.label))
		if obj.isOpen: print("\t"+indChar+"Open: "+str(obj.isOpen))
		if obj.last_line_blank: print("\t"+indChar+"Last line blank: "+str(obj.last_line_blank))
		if obj.start_line: print("\t"+indChar+"Start line: "+str(obj.start_line))
		if obj.start_column: print("\t"+indChar+"Start Column: "+str(obj.start_column))
		if obj.end_line: print("\t"+indChar+"End line: "+str(obj.end_line))
		if not obj.string_content == "": print("\t"+indChar+"String content: "+obj.string_content)
		if not obj.info == "": print("\t"+indChar+"Info: "+obj.info)
		if len(obj.strings) > 0: print("\t"+indChar+"Strings: ["+", ".join(obj.strings)+"]")
		if obj.label:
			print("\t"+indChar+"Label:")
			for b in obj.label:
				self.dumpAST(b, ind+2)
		if hasattr(obj.list_data, "type"):
			print("\t"+indChar+"List Data: ")
			print("\t\t"+indChar+"[type] = "+obj.list_data['type'])
			if hasattr(obj.list_data, "bullet_char"): print("\t\t"+indChar+"[bullet_char] = "+obj.list_data['bullet_char'])
			if hasattr(obj.list_data, "start"): print("\t\t"+indChar+"[start] = "+obj.list_data['start'])
			if hasattr(obj.list_data, "delimiter"): print("\t\t"+indChar+"[delimiter] = "+obj.list_data['delimiter'])
			if hasattr(obj.list_data, "padding"): print("\t\t"+indChar+"[padding] = "+obj.list_data['padding'])
			if hasattr(obj.list_data, "marker_offset"): print("\t\t"+indChar+"[marker_offset] = "+obj.list_data['marker_offset'])
		if len(obj.inline_content) > 0:
			print("\t"+indChar+"Inline content:")
			for b in obj.inline_content:
				self.dumpAST(b, ind+2)
		if len(obj.children) > 0:
			print("\t"+indChar+"Children:")
			for b in obj.children:
				self.dumpAST(b, ind+2)

	def acceptsLines(self, block_type):
		return block_type == "Paragraph" or block_type == "IndentedCode" or block_type == "FencedCode"

	def endsWithBlankLine(self, block):
		if block.last_line_blank:
			return True
		if (block.t == "List" or block.t == "ListItem") and len(block.children) > 0:
			return self.endsWithBlankLine(block.children[len(block.children)-1])
		else:
			return False

	def breakOutOfLists(self, block, line_number):
		b = block
		last_list = None
		while True:
			if (b.t == "List"):
				last_list = b
			b = b.parent
			if not b:
				break

		if (last_list):
			while (not block == last_list):
				self.finalize(block, line_number)
				block = block.parent
			self.finalize(last_list, line_number)
			self.tip = last_list.parent	


	def addLine(self, ln, offset):
		s = ln[offset:]
		if not self.tip.isOpen:
			raise Exception("Attempted to add line (" + ln + ") to closed container." )
		self.tip.strings.append(s)

	def addChild(self, tag, line_number, offset):
		while not (self.tip.t == "Document" or self.tip.t == "BlockQuote" or self.tip.t == "ListItem" or (self.tip.t == "List" and tag == "ListItem")):
			self.finalize(self.tip, line_number)
		column_number = offset+1
		newBlock = Block.makeBlock(tag, line_number, offset)
		self.tip.children.append(newBlock)
		newBlock.parent = self.tip
		self.tip = newBlock
		return newBlock

	def listsMatch(self, list_data, item_data):
		if "type" in list_data and "type" in item_data and "delimiter" in list_data and "delimiter" in item_data and "bullet_char" in list_data and "bullet_char" in item_data:
			return list_data['type'] == item_data['type'] and list_data['delimiter'] == item_data['delimiter'] and list_data['bullet_char'] == item_data['bullet_char']

	def parseListMarker(self, ln, offset):
		rest = ln[offset:]
		data = {}
		blank_item = bool()
		if re.match(reHrule, rest):
			return None
		match = re.search(r"^[*+-]( +|$)", rest)
		match2 = re.search(r"^(\d+)([.)])( +|$)", rest)
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
				data['padding'] = len(match.group(0))-spaces_after_marker+1
			elif match2:
				data['padding'] = len(match2.group(0))-spaces_after_marker+1
		else:
			if match:
				data['padding'] = len(match.group(0))
			elif match2:
				data['padding'] = len(match2.group(0))
		return data


	def incorporateLine(self, ln, line_number):
		all_matched = True
		offset = 0
		CODE_INDENT = 4
		blank = bool()
		already_done = bool()

		container = self.doc
		oldtip = self.tip

		ln = detabLine(ln)

		#self.dumpAST(container)

		while len(container.children) > 0:
			last_child = container.children[len(container.children)-1]
			if not last_child.isOpen:
				break
			container = last_child

			match = matchAt(r"[^ ]", ln, offset)
			if match == None:
				first_nonspace = len(ln)
				blank = True
			else:
				first_nonspace = match
				blank = False
			indent = first_nonspace-offset
			if container.t == "BlockQuote":
				matched = bool()
				if len(ln) > first_nonspace and len(ln) > 0:
					matched = ln[first_nonspace] == ">"
				matched = indent <= 3 and matched
				if matched:
					offset = first_nonspace+1
					try:
						if ln[offset] == " ":
								offset += 1
					except IndexError:
						pass
				else:
					all_matched = False
				break
			elif container.t == "IndentedCode":
				if indent >= CODE_INDENT:
					offset += CODE_INDENT
				elif blank:
					offset = first_nonspace
				else:
					all_matched = False
				break
			elif container.t == "ATXHeader" or container.t == "SetextHeader" or container.t == "HorizontalRule":
				all_matched = False
				break
			elif container.t == "FencedCode":
				i = container.fence_offset
				while i > 0 and len(ln) > offset and ln[offset] == " ":
					offset += 1
					i -= 1
				break
			elif container.t == "HtmlBlock":
				if blank:
					all_matched = False
				break
			elif container.t == "Paragraph":
				if blank:
					container.last_line_blank = True
					all_matched = False
				break
			if not all_matched:
				container = container.parent
				break
		last_matched_container = container

		def closeUnmatchedBlocks(self, already_done, oldtip): # , mythis):
			while not already_done and not oldtip == last_matched_container:
				self.finalize(oldtip, line_number)
				oldtip = oldtip.parent
			return True, oldtip

		if blank and container.last_line_blank:
			self.breakOutOfLists(container, line_number)
		while not container.t == "FencedCode" and not container.t == "IndentedCode" and not container.t == "HtmlBlock" and not matchAt(r"^[ #`~*+_=<>0-9-]", ln, offset) == None:
			match = matchAt("[^ ]", ln, offset)
			if match == None:
				first_nonspace = len(ln)
				blank = True
			else:
				first_nonspace = match
				blank = False
			ATXmatch = re.search(r"^#{1,6}(?: +|$)", ln[first_nonspace:])
			FENmatch = re.search(r"^`{3,}(?!.*`)|^~{3,}(?!.*~)", ln[first_nonspace:])
			PARmatch = re.search(r"^(?:=+|-+) *$", ln[first_nonspace:])
			data = self.parseListMarker(ln, first_nonspace)
			
			indent = first_nonspace-offset
			if indent >= CODE_INDENT:
				if not self.tip.t == "Paragraph" and not blank:
					offset += CODE_INDENT
					already_done, oldtip = closeUnmatchedBlocks(self, already_done, oldtip)
					container = self.addChild('IndentedCode', line_number, offset)
				else:
					break
			elif len(ln) > first_nonspace and ln[first_nonspace] == ">":
				offset = first_nonspace+1
				try:
					if ln[offset] == " ":
						offset += 1
				except IndexError:
					pass
				already_done, oldtip = closeUnmatchedBlocks(self, already_done, oldtip)
				container = self.addChild("BlockQuote", line_number, offset)
			elif ATXmatch:
				offset = first_nonspace+len(ATXmatch.group(0))
				already_done, oldtip = closeUnmatchedBlocks(self, already_done, oldtip)
				container = self.addChild("ATXHeader", line_number, first_nonspace)
				container.level = len(ATXmatch.group(0).strip())
				container.strings = [re.sub(r"(?:(\\#) *#*| *#+) *$", "", ln[offset:])]
				break
			elif FENmatch:
				fence_length = len(FENmatch.group(0))
				already_done, oldtip = closeUnmatchedBlocks(self, already_done, oldtip)
				container = self.addChild("FencedCode", line_number, first_nonspace)
				container.fence_length = fence_length
				container.fence_char = FENmatch.group(0)[0]
				container.fence_offset = first_nonspace-offset
				offset = first_nonspace+fence_length
				break
			elif matchAt(reHtmlBlockOpen, ln, first_nonspace):
				already_done, oldtip = closeUnmatchedBlocks(self, already_done, oldtip)
				container = self.addChild('HtmlBlock', line_number, first_nonspace)
				break
			elif container.t == "Paragraph" and len(container.strings) == 1 and PARmatch:
				already_done, oldtip = closeUnmatchedBlocks(self, already_done, oldtip)
				container.t = "SetextHeader"
				container.level = 1 if PARmatch.group(0)[0] == '=' else 2
				offset = len(ln)
			elif matchAt(reHrule, ln, first_nonspace):
				already_done, oldtip = closeUnmatchedBlocks(self, already_done, oldtip)
				container = self.addChild("HorizontalRule", line_number, first_nonspace)
				offset = len(ln)-1
			elif data:
				already_done, oldtip = closeUnmatchedBlocks(self, already_done, oldtip)
				data['marker_offset'] = indent
				offset = first_nonspace+data['padding']
				if container.t == "List" or not self.listsMatch(container.list_data, data):
					container = self.addChild("List", line_number, first_nonspace)
					container.list_data = data
				container = self.addChild("ListItem", line_number, first_nonspace)
				container.list_data = data
			else:
				break
			if self.acceptsLines(container.t):
				break

		match = matchAt(r"[^ ]", ln, offset)
		if match == None:
			first_nonspace = len(ln)
			blank = True
		else:
			first_nonspace = match
			blank = False
		indent = first_nonspace-offset
		if not self.tip == last_matched_container and not blank and self.tip.t == "Paragraph" and len(self.tip.strings) > 0:
			self.last_line_blank = False
			self.addLine(ln, offset)
		else:
			already_done, oldtip = closeUnmatchedBlocks(self, already_done, oldtip)
			container.last_line_blank = blank and (not container.t == "BlockQuote" or container.t == "FencedCode" or (container.t == "ListItem" and len(container.children) == 0 and container.start_line == line_number))
			cont = container
			while cont.parent:
				cont.parent.last_line_blank = False
				cont = cont.parent
			if container.t == "IndentedCode" or container.t == "HtmlBlock":
				self.addLine(ln, offset)
			elif container.t == "FencedCode":
				match = bool()
				if len(ln) > 0:
					match = len(ln) > first_nonspace and ln[first_nonspace] == container.fence_char and re.match(r"^(?:`{3,}|~{3,})(?= *$)", ln[first_nonspace:])
				match = indent <= 3 and match
				FENmatch = re.search(r"^(?:`{3,}|~{3,})(?= *$)", ln[first_nonspace:])
				if match and len(FENmatch.group(0)) >= container.fence_length:
					self.finalize(container, line_number)
				else:
					self.addLine(ln, offset)
			elif container.t == "ATXHeader" or container.t == "SetextHeader" or container.t == "HorizontalRule":
				# nothing to do; we already added the contents.
				pass
			else:
				if self.acceptsLines(container.t):
					self.addLine(ln, first_nonspace)
				elif blank:
					pass
				elif not container == "HorizontalRule" and not container.t == "SetextHeader":
					container = self.addChild("Paragraph", line_number, first_nonspace)
					self.addLine(ln, first_nonspace)
				else:
					print("Line "+str(line_number)+" with container type "+container.t+" did not match any condition.")



	def finalize(self, block, line_number):
		if (not block.isOpen):
			return 0

		block.isOpen = False
		if (line_number > block.start_line):
			block.end_line = line_number - 1
		else:
			block.end_line = line_number

		if (block.t == "Paragraph"):
			block.string_content = re.sub(r"^ *", "", "\n".join(block.strings), re.MULTILINE)

			pos = self.inlineParser.parseReference(block.string_content, self.refmap)
			while (block.string_content[0] == "[" and pos):
				block.string_content = block.string_content[pos:]
				if (isBlank(block.string_content)):
					block.t = "ReferenceDef"
					break
				pos = self.inlineParser.parseReference(block.string_content, self.refmap)
		elif (block.t in ["ATXHeader", "SetextHeader", "HtmlBlock"]):
			block.string_content = "\n".join(block.strings)
		elif (block.t == "IndentedCode"):
			block.string_content = re.sub(r"(\n *)*$", "\n", "\n".join(block.strings))
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
				last_item = (i == numitems - 1)
				if (self.endsWithBlankLine(item) and not last_item):
					block.tight = False
					break
				numsubitems = len(item.children)
				j = 0
				while (j < numsubitems):
					subitem = item.children[j]
					last_subitem = j == (numsubitems - 1)
					if (self.endsWithBlankLine(subitem) and not (last_item and last_subitem)):
						block.tight = False
						break
					j += 1
				i += 1
		else:
			pass

		self.tip = block.parent #or self.tip #or self.top


	def processInlines(self, block):
		if block.t == "ATXHeader" or block.t == "Paragraph" or block.t == "SetextHeader":
			block.inline_content = self.inlineParser.parse(block.string_content.strip(), self.refmap)
			block.string_content = ""

		if block.children:
			for i in block.children:
				self.processInlines(i)

	def parse(self, input):
		self.doc = Block.makeBlock("Document", 1, 1)
		self.tip = self.doc
		self.refmap = {}
		lines = re.split(r"\r\n|\n|\r", re.sub(r"\n$", '', input))
		length = len(lines)
		for i in range(length):
			self.incorporateLine(lines[i], i+1)
		while (self.tip):
			self.finalize(self.tip, length-1)
		self.processInlines(self.doc)
		return self.doc

class HTMLRenderer(object):
	blocksep = "\n"
	innersep = "\n"
	softbreak = "\n"
	escape_pairs = (("[&](?![#](x[a-f0-9]{1,8}|[0-9]{1,8});|[a-z][a-z0-9]{1,31};)", '&amp;'),
			("[<]", '&lt;'),
			("[>]", '&gt;'),
			(r'["]', '&quot;'),
			(r"[&]",'&amp;'))

	@staticmethod
	def inTags(tag, attribs, contents, selfclosing=None):
		result = "<" + tag
		if (len(attribs) > 0):
			i = 0
			#attrib = attribs[i]
			while (len(attribs) > i) and (not attribs[i] == None):
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

	def escape(self, s, preserve_entities=None):
		if preserve_entities:
			e = self.escape_pairs[:-1]
		else:
			e = self.escape_pairs[1:]
		for r in e:
			s = re.sub(r[0], r[1], s)
		return s

	def renderInline(self, inline):
		attrs = None
		if (inline.t == "Str"):
			return self.escape(inline.c)
		elif (inline.t == "Softbreak"):
			return self.softbreak
		elif inline.t == "Hardbreak":
			return self.inTags('br', [], "", True)+"\n"
		elif inline.t == "Emph":
			return self.inTags('em', [], self.renderInlines(inline.c))
		elif inline.t == "Strong":
			return self.inTags("Strong", [], self.renderInlines(inline.c))
		elif inline.t == "Html":
			return inline.c
		elif inline.t == "Entity":
			return inline.c
		elif inline.t == "Link":
			attrs = [['href', self.escape(inline.destination, True)]]
			if inline.title:
				attrs.append(['title', self.escape(inline.title, True)])
			return self.inTags('a', attrs, self.renderInlines(inline.label))
		elif inline.t == "Image":
			attrs = [['src', self.escape(inline.destination, True)], ['alt', self.escape(self.renderInlines(inline.label))]]
			if inline.title:
				attrs.append(['title', self.escape(inline.title, True)])
			return self.inTags('img', attrs, "", True)
		elif inline.t == "Code":
			return self.inTags('code', [], self.escape(inline.c))
		else:
			print("Unknown inline type "+inline.t)
			return ""

	def renderInlines(self, inlines):
		result = ''
		for i in range(len(inlines)):
			result += self.renderInline(inlines[i])
		return result

	def renderBlock(self,  block, in_tight_list):
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
				return "\n"+self.inTags('p', [], self.renderInlines(block.inline_content))+"\n"
		elif (block.t == "BlockQuote"):
			filling = self.renderBlocks(block.children)
			if (filling == ""):
				a = self.innersep
			else:
				a = self.innersep + self.renderBlocks(block.children) + self.innersep
			return self.inTags('blockquote', [], a)
		elif (block.t == "ListItem"):
			return self.inTags("li", [], self.renderBlocks(block.children, in_tight_list).strip())+"\n"
		elif (block.t == "List"):
			if (block.list_data['type'] == "Bullet"):
				tag = "ul"
			else:
				tag = "ol"
			attr = [] if (not hasattr(block.list_data, 'start')) or block.list_data['start'] == 1 else [['start', str(block.list_data['start'])]]
			return "\n"+self.inTags(tag, attr, "\n"+self.innersep+self.renderBlocks(block.children, block.tight)+self.innersep)
		elif ((block.t == "ATXHeader") or (block.t == "SetextHeader")):
			tag = "h" + str(block.level)
			return "\n"+self.inTags(tag, [], self.renderInlines(block.inline_content))+"\n"
		elif (block.t == "IndentedCode"):
			return '\n'+HTMLRenderer.inTags('pre', [], HTMLRenderer.inTags('code', [], self.escape(block.string_content)+'\n'))+'\n'
		elif (block.t == "FencedCode"):
			info_words = []
			if block.info:
				info_words = block.info.split(" +")
			if ((len(info_words) == 0) or (len(info_words[0]) == 0)):
				attr = []
			else:
				arg = [['class','language-' + self.escape(info_words[0],True)]]
			attr = [] if len(info_words) == 0 else [["class", "language-"+self.escape(info_words[0], True)]]
			return self.inTags('pre', [], self.inTags('code', attr, self.escape(block.string_content)))
		elif (block.t == "HtmlBlock"):
			return block.string_content
		elif (block.t == "ReferenceDef"):
			return ""
		elif (block.t == "HorizontalRule"):
			return self.inTags("hr", [], "", True)
		else:
			print("Unknown block type" + block.t)
			return ""

	def renderBlocks(self, blocks, in_tight_list=None):
		result = []
		for i in range(len(blocks)):
			if not blocks[i].t == "ReferenceDef":
				result.append(self.renderBlock(blocks[i], in_tight_list))
		return self.blocksep.join(result)

	def render(self,  block, in_tight_list=None):
		return self.renderBlock(block, in_tight_list)


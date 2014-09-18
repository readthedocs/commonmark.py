structure
---------

bold == still todo

* unescape(s)
* isBlank(s)
* normalizeReference(s)
* matchAt(re, s, offset)
* detabLine(text)

* InlineParser()
  * match(re)
  * peek()
  * spnl()
  * parseBackticks(inlines)
  * parseEscaped(inlines)
  * parseAutolink(inlines)
  * parseHtmlTag(inlines)
  * scanDelims(c)
  * parseEmphasis(inlines)
  * parseLinkTitle()
  * parseLinkDestination()
  * parseLinkLabel()
  * parseRawLabel(s)
  * parseLink(inlines)
  * parseEntity(inlines)
  * parseString(inlines)
  * parseNewline(inlines)
  * parseImage(inlines)
  * parseReference(s, refmap)
  * parseInline(inlines)
  * parseInlines(s, refmap)
  * parse(s, refmap)


* DocParser()
  * makeBlock(tag, start_line, start_column)
  * **canContain(parent_type, child_type)**
  * **acceptsLines(block_type)**
  * **endsWithBlankLine(block)**
  * breakOutOfLists(block, line_number)
  * **addLine(ln, offset)**
  * addChild(tag, line_number, offset)
  * parseListMarker(ln, offset)
  * listsMatch(list_data, item_data)
  * incorporateLine(ln, line_number)
  * closeUnmatchedBlocks(mythis)
  * **finalize(block, line_number)**
  * processInlines(block)
  * parse(input)

* HtmlRenderer()
  * inTags(tag, attribs, contents, selfclosing)
  * **renderInline(inline)**
  * renderInlines(inlines)
  * **renderBlock(block, in_tight_list)**
  * escape(s, preserve_entities)

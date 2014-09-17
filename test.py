#!/usr/bin/env python

import re, time

import pprint

import CommonMark

#writer = CommonMark.HtmlRenderer
#reader = CommonMark.DocParser

f = open("spec.txt", "r")
data = f.read()
f.close()

passed = 0
failed = 0
examples = []
example_number = 0
current_section = ""

def showSpaces(s):
	t = str(s[:])
	t = re.sub(r"\t", "", t)
	t = re.sub(" ", "", t)
	return t

t = re.sub(r"\r\n?", r"\n", data)
tests = re.sub(r"^<!-- END TESTS -->(.|[\n])*", '', t, flags=re.M)
testMatch = re.findall(re.compile(r"^\.\n([\s\S]*?)^\.\n([\s\S]*?)^\.$|^#{1,6} *(.*)$", re.M), tests)

for match in testMatch:
	if match[2]:
		current_section = match[2]
	else:
		example_number += 1
		examples.append({'markdown': match[0], 'html': match[1], 'section': current_section, 'number': example_number})

current_section = ""

startTime = time.clock()

for example in examples:
	if not example['section'] == current_section:
		if not current_section == "":
			print("")
		current_section = example['section']
		print(current_section)

		actual = wrtier.renderBlock(reader.parse(example['markdown']))


endTime = time.clock()
runTime = endTime-StartTime
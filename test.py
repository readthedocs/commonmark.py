#!/usr/bin/env python

import re, time

import pprint

import CommonMark

renderer = CommonMark.HTMLRenderer()
parser = CommonMark.DocParser()

f = open("spec.txt", "r")
data = f.read()
f.close()

passed = 0
failed = 0
examples = []
example_number = 0
current_section = ""

def showSpaces(s):
	s = s.decode("utf-8")
	#t = str(s[:])
	t = s
	t = re.sub(u"\\t", u'\u2192', t)
	t = re.sub(u" ", u'\u2423', t)
	return t

t = re.sub(r"\r\n?", r"\n", data)
tests = re.sub(r"^<!-- END TESTS -->(.|[\n])*", '', t, flags=re.M)
testMatch = re.findall(re.compile(r"^\.\n([\s\S]*?)^\.\n([\s\S]*?)^\.$|^#{1,6} *(.*)$", re.M), tests)

for match in testMatch:
	if not match[2] == "":
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

		actual = renderer.render(parser.parse(re.sub(u'\u2192', r"\t", example['markdown'])))
		if actual == example['html']:
			passed += 1
			print("\ntick "+u'\u2713')
		else:
			failed += 1
			print("\ncross "+u'\u274C')
			print("=== markdown ===============\n"+showSpaces(example['markdown'])+"\n=== expected ===============\n"+showSpaces(example['html'])+"\n=== got ====================\n"+showSpaces(actual))

print(str(passed)+" tests passed, "+str(failed)+" failed")

endTime = time.clock()
runTime = endTime-startTime

print("runtime: "+str(runTime)+"s")

#!/usr/bin/env python

import re, time, codecs, argparse, sys
import pprint
import CommonMark

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def trace_calls(frame, event, arg):
	co = frame.f_code
	func_name = co.co_name
	if func_name == "write":
		return
	line_no = frame.f_lineno
	filename = co.co_filename
	if event == "call" and not re.match("__", func_name) and re.search("CommonMark", filename):
		print("Called "+func_name+" at "+str(line_no)+" in "+filename)
		return trace_calls

parser = argparse.ArgumentParser(description="script to run the CommonMark specification tests against the CommonMark.py parser")
parser.add_argument('-t', help="Single test to run or comma seperated list of tests (-t 10 or -t 10,11,12,13)")
parser.add_argument('-v', action="store_true", help="Verbose mode for debugging, print more stuff...")
parser.add_argument('-i', action="store_true", help="Interactive Markdown input mode")
parser.add_argument('-d', action="store_true", help="Debug stuff")
args = parser.parse_args()

if args.d:
	sys.settrace(trace_calls)

renderer = CommonMark.HTMLRenderer()
parser = CommonMark.DocParser()

f = codecs.open("spec.txt", encoding="utf-8")
datalist = []
for line in f:
	datalist.append(line)
data = "\n".join(datalist)

passed = 0
failed = 0
examples = []
example_number = 0
current_section = ""
tabChar = u'\u2192'
spaceChar = u'\u2423'


def showSpaces(s):
	s = s
	#t = str(s[:])
	t = s
	t = re.sub(u"\\t", tabChar, t)
	t = re.sub(u" ", spaceChar, t)
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

if args.i:
	while True:
		s = raw_input(colors.OKBLUE+"Markdown: "+colors.ENDC)
		ast = parser.parse(s)
		html = renderer.render(ast)
		print(colors.WARNING+"="*10+"AST====="+colors.ENDC)
		parser.dumpAST(ast)
		print(colors.WARNING+"="*10+"HTML===="+colors.ENDC)
		print(html)
	exit(0)

# some tests?
if args.t:
	tests = args.t.split(",")
	choice_examples = []
	for t in tests:
		if not t == "" and len(examples) > int(t):
			choice_examples.append(examples[int(t)-1])
	examples = choice_examples

# all tests

for i, example in enumerate(examples): # [0,examples[0]]
	if not example['section'] == "" and not current_section == example['section']:
		print(colors.HEADER+"\n"+example['section']+colors.ENDC)
		current_section = example['section']

	print("Test #"+str(i+1))
	ast = parser.parse(re.sub(tabChar, "\t", example['markdown']))
	actual = renderer.render(ast)
	if actual == example['html']:
		passed += 1
		print(colors.OKGREEN+"\ntick"+colors.ENDC)
		if args.v:
			print(colors.OKBLUE+"=== markdown ===============\n"+colors.ENDC+showSpaces(example['markdown'])+colors.OKBLUE+"\n=== expected ===============\n"+colors.ENDC+showSpaces(example['html'])+colors.OKBLUE+"\n=== got ====================\n"+colors.ENDC+showSpaces(actual))
	else:
		failed += 1
		print(colors.FAIL+"\ncross"+colors.ENDC)
		print(colors.WARNING+"=== markdown ===============\n"+colors.ENDC+showSpaces(example['markdown'])+colors.WARNING+"\n=== expected ===============\n"+colors.ENDC+showSpaces(example['html'])+colors.WARNING+"\n=== got ====================\n"+colors.ENDC+showSpaces(actual))

print(str(passed)+" tests passed, "+str(failed)+" failed")

endTime = time.clock()
runTime = endTime-startTime

print("runtime: "+str(runTime)+"s")

#!/usr/bin/env python
import argparse, json, CommonMark
parser = argparse.ArgumentParser(description="Process Markdown according to the CommonMark specification.")
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')
parser.add_argument('infile', nargs="?", type=argparse.FileType('r'), default=sys.stdin, help="Input Markdown file to parse, defaults to stdin")
parser.add_argument('-o', nargs="?", type=argparse.FileType('w'), default=sys.stdout, help="Output HTML/JSON file, defaults to stdout")
parser.add_argument('-a', action="store_true", help="Print formatted AST")
parser.add_argument('-aj', action="store_true", help="Output JSON AST")
args = parser.parse_args()
parser = CommonMark.DocParser()
f = args.infile
o = args.o
lines = []
for line in f:
    lines.append(line)
data = "".join(lines)
ast = parser.parse(data)
if not args.a and not args.aj:
    renderer = CommonMark.HTMLRenderer()
    o.write(renderer.render(ast))
    exit()
if args.a:
    # print ast
    CommonMark.dumpAST(ast)
    exit()

# output json
def ASTtoJSON(block):
    # this is destructive
    if block.parent:
        block.parent = None
    if block.children:
        for i, child in enumerate(block.children):
            block.children[i] = ASTtoJSON(child)
    return json.dumps(block, default=lambda o: o.__dict__, sort_keys=True) # indent=4)

#o.write(ast.to_JSON())
o.write(ASTtoJSON(ast))
exit()
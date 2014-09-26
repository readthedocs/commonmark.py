import sys
__all__ = ["HTMLRenderer", "DocParser", "dumpAST", "ASTtoJSON"]
if sys.version_info < (3,0):
	from CommonMark import HTMLRenderer
	from CommonMark import DocParser
	from CommonMark import dumpAST
	from CommonMark import ASTtoJSON
else:
	from CommonMark.CommonMark import HTMLRenderer
	from CommonMark.CommonMark import DocParser
	from CommonMark.CommonMark import dumpAST
	from CommonMark.CommonMark import ASTtoJSON

#!/usr/bin/env python

import re

import CommonMark

writer = CommonMark.HtmlRenderer()
reader = CommonMark.DocParser()

f = open("spec.txt", "r")
data = f.read()
f.close()

t = re.sub(r"\r\n?", r"\n", data)
tests = re.sub("^<!-- END TESTS -->(.|[\n])*", '', t)

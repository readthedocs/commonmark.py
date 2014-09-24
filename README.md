CommonMark-py
=============

Pure Python port of [jgm](https://github.com/jgm)'s [stmd.js](https://github.com/jgm/stmd/blob/master/js/stmd.js), a Markdown parser and renderer for the [CommonMark](http://commonmark.org) specification. Once both this project and the CommonMark specification are stable we will release the first `1.0` version and attempt to keep up to date with changes in `stmd.js`.

When the project is semi-stable we will move to a Python package format (PyPi) and include both a module and cli tool to render HTML (also some format to represent the intermediate AST, and maybe other things like PDF, etc in the future) files from Markdown files.

(**Note**: This is a work in progress! **368**/**443** tests currently passing)

[![Build Status](https://travis-ci.org/rolandshoemaker/CommonMark-py.svg?branch=master)](https://travis-ci.org/rolandshoemaker/CommonMark-py)

Usage
-----

In Python

	import CommonMark
	parser = CommonMark.DocParser()
	renderer = CommonMark.HTMLRenderer()
	print(renderer.render(parser.parse("Hello *World*")))

Using the CLI script

	rolands@kamaji:~$ CommonMark.py README.md -o README.html

Tests
-----

The tests script, `CommonMark-tests.py`, is pretty much a devtool. As well as running all the tests embeded in `spec.txt` it also allows you to run specific tests using the `-t` argument, provide information about passed tests with `-p`, percentage passed by category of test with `-s`, and enter markdown interactively with `-i` (In interactive mode end a block by inputing a line with just `end`, to quit do the same but with `quit`). `-d` can be used to print call tracing.

	rolands@kamaji:~/utils/CommonMark-py$ python CommonMark-tests.py -h
	usage: CommonMark-tests.py [-h] [-t T] [-p] [-f] [-i] [-d] [-np] [-s]

	script to run the CommonMark specification tests against the CommonMark.py
	parser

	optional arguments:
	  -h, --help  show this help message and exit
	  -t T        Single test to run or comma seperated list of tests (-t 10 or -t 10,11,12,13)
	  -p          Print passed test information
	  -f          Print failed tests (during -np...)
	  -i          Interactive Markdown input mode
	  -d          Debug, trace calls
	  -np         Only print section header, tick, or cross
	  -s          Print percent of tests passed by category

Authors
-------
* [Bibek Kafle](https://github.com/kafle)
* [Roland Shoemaker](https://github.com/rolandshoemaker)

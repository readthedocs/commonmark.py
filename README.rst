CommonMark-py
=============

Pure Python port of `jgm <https://github.com/jgm>`__'s
`commonmark.js <https://github.com/jgm/commonmark.js>`__, a
Markdown parser and renderer for the
`CommonMark <http://commonmark.org>`__ specification, using only native
modules. Once both this project and the CommonMark specification are
stable we will release the first ``1.0`` version and attempt to keep up
to date with changes in ``commonmark.js``.

We are currently at the same development stage (actually a bit ahead
because we have implemented HTML entity conversion and href URL
escaping) as ``commonmark.js``. Since Python versions pre-3.4 use outdated
(i.e. not HTML5 spec) entity conversion, I've converted the 3.4
implementation into a single file, ``entitytrans.py`` which so far seems
to work (all tests pass on 2.6, 2.7, 3.3, 3.4, and 3.5).

**Current version:** 0.6.4

|Build Status| |Doc Link|

Installation
------------

::

    rolands@kamaji:~$ pip install commonmark

Usage
-----

::

    import CommonMark

    CommonMark.commonmark('*hello!*')
    # '<p><em>hello!</em></p>\n'

    # Or, without the syntactic sugar:
    parser = CommonMark.Parser()
    renderer = CommonMark.HtmlRenderer()
    ast = parser.parse("Hello *World*")
    html = renderer.render(ast)
    json = CommonMark.ASTtoJSON(ast)
    CommonMark.dumpAST(ast) # pretty print generated AST structure
    print(html) # <p>Hello <em>World</em><p/>

    ----- or -----

    rolands@kamaji:~$ cmark.py README.md -o README.html
    rolands@kamaji:~$ cmark.py README.md -o README.json -aj # output AST as JSON
    rolands@kamaji:~$ cmark.py README.md -a # pretty print generated AST structure
    rolands@kamaji:~$ cmark.py -h
    usage: cmark.py [-h] [-o [O]] [-a] [-aj] [infile]

    Process Markdown according to the CommonMark specification.

    positional arguments:
      infile      Input Markdown file to parse, defaults to stdin

    optional arguments:
      -h, --help  show this help message and exit
      -o [O]      Output HTML/JSON file, defaults to stdout
      -a          Print formatted AST
      -aj         Output JSON AST
     

Contributing
------------

If you would like to offer suggestions/optimizations/bugfixes through
pull requests please do! Also if you find an error in the
parser/renderer that isn't caught by the current test suite please open
a new issue and I would also suggest you send the
`commonmark.js <https://github.com/jgm/commonmark.js>`__ project
a pull request adding your test to the existing test suite.

Tests
-----

To work on CommonMark-py, you will need to be able to run the test suite to
make sure your changes don't break anything. To run the tests, you can do
something like this:

::

   $ pyvenv venv
   $ ./venv/bin/python setup.py develop test

The tests script, ``run_spec_tests.py``, is pretty much a devtool. As
well as running all the tests embedded in ``spec.txt`` it also allows you
to run specific tests using the ``-t`` argument, provide information
about passed tests with ``-p``, percentage passed by category of test
with ``-s``, and enter markdown interactively with ``-i`` (In
interactive mode end a block by inputting a line with just ``end``, to
quit do the same but with ``quit``). ``-d`` can be used to print call
tracing.

::

    rolands@kamaji:~/utils/CommonMark-py$ python run_spec_tests.py -h
    usage: run_spec_tests.py [-h] [-t T] [-p] [-f] [-i] [-d] [-np] [-s]

    script to run the CommonMark specification tests against the CommonMark.py
    parser

    optional arguments:
      -h, --help  show this help message and exit
      -t T        Single test to run or comma separated list of tests (-t 10 or -t 10,11,12,13)
      -p          Print passed test information
      -f          Print failed tests (during -np...)
      -i          Interactive Markdown input mode
      -d          Debug, trace calls
      -np         Only print section header, tick, or cross
      -s          Print percent of tests passed by category

Authors
-------

-  `Bibek Kafle <https://github.com/kafle>`__
-  `Roland Shoemaker <https://github.com/rolandshoemaker>`__

.. |Build Status| image:: https://travis-ci.org/rtfd/CommonMark-py.svg?branch=master
   :target: https://travis-ci.org/rtfd/CommonMark-py
   
.. |Doc Link| image:: https://readthedocs.org/projects/commonmark-py/badge/?version=latest
   :target: https://commonmark-py.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

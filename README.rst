CommonMark-py
=============

CommonMark-py is a pure Python port of `jgm <https://github.com/jgm>`__'s
`commonmark.js <https://github.com/jgm/commonmark.js>`__, a
Markdown parser and renderer for the
`CommonMark <http://commonmark.org>`__ specification, using only native
modules. Once both this project and the CommonMark specification are
stable we will release the first ``1.0`` version and attempt to keep up
to date with changes in ``commonmark.js``.

CommonMark-py is tested against the CommonMark spec with Python versions
2.6, 2.7, 3.3, 3.4, 3.5, and 3.6.

**Current version:** 0.7.4

|Build Status| |Doc Link|

Installation
------------

::

    $ pip install commonmark

Usage
-----

::

    >>> import CommonMark
    >>> CommonMark.commonmark('*hello!*')
    '<p><em>hello!</em></p>\n'

Or, without the syntactic sugar:

.. code:: python

    import CommonMark
    parser = CommonMark.Parser()
    ast = parser.parse("Hello *World*")
    
    renderer = CommonMark.HtmlRenderer()
    html = renderer.render(ast)
    print(html) # <p>Hello <em>World</em><p/>
    
    # inspecting the abstract syntax tree
    json = CommonMark.dumpJSON(ast)
    CommonMark.dumpAST(ast) # pretty print generated AST structure
   
There is also a CLI:

::

    $ cmark README.md -o README.html
    $ cmark README.md -o README.json -aj # output AST as JSON
    $ cmark README.md -a # pretty print generated AST structure
    $ cmark -h
    usage: cmark [-h] [-o [O]] [-a] [-aj] [infile]

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

The tests script, ``CommonMark/tests/run_spec_tests.py``, is pretty much a devtool. As
well as running all the tests embedded in ``spec.txt`` it also allows you
to run specific tests using the ``-t`` argument, provide information
about passed tests with ``-p``, percentage passed by category of test
with ``-s``, and enter markdown interactively with ``-i`` (In
interactive mode end a block by inputting a line with just ``end``, to
quit do the same but with ``quit``). ``-d`` can be used to print call
tracing.

::

    $ ./venv/bin/python CommonMark/tests/run_spec_tests.py -h
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

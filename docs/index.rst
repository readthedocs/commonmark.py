.. CommonMark-py documentation master file, created by
   sphinx-quickstart on Mon Jan  4 18:11:52 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CommonMark-py's documentation!
=========================================

CommonMark-py is a pure Python port of `jgm
<https://github.com/jgm>`__'s `commonmark.js
<https://github.com/jgm/commonmark.js>`__, a Markdown parser and
renderer for the `CommonMark <http://commonmark.org>`__ specification,
using only native modules. Once both this project and the CommonMark
specification are stable we will release the first ``1.0`` version and
attempt to keep up to date with changes in ``commonmark.js``.

CommonMark-py is tested against the CommonMark spec with Python versions
2.7, 3.3, 3.4, and 3.5.

Usage
=====

.. code-block:: python

  import CommonMark

  CommonMark.commonmark('*hello!*')
  # '<p><em>hello!</em></p>\n'

  # Or, without the syntactic sugar:
  parser = CommonMark.Parser()
  renderer = CommonMark.HtmlRenderer()
  ast = parser.parse('Hello *World*')
  html = renderer.render(ast)
  json = CommonMark.ASTtoJSON(ast)
  CommonMark.dumpAST(ast)  # pretty print generated AST structure
  print(html)  # <p>Hello <em>World</em><p/>

.. toctree::
   :maxdepth: 2

   api


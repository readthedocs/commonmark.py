## 0.6.1 (2016-01-04)
- Fixed an IndexError exception that occurred when input string
  was empty.

## 0.6.0 (2016-01-04)
- CommonMark-py now complies to the 0.23 CommonMark spec
  http://spec.commonmark.org/0.23/
- The ExtensionBlock has been removed in this release, since
  the parser has been rewritten.
- Added a compatibility fix for Python 2.6, but this version
  of Python still isn't really supported.
- `HTMLRenderer` has been renamed to `HtmlRenderer`.
- `DocParser` has been renamed to `Parser`.

## 0.5.5 (2015-12-18)
- Random bug fixes
- Internal code structure changes
- Compatibility fixes for Python 3

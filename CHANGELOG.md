## x.y.z (unreleased)

## 0.9.1 (2019-10-04)
- commonmark.py now requires `future >= 0.14.0` on Python 2, for uniform `builtins` imports in Python 2/3
- Added CHANGELOG.md to the manifest file.

## 0.9.0 (2019-05-02)
- The CommonMark spec has been updated to 0.29. Completed by @iamahuman.

## 0.8.1 (2018-09-06)
- Removed `CommonMark` symlink. So, as of this version, you need to replace all instances of `CommonMark` with `commonmark` in your code.

## 0.8.0 (2018-09-03)
- Added the `Node.normalize()` method. (from @lez)
- Renamed package name to `commonmark` for PEP8 compliance. You can now do `import commonmark` as well as `import CommonMark`. Closes [#60](https://github.com/rtfd/commonmark.py/issues/60)
- Added testing on Python 3.7.

## 0.7.5 (2018-03-13)
- Fixed smart dashes bug in Python 3. (from @alvra)

## 0.7.4 (2017-08-05)
- The CommonMark spec has been updated to 0.28.

## 0.7.3 (2017-01-05)
- The CommonMark spec has been updated to 0.27.

## 0.7.2 (2016-08-10)
- Removed outdated files from distributed packages, reported by @hyperknot

## 0.7.1 (2016-07-20)
- Updated CommonMark spec to 0.26.
- Fixed JSON output invoked by `cmark -aj somefile.md`, reported by @rplCloud
- Fixed a bug with `dumpAST()` on ordered lists, from @rflynn

## 0.7.0 (2016-06-07)
- The `cmark.py` script is now just called `cmark`.
- Fixed a bug where the `cmark.py` script contained a bogus path, reported
  by @yuhui-lin.
- Fixed a bug where a TypeError could occur, reported by @civalin.

## 0.6.4 (2016-05-09)
- The CommonMark spec has been updated to 0.25.
- The HtmlRenderer has been refactored based on upstream changes in commonmark.js.
- Python 2 fixes from @eric-wieser
- Contributions from @funkybob and @hyperknot

## 0.6.3 (2016-01-19)
- commonmark.py now supports Python 2.6.
- The CommonMark spec has been updated to 0.24.

## 0.6.2 (2016-01-08)
- Fixed a UnicodeEncodeError when parsing unicode entities on
  Python 2. As a result, commonmark.py now relies on the "future"
  module in Python 2, as documented in setup.py. This can be found on
  pypi: https://pypi.python.org/pypi/future

## 0.6.1 (2016-01-05)
- Fixed an IndexError exception that occurred when input string
  was empty.

## 0.6.0 (2016-01-04)
- commonmark.py now complies to the 0.23 CommonMark spec
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

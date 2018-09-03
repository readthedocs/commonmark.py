from setuptools import setup, find_packages, Command


class Test(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import sys
        errno = subprocess.call([
            sys.executable, 'commonmark/tests/run_spec_tests.py'])
        raise SystemExit(errno)


tests_require = [
    'flake8==3.5.0',
    'hypothesis==3.55.3',
    # For python 2.6
    'hypothesislegacysupport',
]


setup(
    name="commonmark",
    packages=find_packages(exclude=['tests']),
    version="0.8.0",
    license="BSD-3-Clause",
    description="Python parser for the CommonMark Markdown spec",
    author="Bibek Kafle <bkafle662@gmail.com>, " +
    "Roland Shoemaker <rolandshoemaker@gmail.com>",
    author_email="rolandshoemaker@gmail.com",
    maintainer="Nikolas Nyby",
    maintainer_email="nikolas@gnu.org",
    url="https://github.com/rtfd/CommonMark-py",
    keywords=["markup", "markdown", "commonmark"],
    entry_points={
        'console_scripts': [
            'cmark = commonmark.cmark:main',
        ]
    },
    cmdclass={'test': Test},
    install_requires=[
        'future',
    ],
    tests_require=tests_require,
    extras_require={'test': tests_require},
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Other Environment",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Documentation",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities"])

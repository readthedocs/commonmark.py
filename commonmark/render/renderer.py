from __future__ import unicode_literals


class Renderer(object):
    def render(self, ast, strict=False):
        """Walks the AST and calls member methods for each Node type.

        @param ast {Node} The root of the abstract syntax tree.
        @param strict {bool} Whether unimplemented node types should raise
            an exception.
        """
        walker = ast.walker()

        self.buf = ''
        self.last_out = '\n'

        event = walker.nxt()
        while event is not None:
            type_ = event['node'].t
            if strict or hasattr(self, type_):
                getattr(self, type_)(event['node'], event['entering'])
            event = walker.nxt()

        return self.buf

    def lit(self, s):
        """Concatenate a literal string to the buffer.

        @param str {String} The string to concatenate.
        """
        self.buf += s
        self.last_out = s

    def cr(self):
        if self.last_out != '\n':
            self.lit('\n')

    def out(self, s):
        """Concatenate a string to the buffer possibly escaping the content.

        Concrete renderer implementations should override this method.

        @param str {String} The string to concatenate.
        """
        self.lit(s)

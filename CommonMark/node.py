class Node:

    @staticmethod
    def makeNode(tag, start_line, start_column):
        return Node(t=tag, start_line=start_line, start_column=start_column)

    def __init__(self, t="", c="", destination="", label="",
                 start_line="", start_column="", title=""):
        self.t = t
        self.c = c
        self.destination = destination
        self.label = label
        self.is_open = True
        self.last_line_blank = False
        self.start_line = start_line
        self.start_column = start_column
        self.end_line = start_line
        self.children = []
        self.parent = None
        self.string_content = ''
        self.literal = None
        self.strings = []
        self.inline_content = []
        self.list_data = {}
        self.title = title
        self.info = ''
        self.tight = bool()
        self.attributes = {}
        self.is_fenced = False
        self.fence_length = 0
        self.fence_char = None
        self.fence_offset = None

    def __repr__(self):
        return "Node {t} [{start}:{end}]".format(
            t=self.t,
            start=self.start_line,
            end=self.end_line,
            )

    def pretty(self):
        from pprint import pprint
        pprint(self.__dict__)

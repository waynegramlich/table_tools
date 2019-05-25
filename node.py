class Node(object):

        def __init__(self, name, path=None, parent=None):
            super(Node, self).__init__()

            self.name = name
            self.children = []
            self.parent = parent

            self.is_dir = False
            self.path = path
            self.is_traversed = False

            if parent is not None:
                parent.add_child(self)

        def add_child(self, child):
            self.children.append(child)
            child.parent = self

        def insert_child(self, position, child):
            if position < 0 or position > self.child_count():
                return False

            self.children.insert(position, child)
            child.parent = self

            return True

        def child(self, row):
            # Probably should be `return self.children[row]` with error checking:
            assert isinstance(row, int)
            node = self
            children = node.children
            assert 0 <= row < len(children)
            return children[row]

        def child_count(self):
            return len(self.children)

        def row(self):
            if self.parent is not None:
                return self.parent.children.index(self)
            return 0

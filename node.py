import os

class Node(object):

        def __init__(self, name, path, parent=None):
            # Verify argument types:
            assert isinstance(name, str)
            assert isinstance(path, str)
            assert isinstance(parent, Node) or parent is None

            # Initilize the parent type of *node* (i.e. *self*):
            node = self
            super(Node, self).__init__()

            is_dir = os.path.isdir(path)
            is_traversed = not is_dir or is_dir and len(list(os.listdir(path))) == 0

            # Load up *node* (i.e. *self*):
            node.children = []
            node.name = name
            node.is_dir = is_dir
            node.is_traversed = is_traversed
            node.parent = parent
            node.path = path

            # Force *node* to be in *parent*:
            if parent is not None:
                parent.add_child(node)

        def add_child(self, child):
            # Verify argument types:
            assert isinstance(child, Node)

            # Append *child* to the *node* (i.e. *self*) children list:
            node = self
            node.children.append(child)
            child.parent = node

        def insert_child(self, position, child):
            # Verify argument types:
            assert isinstance(position, int)
            assert isinstance(child, Node)
        
            node = self
            children = node.children
            inserted = 0 <= position <= len(children)
            if inserted:
                children.insert(position, child)
                child.parent = node
            return inserted

        def child(self, row):
            # Verify argument types:
            assert isinstance(row, int)

            node = self
            children = node.children
            result = children[row] if 0 <= row < len(children) else None
            return result

        def child_count(self):
            node = self
            return len(node.children)

        def row(self):
            node = self
            parent = node.parent
            result = 0 if parent is None else parent.children.index(node)
            return result

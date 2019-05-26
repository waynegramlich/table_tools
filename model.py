import os

from PySide2.QtCore import Qt, QModelIndex, QAbstractItemModel

from node import Node


class FileSystemTreeModel(QAbstractItemModel):

        FLAG_DEFAULT = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        def __init__(self, root_node, path):
            # Verify argument types:
            assert isinstance(root_node, Node) and root_node.is_dir
            assert isinstance(path, str)

            # Initialize the parent *QAbstraceItemModel*:
            super(FileSystemTreeModel, self).__init__()

            # Stuff *root* into *model* (i.e. *self*):
            model = self
            model.headers = {0: "Name", 1: "Type"}
            model.path = path
            model.root_node = root_node

            # Populate the top level of *root_node*:
            file_names = sorted(os.listdir(path))
            for file in file_names:
                file_path = os.path.join(path, file)
                node = Node(file, file_path, parent=root_node)
            root_node.is_traversed = True

        # takes a model index and returns the related Python node
        def getNode(self, index):
            # Verify argument types:
            assert isinstance(index, QModelIndex)

            model = self
            node = index.internalPointer() if index.isValid() else model.root_node
            assert isinstance(node, Node)
            return node

        # check if the note has data that has not been loaded yet
        def canFetchMore(self, index):
            # Verify argument types:
            assert isinstance(index, QModelIndex)

            model = self
            node = model.getNode(index)
            can_fetch_more = node.is_dir and not node.is_traversed
            return can_fetch_more

        # called if canFetchMore returns True, then dynamically inserts nodes required for
        # directory contents
        def fetchMore(self, index):
            # Verify argument types:
            assert isinstance(index, QModelIndex)

            model = self
            parent = model.getNode(index)

            nodes = []
            for file in sorted(os.listdir(parent.path)):
                file_path = os.path.join(parent.path, file)
                node = Node(file, file_path)
                nodes.append(node)

            model.insertNodes(0, nodes, index)
            parent.is_traversed = True

        # returns True for directory nodes so that Qt knows to check if there is more to load
        def hasChildren(self, index):
            # Verify argument types:
            assert isinstance(index, QModelIndex)

            model = self
            node = model.getNode(index)
            has_children = ((node.is_dir and not node.is_traversed) or
              super(FileSystemTreeModel, model).hasChildren(index))
            return has_children

        # Return 0 if there is data to fetch (handled implicitly by check length of child list)
        def rowCount(self, parent):
            # Verify argument types:
            assert isinstance(parent, QModelIndex)
            model = self
            node = model.getNode(parent)
            return node.child_count()

        def columnCount(self, parent):
            # Verify argument types:
            assert isinstance(parent, QModelIndex)
            return 2

        def flags(self, index):
            # Verify argument types:
            assert isinstance(index, QModelIndex)
            return FileSystemTreeModel.FLAG_DEFAULT

        def parent(self, index):
            # Verify argument types:
            assert isinstance(index, QModelIndex)

            model = self
            node = model.getNode(index)

            parent = node.parent
            index = (QModelIndex() if parent == model.root_node else
                     model.createIndex(parent.row(), 0, parent))
            assert isinstance(index, QModelIndex)
            return index

        def index(self, row, column, parent):
            # Verify argument types:
            assert isinstance(row, int)
            assert isinstance(column, int)
            assert isinstance(parent, QModelIndex)

            model = self
            node = model.getNode(parent)
            child = node.child(row)
            index = QModelIndex() if child is None else model.createIndex(row, column, child)
            assert isinstance(index, QModelIndex)
            return index

        def headerData(self, section, orientation, role):
            assert isinstance(section, int)
            assert isinstance(orientation, Qt.Orientation)
            assert isinstance(role, int)

            model = self
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return model.headers[section]
            return None

        def data(self, index, role):
            # Verify argument types:
            assert isinstance(index, QModelIndex)
            assert isinstance(role, int)

            column = index.column()
            value = None
            if index.isValid():
                node = index.internalPointer()
                if role == Qt.DisplayRole:
                    if column == 0:
                        value = node.name
                    elif column == 1:
                        value = "D" if node.is_dir else "T"
            assert isinstance(value, str) or value is None
            return value

        def insertNodes(self, position, nodes, parent=QModelIndex()):
            assert isinstance(position, int)
            assert isinstance(nodes, list)
            assert isinstance(parent, QModelIndex)
            for node in nodes:
                assert isinstance(node, Node)

            model = self
            node = model.getNode(parent)

            self.beginInsertRows(parent, position, position + len(nodes) - 1)

            for child in reversed(nodes):
                success = node.insert_child(position, child)

            self.endInsertRows()

            return True

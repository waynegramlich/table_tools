import os

from PyQt4.QtCore import Qt, QModelIndex, QAbstractItemModel

from node import Node


class FileSystemTreeModel(QAbstractItemModel):

        FLAG_DEFAULT = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        def __init__(self, root, path='/', parent=None):
            super(FileSystemTreeModel, self).__init__()

            self.root = root
            self.parent = parent
            self.path = path

            # generate root node children
            for file in os.listdir(path):
                file_path = os.path.join(path, file)

                node = Node(file, file_path, parent=self.root)
                if os.path.isdir(file_path):
                    node.is_dir = True

        # takes a model index and returns the related Python node
        def getNode(self, index):
            if index.isValid():
                return index.internalPointer()
            else:
                return self.root

        # check if the note has data that has not been loaded yet
        def canFetchMore(self, index):
            node = self.getNode(index)

            if node.is_dir and not node.is_traversed:
                return True

            return False

        # called if canFetchMore returns True, then dynamically inserts nodes required for
        # directory contents
        def fetchMore(self, index):
            parent = self.getNode(index)

            nodes = []
            for file in os.listdir(parent.path):
                file_path = os.path.join(parent.path, file)

                node = Node(file, file_path)
                if os.path.isdir(file_path):
                    node.is_dir = True

                nodes.append(node)

            self.insertNodes(0, nodes, index)
            parent.is_traversed = True

        # returns True for directory nodes so that Qt knows to check if there is more to load
        def hasChildren(self, index):
            node = self.getNode(index)

            if node.is_dir:
                return True

            return super(FileSystemTreeModel, self).hasChildren(index)

        # should return 0 if there is data to fetch (handled implicitly by check length of child list)
        def rowCount(self, parent):
            node = self.getNode(parent)
            return node.child_count()

        def columnCount(self, parent):
            return 1

        def flags(self, index):
            return FileSystemTreeModel.FLAG_DEFAULT

        def parent(self, index):
            node = self.getNode(index)

            parent = node.parent
            if parent == self.root:
                return QModelIndex()

            return self.createIndex(parent.row(), 0, parent)

        def index(self, row, column, parent):
            node = self.getNode(parent)

            child = node.child(row)

            if not child:
                return QModelIndex()

            return self.createIndex(row, column, child)

        def headerData(self, section, orientation, role):
            return self.root.name

        def data(self, index, role):
            if not index.isValid():
                return None

            node = index.internalPointer()

            if role == Qt.DisplayRole:
                return node.name

            else:
                return None

        def insertNodes(self, position, nodes, parent=QModelIndex()):
            node = self.getNode(parent)

            self.beginInsertRows(parent, position, position + len(nodes) - 1)

            for child in nodes:
                success = node.insert_child(position, child)

            self.endInsertRows()

            return True

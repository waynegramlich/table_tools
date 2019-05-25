import sys

from PyQt4.QtGui import QApplication, QTreeView

from node import Node
from model import FileSystemTreeModel


app = QApplication(sys.argv)

model = FileSystemTreeModel(Node('Filename'), path='/')


tree = QTreeView()
tree.setModel(model)

tree.show()

sys.exit(app.exec_())

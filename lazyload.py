#!/usr/bin/env python3

import sys

from PySide2.QtWidgets import QApplication, QTreeView

from node import Node
from model import FileSystemTreeModel


app = QApplication(sys.argv)

path="/home/wayne/public_html/projects/digikey_tables"
model = FileSystemTreeModel(Node("Root", path), path)

tree = QTreeView()
tree.setModel(model)

tree.show()

sys.exit(app.exec_())

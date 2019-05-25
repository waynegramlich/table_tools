#!/usr/bin/env python3

############################################################################
##
## Copyright (C) 2005-2005 Trolltech AS. All rights reserved.
##
## This file is part of the example classes of the Qt Toolkit.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http://www.trolltech.com/products/qt/opensource.html
##
## If you are unsure which license is appropriate for your use, please
## review the following information:
## http://www.trolltech.com/products/qt/licensing.html or contact the
## sales department at sales@trolltech.com.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################

from PySide2 import QtCore, QtGui, QtWidgets

class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, data, parent=None):
        super(TreeModel, self).__init__(parent)

        self.rootItem = TreeItem(("Title", "Summary"))
        self.setupModelData(data.split('\n'), self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, lines, parent):
        parents = [parent]
        indentations = [0]

        number = 0

        while number < len(lines):
            position = 0
            while position < len(lines[number]):
                if lines[number][position] != ' ':
                    break
                position += 1

            lineData = lines[number][position:].strip()

            if lineData:
                # Read the column data from the rest of the line.
                columnData = [s for s in lineData.split('\t') if s]

                if position > indentations[-1]:
                    # The last child of the current parent is now the new
                    # parent unless the current parent has no children.

                    if parents[-1].childCount() > 0:
                        parents.append(parents[-1].child(parents[-1].childCount() - 1))
                        indentations.append(position)

                else:
                    while position < indentations[-1] and len(parents) > 0:
                        parents.pop()
                        indentations.pop()

                # Append a new item to the current parent's list of children.
                parents[-1].appendChild(TreeItem(columnData, parents[-1]))

            number += 1


if __name__ == '__main__':

    import sys

    app = QtWidgets.QApplication(sys.argv)

    text = (
      "Getting Started\t\t\t\tHow to familiarize yourself with Qt Designer\n"
      "    Launching Designer\t\t\tRunning the Qt Designer application\n"
      "    The User Interface\t\t\tHow to interact with Qt Designer\n"
      "\n"
      "Designing a Component\t\t\tCreating a GUI for your application\n"
      "    Creating a Dialog\t\t\tHow to create a dialog\n"
      "    Composing the Dialog\t\tPutting widgets into the dialog example\n"
      "    Creating a Layout\t\t\tArranging widgets on a form\n"
      "    Signal and Slot Connections\t\tMaking widget communicate with each other\n"
      "\n"
      "Using a Component in Your Application\tGenerating code from forms\n"
      "    The Direct Approach\t\t\tUsing a form without any adjustments\n"
      "    The Single Inheritance Approach\tSubclassing a form's base class\n"
      "    The Multiple Inheritance Approach\tSubclassing the form itself\n"
      "    Automatic Connections\t\tConnecting widgets using a naming scheme\n"
      "        A Dialog Without Auto-Connect\tHow to connect widgets without a naming scheme\n"
      "        A Dialog With Auto-Connect\tUsing automatic connections\n"
      "\n"
      "Form Editing Mode\t\t\tHow to edit a form in Qt Designer\n"
      "    Managing Forms\t\t\tLoading and saving forms\n"
      "    Editing a Form\t\t\tBasic editing techniques\n"
      "    The Property Editor\t\t\tChanging widget properties\n"
      "    The Object Inspector\t\tExamining the hierarchy of objects on a form\n"
      "    Layouts\t\t\t\tObjects that arrange widgets on a form\n"
      "        Applying and Breaking Layouts\tManaging widgets in layouts\n"
      "        Horizontal and Vertical Layouts\tStandard row and column layouts\n"
      "        The Grid Layout\t\t\tArranging widgets in a matrix\n"
      "    Previewing Forms\t\t\tChecking that the design works\n"
      "\n"
      "Using Containers\t\t\tHow to group widgets together\n"
      "    General Features\t\t\tCommon container features\n"
      "    Frames\t\t\t\tQFrame\n"
      "    Group Boxes\t\t\t\tQGroupBox\n"
      "    Stacked Widgets\t\t\tQStackedWidget\n"
      "    Tab Widgets\t\t\t\tQTabWidget\n"
      "    Toolbox Widgets\t\t\tQToolBox\n"
      "\n"
      "Connection Editing Mode\t\t\tConnecting widgets together with signals and slots\n"
      "    Connecting Objects\t\t\tMaking connections in Qt Designer\n"
      "     Editing Connections\t\t\tChanging existing connections\n"
    )

    model = TreeModel(text)
    
    view = QtWidgets.QTreeView()
    view.setModel(model)
    view.setWindowTitle("Simple Tree Model")
    view.show()
    sys.exit(app.exec_())

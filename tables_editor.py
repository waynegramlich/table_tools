#!/usr/bin/env python3

#<-------------------------------------------- 100 characters ------------------------------------>|

# Coding standards:
# * In general, the coding guidexml_lines PEP 8 are used.
# * All code and docmenation xml_lines must be on xml_lines of 100 characters or less.
# * Comments:
#   * All code comments are written in [Markdown](https://en.wikipedia.org/wiki/Markdown).
#   * Code is organized into blocks are preceeded by comment that explains the code block.
#   * For methods, the class name is listed on a comment preceding the **def**.
# * Class/Function standards:
#   * Indentation levels are multiples of 4 spaces and continuation xml_lines have 2 more spaces.
#   * All classes are listed alphabetically.
#   * All methods within a class are listed alphabetically.
#   * No duck typing!  All function/method arguments are checked for compatibale types.
#   * Inside a method, *self* is usually replaced with more descriptive variable name.
#   * Generally, single character strings are in single quotes (`'`) and multi characters in double
#     quotes (`"`).  Empty strings are represented as `""`.  Strings with multiple double quotes
#     can be enclosed in single quotes.

# Import some libraries:
import re
import csv
import os
import sys
import xmlschema
import lxml.etree as etree
import copy  # Is this used any more?
from functools import partial
import PySide2
from PySide2.QtGui import (QStandardItem, QStandardItemModel)
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QCheckBox, QComboBox, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton,
                               QTableView, QTableWidget, QTableWidgetItem, QWidget)
from PySide2.QtCore import (Qt, QFile, QByteArray, QTimer)
#from PySide2.QtNetwork import (QUdpSocket, QHostAddress)

class ComboEdit:
    """ A *ComboEdit* object repesents the GUI controls for manuipulating a combo box widget.
    """

    # *WIDGET_CALLBACKS* is defined at the end of this class after all of the callback routines
    # are defined.
    WIDGET_CALLBACKS = dict()

    # ComboEdit::
    def __init__(self, name, tables_editor, items,
      new_item_function, current_item_set_function, comment_get_function, comment_set_function,
      tracing=None, **widgets):
        """ Initialize the *ComboEdit* object (i.e. *self*.)

        The arguments are:
        * *name*: A name for the *ComboEdit* object (i.e. *self*) for debugging.
        * *tables_editor*: The root *TablesEditor* object.
        * *items*: A list of item objects to manage.
        * *new_item_function*: A function that is called to create a new item.
        * *current_item_set_function*: A function that is called each time the current item is set.
        * *comment_get_function*: A function that is called to get the comment text.
        * *comment_set_function*: A function that is called to set the comment new comment text.
        * *tracing* (optional): The amount to indent when tracing otherwise *None* for no tracing:
        * *widgets*: A dictionary of widget names to widgets.  The following widget names
          are required:
          * "combo_box":    The *QComboBox* widget to be edited.
          * "comment_text": The *QComboPlainText* widget for comments.
          * "delete_button: The *QPushButton* widget that deletes the current entry.
          * "first_button": The *QPushButton* widget that moves to the first entry.
          * "last_button":  The *QPushButton* widget that moves to the last entry.
          * "line_edit":    The *QLineEdit* widget that supports new entry names and entry renames.
          * "next_button":  The *QPushButton* widget that moves to the next entry.
          * "new_button":   The *QPushButton* widget that create a new entry.
          * "previous_button": The *QPushButton* widget that moves tot the pervious entry.
          * "rename_button": The *QPushButton* widget that   rename_button_clicked,
        """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(items, list)
        assert callable(new_item_function)
        assert callable(current_item_set_function)
        assert callable(comment_get_function)
        assert callable(comment_set_function)
        assert isinstance(tracing, str) or tracing == None
        widget_callbacks = ComboEdit.WIDGET_CALLBACKS
        widget_names = list(widget_callbacks)
        for widget_name, widget in widgets.items():
            assert widget_name in widget_names, \
              "Invalid widget name '{0}'".format(widget_name)
            assert isinstance(widget, QWidget), \
              "'{0}' is not a QWidget {1}".format(widget_name, widget)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>ComboEdit.__init__(*, {1}, ...)".format(tracing, name))

        # Load some values into *combo_edit* (i.e. *self*):
        combo_edit = self
        combo_edit.comment_get_function = comment_get_function
        combo_edit.comment_set_function = comment_set_function
        combo_edit.comment_position = 0 
        combo_edit.current_item_set_function = current_item_set_function
        combo_edit.items = items
        combo_edit.name = name
        combo_edit.new_item_function = new_item_function
        combo_edit.tables_editor = tables_editor

        # Set the current item after *current_item_set_function* has been set.
        combo_edit.current_item_set(items[0] if len(items) > 0 else None, tracing=next_tracing)

        # Stuff each *widget* into *combo_edit* and connect the *widget* to the associated
        # callback routine from *widget_callbacks*:
        for widget_name, widget in widgets.items():
            # Store *widget* into *combo_edit* with an attribute name of *widget_name*:
            setattr(combo_edit, widget_name, widget)

            # Lookup the *callback* routine from *widget_callbacks*:
            callback = widget_callbacks[widget_name]

            # Using *widget* widget type, perform appropraite signal connection to *widget*:
            if isinstance(widget, QComboBox):
                # *widget* is a *QcomboBox* and generate a callback each time it changes:
                assert widget_name == "combo_box"
                widget.currentTextChanged.connect(   partial(callback, combo_edit))
            elif isinstance(widget, QLineEdit):
                # *widget* is a *QLineEdit* and generate a callback for each character changed:
                assert widget_name == "line_edit"
                widget.textEdited.connect(           partial(callback, combo_edit))
            elif isinstance(widget, QPushButton):
                # *widget* is a *QPushButton* and generat a callback for each click:
                widget.clicked.connect(              partial(callback, combo_edit))
            elif isinstance(widget, QPlainTextEdit):
                # *widget* is a *QPushButton* and generat a callback for each click:
                widget.textChanged.connect(          partial(callback, combo_edit))
                widget.cursorPositionChanged.connect(
                                                    partial(ComboEdit.position_changed, combo_edit))
            else:
                assert False, "'{0}' is not a valid widget".format(widget_name)

        # Wrap-up any requested *tracing*:
        if not tracing is None:
            print("{0}<=ComboEdit.__init__(*, {1}, ...)".format(tracing, name))

    # ComboEdit::
    def combo_box_changed(self, new_name):
        """ Callback method invoked when the *QComboBox* widget changes:

        The arguments are:
        * *new_name*: The *str* that specifies the new *QComboBox* widget value selected.
        """

        # Verify argument types:
        assert isinstance(new_name, str)

        # Only do something if we are not already *in_signal*:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>ComboEdit.combo_box_changed('{0}', '{1}')".
                  format(combo_edit.name, new_name))

                # Grab *attributes* (and compute *attributes_size*) from *combo_edit* (i.e. *self*):
                items = combo_edit.items
                for index, item in enumerate(items):
                    if item.name == new_name:
                        # We have found the new *current_item*:
                        print("  items[{0}] '{1}'".format(index, item.name))
                        combo_edit.current_item_set(item, tracing=next_tracing)
                        break

            # Update the the GUI:
            tables_editor.update(tracing=next_tracing)

            # Wrap up any signal tracing:
            if trace_signals:
                print("<=ComboEdit.combo_box_changed('{0}', '{1}')\n".
                  format(combo_edit.name, new_name))
            tables_editor.in_signal = False

    # ComboEdit::
    def comment_text_changed(self):
        # Do nothing if we are in a signal:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>ComboEdit.comment_text_changed()")

            # Extract *actual_text* from the *comment_plain_text* widget:
            main_window = tables_editor.main_window
            comment_text = combo_edit.comment_text
            actual_text = comment_text.toPlainText()
            cursor = comment_text.textCursor()
            position = cursor.position()

            # Store *actual_text* into *current_comment* associated with *current_parameter*:
            item = combo_edit.current_item_get()
            if not item is None:
                lines = actual_text.split('\n')
                combo_edit.comment_set_function(item, actual_text, position, tracing=next_tracing)

            # Force the GUI to be updated:
            tables_editor.update(tracing=next_tracing)

            # Wrap up any signal tracing:
            if trace_signals:
                print(" <=ComboEditor.comment_text_changed():{0}\n".format(cursor.position()))
            tables_editor.in_signal = False

    # ComboEdit::
    def current_item_get(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested tracing:
        combo_edit   = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>ComboEdit.current_item_get".format(tracing, combo_edit.name))

        current_item = combo_edit.current_item
        items        = combo_edit.items
        items_size   = len(items)

        # In general, we just want to return *current_item*. However, things can get
        # messed up by accident.  So we want to be darn sure that *current_item* is
        # either *None* or a valid item from *items*.

        # Step 1: Search for *current_item* in *tems:
        new_current_item = None
        for item in items:
            if item is current_item:
                # Found it:
                new_current_item = current_item

        # Just in case we did not find it, we attempt to grab the first item in *items* instead:
        if new_current_item is None and len(items) >= 1:
            new_current_item = items[0]

        # If the *current_item* has changed, we let the parent know:
        if not new_current_item is current_item:
            combo_edit.current_item_set(new_current_item, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}=>ComboEdit.current_item_get".format(tracing, combo_edit.name))
        return new_current_item

    # ComboEdit::
    def current_item_set(self, current_item, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        combo_edit = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>ComboEdit.current_item_set('{1}', *)".format(tracing, combo_edit.name))

        combo_edit.current_item = current_item
        combo_edit.current_item_set_function(current_item, tracing=next_tracing)

        # Wrap up any requested tracing:
        if not tracing is None:
            print("{0}<=ComboEdit.current_item_set('{1}', *)".format(tracing, combo_edit.name))

    # ComboEdit::
    def delete_button_clicked(self):
        # Perform any requested tracing from *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.delete_button_clicked('{0}')".format(combo_edit.name))

        # Find the matching *item* in *items* and delete it:
        tables_editor.in_signal = True
        items      = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                # Delete the *current_item* from *items*:
                del items[index]
                items_size = len(items)

                # Update *current_item* in *combo_edit*:
                if 0 <= index < items_size:
                    current_item = items[index]
                elif 0 <= index - 1 < items_size:
                    current_item = items[index - 1]
                else:
                    current_item = None
                combo_edit.current_item_set(current_item, tracing=next_tracing)
                break

        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested tracing;
        if trace_signals:
            print("<=ComboEdit.delete_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit::
    def first_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.first_button_clicked('{0}')".format(combo_edit.name))

        # If possible, select the *first_item*:
        tables_editor.in_signal = True
        items      = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            first_item = items[0]
            combo_edit.current_item_set(first_item, tracing=next_tracing)

        # Update the user interface:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.first_button_clicked('{0})\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit::
    def gui_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* of *combo_edit* (i.e. *self*):
        combo_edit = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>ComboEdit.gui_update('{1}')".format(tracing, combo_edit.name))

        # Grab the widgets from *combo_edit* (i.e. *self*):
        combo_box       = combo_edit.combo_box
        delete_button   = combo_edit.delete_button
        first_button    = combo_edit.first_button
        last_button     = combo_edit.last_button
        line_edit       = combo_edit.line_edit
        new_button      = combo_edit.new_button
        next_button     = combo_edit.next_button 
        previous_button = combo_edit.previous_button 
        rename_button   = combo_edit.rename_button 

        # If *current_item* *is_a_valid_item* we can enable most of the item widgets:
        current_item = combo_edit.current_item_get()
        items        = combo_edit.items
        items_size   = len(items)
        is_a_valid_item = not current_item is None
        combo_box.setEnabled(         is_a_valid_item)
        #if not tracing is None:
        #    print("{0}current_item='{1}'".
        #      format(tracing, "None" if current_item is None else current_item.name))


        # Changing the *combo_box* generates a bunch of spurious callbacks to
        # *ComboEdit.combo_box_changed()* callbacks.  The *combo_box_being_updated* attribute
        # is set to *True* in *combo_edit* so that these spurious callbacks can be ignored.
        combo_edit.combo_box_being_updated = True
        #print("combo_edit.combo_box_being_updated={0}".format(combo_edit.combo_box_being_updated))

        # Empty out *combo_box* and then refill it from *items*:
        combo_box.clear()
        current_item_index = -1
        for index, item in enumerate(items):
            combo_box.addItem(item.name)
            #if not tracing is None:
            #    print("{0}[{1}]: '{2}".format(tracing, index,
            #      "--" if item is None else item.name))
            if item is current_item:
                combo_box.setCurrentIndex(index)
                current_item_index = index
                if not tracing is None:
                    print("{0}match".format(tracing))
        assert not is_a_valid_item or current_item_index >= 0
        #print("current_item_index={0}".format(current_item_index))
        #print("items_size={0}".format(items_size))

        # Read the comment *current_text* out:
        if current_item is None:
            current_text = ""
            position = 0
        else:
            current_text, position = combo_edit.comment_get_function(
              current_item, tracing=next_tracing)

        # Make sure that *current_text* is being displayed by the *comment_text* widget:
        comment_text = combo_edit.comment_text
        previous_text = comment_text.toPlainText()
        if previous_text != current_text:
            comment_text.setPlainText(current_text)

        # Set the cursor to be at *position* in the *comment_text* widget.  *cursor* is a
        # copy of the cursor from *comment_text*.  *position* is loaded into *cursor* which
        # is then loaded back into *comment_text* to actually move the cursor position:
        cursor = comment_text.textCursor()
        cursor.setPosition(position)
        comment_text.setTextCursor(cursor)

        # Figure out if *_new_button_is_visible*:
        line_edit_text = line_edit.text()
        #print("line_edit_text='{0}'".format(line_edit_text))
        no_name_conflict = line_edit_text != ""
        for index, item in enumerate(items):
            item_name = item.name
            #print("[{0}] attribute_name='{1}'".format(index, item_name))
            if item.name == line_edit_text:
                no_name_conflict = False
                #print("new is not allowed")
        #print("no_name_conflict={0}".format(no_name_conflict))

        # If *current_attribute* *is_a_valid_attribute* we can enable most of the attribute widgets.
        # The first, next, previous, and last buttons depend upon the *current_attribute_index*:
        combo_box.setEnabled(         is_a_valid_item)
        delete_button.setEnabled(     is_a_valid_item)
        first_button.setEnabled(      is_a_valid_item
          and current_item_index > 0)
        last_button.setEnabled(       is_a_valid_item
          and current_item_index + 1 < items_size)
        new_button.setEnabled(        no_name_conflict)
        next_button.setEnabled(       is_a_valid_item
          and current_item_index + 1 < items_size)
        previous_button.setEnabled(   is_a_valid_item
          and current_item_index > 0)
        next_button.setEnabled(       is_a_valid_item
          and current_item_index + 1 < items_size)
        rename_button.setEnabled(     no_name_conflict)

        # Wrap up any requeted *tracing*:
        if not tracing is None:
            print("{0}<=ComboEdit.gui_update('{1}')".format(tracing, combo_edit.name))

    # ComboEdit::
    def items_replace(self, new_items):
        # Verify argument types:
        assert isinstance(new_items, list)

        # Stuff *new_items* into *combo_item*:
        combo_item = self
        combo_item.items = new_items

    # ComboEdit::
    def items_set(self, items, update_function, new_item_function, current_item_set_function):
        # Verify argument types:
        assert isinstance(items, list)
        assert callable(update_function)
        assert callable(new_item_function)
        assert callable(current_item_set_function)

        # Load values into *items*:
        combo_edit = self
        combo_item.current_item_set_function = current_item_set_function
        combo_item.items = new_items
        combo_item.new_item_function = new_item_function
        combo_item.update_function = update_function

        # Set the *current_item* last to be sure that the call back occurs:
        combo_item.current_item_set(new_items[0] if len(new_items) > 0 else None, "items_set")

    # ComboEdit::
    def last_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.last_button_clicked('{0}')".format(combo_edit.name))

        # If possible select the *last_item*:
        tables_editor.in_signal = True
        items      = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            last_item = items[-1]
            combo_edit.current_item_set(last_item, tracing=next_tracing)

        # Update the user interface:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.last_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit::
    def line_edit_changed(self, text):
        # Verify argument types:
        assert isinstance(text, str)

        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        if not tables_editor.in_signal:
            tables_editor.in_signal = True
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>ComboEditor.line_edit_changed('{0}')".format(text))
            next_tracing = " " if trace_signals else None
            combo_edit.gui_update(tracing=next_tracing)
            if trace_signals:
                print("<=ComboEditor.line_edit_changed('{0}')\n".format(text))
            tables_editor.in_signal = False

    # ComboEdit::
    def new_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.new_button_clicked('{0}')".format(combo_edit.name))
        
        # Grab some values from *combo_edit*:
        tables_editor.in_signal = True
        combo_box         = combo_edit.combo_box
        items             = combo_edit.items
        line_edit         = combo_edit.line_edit
        new_item_function = combo_edit.new_item_function
        print("items.id=0x{0:x}".format(id(items)))

        # Create a *new_item* and append it to *items*:
        new_item_name = line_edit.text()
        #print("new_item_name='{0}'".format(new_item_name))
        new_item = new_item_function(new_item_name, tracing=next_tracing)
        items.append(new_item)
        combo_edit.current_item_set(new_item, tracing=next_tracing)
        
        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("<=ComboEdit.new_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit::
    def next_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.next_button_clicked('{0}')".format(combo_edit.name))

        # ...
        tables_editor.in_signal = True
        items      = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                if index + 1 < items_size:
                    current_item = items[index + 1]
                break
        combo_edit.current_item_set(current_item, tracing=next_tracing)

        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.next_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit::
    def position_changed(self):
        # Do nothing if we already in a signal:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>ComboEdit.position_changed('{0}')".format(combo_edit.name))

            # Grab the *actual_text* and *position* from the *comment_text* widget and stuff
            # both into the comment field of *item*:
            item = combo_edit.current_item_get()
            comment_text = combo_edit.comment_text
            cursor = comment_text.textCursor()
            position = cursor.position()
            actual_text = comment_text.toPlainText()
            combo_edit.comment_set_function(item, actual_text, position, tracing=next_tracing)

            # Wrap up any signal tracing:
            if trace_signals:
                #print("position={0}".format(position))
                print("<=ComboEdit.position_changed('{0}')\n".format(combo_edit.name))
            tables_editor.in_signal = False

    # ComboEdit::
    def previous_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.previous_button_clicked('{0}')".format(combo_edit.name))

        # ...
        tables_editor.in_signal = True
        items      = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                if index > 0:
                    current_item = items[index - 1]
                break
        combo_edit.current_item_set(current_item, tracing=next_tracing)

        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.previous_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit::
    def rename_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.rename_button_clicked('{0}')".format(combo_edit.name))

        tables_editor.in_signal = True
        combo_edit = self
        line_edit = combo_edit.line_edit
        new_item_name = line_edit.text()

        current_item = combo_edit.current_item_get()
        if not current_item is None:
            current_item.name = new_item_name

        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if trace_signals:
            print("=>ComboEdit.rename_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit::
    # *WIDGET_CALLBACKS* is defined here **after** the actual callback routines are defined:
    WIDGET_CALLBACKS = {
      "combo_box":       combo_box_changed,
      "comment_text":    comment_text_changed,
      "delete_button":   delete_button_clicked,
      "first_button":    first_button_clicked,
      "last_button":     last_button_clicked,
      "line_edit":       line_edit_changed,
      "next_button":     next_button_clicked,    
      "new_button":      new_button_clicked,
      "previous_button": previous_button_clicked,
      "rename_button":   rename_button_clicked,
    }

class Comment:

    # Comment::
    def __init__(self, tag_name, **arguments_table):
        # Verify argument types:
        assert isinstance(tag_name, str) and tag_name in \
         ("EnumerationComment", "ParameterComment", "TableComment", "SearchComment")
        is_comment_tree = "comment_tree" in arguments_table
        if is_comment_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["comment_tree"], etree._Element)
        else:
            assert len(arguments_table) >= 2
            assert "language" in arguments_table and isinstance(arguments_table["language"], str)
            assert "lines" in arguments_table
            lines = arguments_table["lines"]
            for line in lines:
                assert isintance(line, str)

        if is_comment_tree:
            comment_tree = arguments_table["comment_tree"]
            assert comment_tree.tag == tag_name, \
              "tag_name='{0}' tree_tag='{1}'".format(tag_name, comment_tree.tag)
            attributes_table = comment_tree.attrib
            assert "language" in attributes_table
            language = attributes_table["language"]
            text = comment_tree.text.strip()
            lines = text.split('\n')
            for index, line in enumerate(lines):
                lines[index] = line.strip().replace("<", "&lt;").replace(">", "&gt;")
        else:
            language = arguments_table["language"]
            lines = arguments_table["lines"]

        # Load up *table_comment* (i.e. *self*):
        comment = self
        comment.position = 0
        comment.language = language
        comment.lines = lines
        #print("Comment(): comment.lines=", tag_name, lines)

    # Coment::
    def __eq__(self, comment2):
        # Verify argument types:
        assert isinstance(comment2, Comment)

        # Compare each field in *comment1* (i.e. *self*) with the corresponding field in *comment2*:
        comment1 = self
        language_equal = (comment1.language == comment2.language)
        lines_equal    = (comment1.lines    == comment2.lines)
        all_equal      = (language_equal and lines_equal)
        #print("language_equal={0}".format(language_equal))
        #print("lines_equal={0}".format(lines_equal))
        return all_equal

class Enumeration:

    # Enumeration::
    def __init__(self, **arguments_table): 
        is_enumeration_tree = "enumeration_tree" in arguments_table
        if is_enumeration_tree:
            assert isinstance(arguments_table["enumeration_tree"], etree._Element)
        else:
            assert len(arguments_table) == 2
            assert "name" in arguments_table
            assert "comments" in arguments_table
            comments = arguments_table["comments"]
            for comment in comments:
                assert isinstance(comment, EnumerationComment)

        if is_enumeration_tree:
            enumeration_tree = arguments_table["enumeration_tree"]
            assert enumeration_tree.tag == "Enumeration"
            attributes_table = enumeration_tree.attrib
            assert len(attributes_table) == 1
            assert "name" in attributes_table
            name = attributes_table["name"]
            comments_tree = list(enumeration_tree)
            comments = list()
            for comment_tree in comments_tree:
                comment = EnumerationComment(comment_tree=comment_tree)
                comments.append(comment)
            assert len(comments) >= 1
        else:
            name = atributes_table["name"]
            comments = atributes_table["comments"]

        # Load value into *enumeration* (i.e. *self*):
        enumeration = self
        enumeration.name = name
        enumeration.comments = comments

    # Enumeration::
    def __eq__(self, enumeration2):
        # Verify argument types:
        assert isinstance(enumeration2, Enumeration)
        
        enumeration1 = self
        name_equal     = (enumeration1.name     == enumeration2.name)
        comments_equal = (enumeration1.comments == enumeration2.comments)
        return name_equal and comments_equal

    # Enumeration::
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Append an `<Enumeration>` element to *xml_lines*:
        enumeration = self
        xml_lines.append('{0}<Enumeration name="{1}">'.format(indent, enumeration.name))
        for comment in enumeration.comments:
            comment.xml_lines_append(xml_lines, indent + "  ")
        xml_lines.append('{0}</Enumeration>'.format(indent))

class EnumerationComment(Comment):

    # EnumerationComment::
    def __init__(self, **arguments_table):
        #print("=>EnumerationComment.__init__()")
        enumeration_comment = self
        super().__init__("EnumerationComment", **arguments_table)
        assert isinstance(enumeration_comment.language, str)
        assert isinstance(enumeration_comment.lines, list)

    # EnumerationComment::
    def __equ__(self, enumeration_comment2):
        assert isinstance(enumeration_comment2, EnumerationComment)
        return super.__eq__(enumeration_comment2)

    # EnumerationComment::
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Append and `<EnumerationComment>` an element to *xml_lines*:
        enumeration_comment = self
        xml_lines.append('{0}<EnumerationComment language="{1}">'.
          format(indent, enumeration_comment.language))
        for line in enumeration_comment.lines:
            xml_lines.append('{0}  {1}'.format(indent, line))
        xml_lines.append('{0}</EnumerationComment>'.format(indent))

class Filter:

    # Filter::
    def __init__(self, **arguments_table):
        # Verify argument types:
        is_filter_tree = "tree" in arguments_table
        arguments_table_size = len(arguments_table)
        if is_filter_tree:
            assert arguments_table_size == 2
            assert "table" in arguments_table
        else:
            assert arguments_table_size == 3
            assert "parameter" in arguments_table
            assert "table" in arguments_table
            assert "use" in arguments_table

        # Dispatch on *is_filter_tree*:
        if is_filter_tree:
            # Grab *tree* and *table* out of *arguments_table*:
            tree = arguments_table["tree"]
            assert isinstance(tree, etree._Element)
            table = arguments_table["table"]
            assert isinstance(table, Table)

            # Grab the *parameter_name* and *use* from *filter_tree*:
            attributes_table = tree.attrib
            assert len(attributes_table) == 2

            # Extrace *use* from *attributes_table*:
            assert "use" in attributes_table
            use_text = attributes_table["use"].lower()
            if use_text == "true":
                use = True
            elif use_text == "false":
                use = False
            else:
                assert False

            # Extract *parameter* from *attributes_table* and *table*:
            assert "name" in attributes_table
            parameter_name = attributes_table["name"]
            parameters = table.parameters
            match_parameter = None
            for parameter in parameters:
                if parameter.name == parameter_name:
                    match_parameter = parameter
                    break
            else:
                assert False
            parameter = match_parameter
        else:
            # Just grab *table*, *parameter*, and *use* directly from *arguments_table*:
            table = arguments_table["table"]
            assert isinstance(table, Table)
            parameter = arguments_table["parameter"]
            assert isinstance(parameter, Parameter)
            use = arguments_table["use"]
            assert isinstance(use, bool)
            
            # Make sure that *parameter* is in *parameters*:
            parameter_name = parameter.name
            parameters = table.parameters
            for parameter in parameters:
                if parameter.name == parameter_name:
                    break
            else:
                assert False

        # Load up *filter* (i.e. *self*):
        filter           = self
        filter.parameter = parameter
        filter.use       = use

    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Start appending the `<Filter...>` element to *xml_lines*:
        filter = self
        parameter = filter.parameter
        xml_lines.append('{0}<Filter name="{1}" use="{2}">'.
          format(indent, parameter.name, filter.use))

        # Append any *enumerations*:
        enumerations = parameter.enumerations
        if len(enumerations) >= 1:
            xml_lines.append('{0}  <FilterEnumerations>'.format(indent))
            for enumeration in enumerations:
                xml_lines.append('{0}    <FilterEnumeration name="{1}" match="{2}"/>'.
                  format(indent, enumeration.name, False))
            xml_lines.append('{0}  </FilterEnumerations>'.format(indent))

        # Wrap up `<Filter...>` element:
        xml_lines.append('{0}</Filter>'.format(indent))

class Parameter:

    # Parameter::
    def __init__(self, **arguments_table):
        is_parameter_tree = "parameter_tree" in arguments_table
        if is_parameter_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["parameter_tree"], etree._Element)
        else:
            assert "name" in arguments_table
            assert "type" in arguments_table
            assert "csv" in arguments_table
            assert "comments" in arguments_table
            arguments_count = 4
            if "default" in arguments_table:
                arguments_count += 1
                assert isinstance(arguments_table["default"], str)
            if "optional" in arguments_table:
                assert isinstance(arguments_table["optional"], bool)
                arguments_count += 1
            if "enumerations" in arguments_table:
                arguments_count += 1
                enumerations = arguments_table["enumerations"]
                for enumeration in enumerations:
                    assert isinstance(enumeration, Enumeration)
            assert len(arguments_table) == arguments_count, arguments_table

        if is_parameter_tree:
            parameter_tree = arguments_table["parameter_tree"]
            assert parameter_tree.tag == "Parameter"
            attributes_table = parameter_tree.attrib
            assert "name" in attributes_table
            name = attributes_table["name"]
            assert "type" in attributes_table
            type = attributes_table["type"].lower()
            if "optional" in attributes_table:
                optional_text = attributes_table["optional"].lower()
                assert optional_text in ("true", "false")
                optional = (optional_text == "true")
            else:
                optional = False
            csv = attributes_table["csv"] if "csv" in attributes_table else ""
            default = attributes_table["default"] if "default" in attributes_table else None
            parameter_tree_elements = list(parameter_tree)
            assert len(parameter_tree_elements) >= 1
            comments_tree = parameter_tree_elements[0]
            assert comments_tree.tag == "ParameterComments"
            assert len(comments_tree.attrib) == 0
            comments = list()
            for comment_tree in comments_tree:
                comment = ParameterComment(comment_tree=comment_tree)
                comments.append(comment)            

            enumerations = list()
            if type == "enumeration":
                assert len(parameter_tree_elements) == 2
                enumerations_tree = parameter_tree_elements[1]
                assert len(enumerations_tree.attrib) == 0
                assert enumerations_tree.tag == "Enumerations"
                assert len(enumerations_tree) >= 1
                for enumeration_tree in enumerations_tree:
                    enumeration = Enumeration(enumeration_tree=enumeration_tree)
                    enumerations.append(enumeration)
            else:
                assert len(parameter_tree_elements) == 1
        else:
            name = arguments_table["name"]
            type = arguments_table["type"]
            csv  = arguments_table["csv"]
            default = arguments_table["defualt"] if "default" in arguments_table else None
            optional = arguments_table["optional"] if "optional" in arguments_table else False
            comments = arguments_table["comments"] if "comments" in arguments_table else list()
            enumerations = \
              arguments_table["enumerations"] if "enumerations" in arguments_table else list()

        # Load values into *parameter* (i.e. *self*):
        super().__init__()
        parameter = self
        parameter.comments     = comments
        parameter.csv          = csv
        parameter.default      = default
        parameter.enumerations = enumerations
        parameter.name         = name
        parameter.optional     = optional
        parameter.type         = type
        parameter.use          = False
        #print("Parameter('{0}'): optional={1}".format(name, optional))
        print("Parameter(name='{0}', type='{1}', csv='{1}')".format(name, type, parameter.csv))

    # Parameter::
    def __eq__(self, parameter2):
        #print("=>Parameter.__eq__()")

        # Verify argument types:
        assert isinstance(parameter2, Parameter)

        # Compare each field of *parameter1* (i.e. *self*) with the corresponding field
        # of *parameter2*:
        parameter1         = self
        name_equal         = (parameter1.name         == parameter2.name)
        default_equal      = (parameter1.default      == parameter2.default)
        type_equal         = (parameter1.type         == parameter2.type)
        optional_equal     = (parameter1.optional     == parameter2.optional)
        comments_equal     = (parameter1.comments     == parameter2.comments)
        enumerations_equal = (parameter1.enumerations == parameter2.enumerations)
        all_equal = (name_equal and
          default_equal and type_equal and optional_equal and comments_equal and enumerations_equal)

        # Debugging code:
        #print("name_equal={0}".format(name_equal))
        #print("default_equal={0}".format(default_equal))
        #print("type_equal={0}".format(type_equal))
        #print("optional_equal={0}".format(optional_equal))
        #print("comments_equal={0}".format(comments_equal))
        #print("enumerations_equal={0}".format(enumerations_equal))
        #print("<=Parameter.__eq__()=>{0}".format(all_equal))

        return all_equal

    # Parameter::
    def xml_lines_append(self, xml_lines, indent):
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Grab some values from *parameter* (i.e. *self*):
        parameter = self
        default = parameter.default
        optional = parameter.optional

        # Start the *parameter* XML add in *optional* and *default* if needed:
        xml_line = '{0}<Parameter name="{1}" type="{2}" csv="{3}"'.format(
          indent, parameter.name, parameter.type, parameter.csv)
        if optional:
            xml_line += ' optional="true"'
        if not default is None:
            xml_line += ' default="{0}"'.format(default)
        xml_line += '>'
        xml_lines.append(xml_line)
        
        # Append all of the comments*:
        comments = parameter.comments
        for comment in comments:
            xml_lines.append('{0}  <ParameterComments>'.format(indent))
            comment.xml_lines_append(xml_lines)
            xml_lines.append('{0}  </ParameterComments>'.format(indent))

        # Append all of the *enumerations*:
        enumerations = parameter.enumerations
        if len(enumerations) >= 1:
            xml_lines.append('{0}  <Enumerations>'.format(indent))
            for enumeration in enumerations:
                enumeration.xml_lines_append(xml_lines, indent + "    ")
            xml_lines.append('{0}  </Enumerations>'.format(indent))

        # Close out the *parameter*:
        xml_lines.append('{0}</Parameter>'.format(indent))

class ParameterComment(Comment):

    # ParameterComment::
    def __init__(self, **arguments_table):
        # Verify argument types:        
        is_comment_tree = "comment_tree" in arguments_table
        if is_comment_tree:
            assert isinstance(arguments_table["comment_tree"], etree._Element)
        else:
            assert "language" in arguments_table and isinstance(arguments_table["language"], str)
            assert "long_heading" in arguments_table \
              and isinstance(arguments_table["long_heading"], str)
            assert "lines" in arguments_table
            lines = arguments_table["lines"]
            for line in lines:
                assert isinstance(line, str)
            arguments_count = 3
            has_short_heading = "short_heading" in arguments_table
            if has_short_heading:
                arguments_count += 1
                assert isinstance(arguments_table["short_heading"], str)
            assert len(arguments_table) == arguments_count

        if is_comment_tree:
            comment_tree = arguments_table["comment_tree"]
            attributes_table = comment_tree.attrib
            attributes_count = 2
            long_heading = attributes_table["longHeading"]
            if "shortHeading" in attributes_table:
                attributes_count += 1
                short_heading = attributes_table["shortHeading"] 
            else:
                short_heading = None
            assert len(attributes_table) == attributes_count
        else:
            long_heading = arguments_table["long_heading"]
            lines = arguments_table["lines"]
            short_heading = arguments_table["short_heading"] if has_short_heading else None
        
        # Initailize the parent of *parameter_comment* (i.e. *self*).  The parent initializer
        # will fill in the *language* and *lines* fields:
        parameter_comment = self
        super().__init__("ParameterComment", **arguments_table)
        assert isinstance(parameter_comment.language, str)
        assert isinstance(parameter_comment.lines, list)

        # Initialize the remaining two fields that are specific to a *parameter_comment*:
        parameter_comment.long_heading = long_heading
        parameter_comment.short_heading = short_heading

    # ParameterComment::
    def __eq__(self, parameter_comment2):
        # Verify argument types:
        assert isinstance(parameter_comment2, ParameterComment)

        parameter_comment1 = self
        language_equal = parameter_comment1.language == parameter_comment2.language
        lines_equal    = parameter_comment1.lines == parameter_comment2.lines
        long_equal     = parameter_comment1.long_heading == parameter_comment2.long_heading
        short_equal    = parameter_comment1.short_heading == parameter_comment2.short_heading
        all_equal      = language_equal and lines_equal and long_equal and short_equal
        return all_equal

    # ParameterComment::
    def xml_lines_append(self, xml_lines):
        parameter_comment = self
        xml_line = '        <ParameterComment language="{0}" longHeading="{1}"'.format(
          parameter_comment.language, parameter_comment.long_heading)
        short_heading = parameter_comment.short_heading
        if not short_heading is None:
            xml_line += ' shortHeading="{0}"'.format(short_heading)
        xml_line += '>'
        xml_lines.append(xml_line)
        for line in parameter_comment.lines:
            xml_lines.append('          {0}'.format(line))
        xml_lines.append('        </ParameterComment>')

class Search:

    # Search::
    def __init__(self, **arguments_table):
        # Verify argument types:
        is_search_tree = "search_tree" in arguments_table
        required_arguments_size = 1 if "tracing" in arguments_table else 0
        if is_search_tree:
            required_arguments_size += 2
            assert "tables" in arguments_table
        else:
            required_arguments_size += 3
            assert "name" in arguments_table
            assert "comments" in arguments_table
            assert "table" in arguments_table
        assert len(arguments_table) == required_arguments_size

        # Perform any request 
        tracing = arguments_table["tracing"] if "tracing" in arguments_table else None
        assert isinstance(tracing, str) or tracing is None
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>Search(*)".format(tracing))

        # Dispatch on is *is_search_tree*:
        if is_search_tree:
            search_tree = arguments_table["search_tree"]
            tables = arguments_table["tables"]
            assert isinstance(tables, list)
            for table in tables:
                assert isinstance(table, Table)
            attributes_table = search_tree.attrib
            assert "name" in attributes_table
            name = attributes_table["name"]

            assert "table" in attributes_table
            table_name = attributes_table["table"]
            match_table = None
            for table in tables:
                if table.name == table_name:
                    match_table = table
                    break
            else:
                assert False, "No table named '{0}'".format(table_name)
            table = match_table

            comments = list()
            filters = list()
            sub_trees = list(search_tree)
            assert len(sub_trees) == 2
            for sub_tree in sub_trees:
                sub_tree_tag = sub_tree.tag
                if sub_tree_tag == "SearchComments":
                    search_comment_trees = list(sub_tree)
                    for search_comment_tree in search_comment_trees:
                        assert search_comment_tree.tag == "SearchComment"
                        comment = SearchComment(comment_tree=search_comment_tree)
                        comments.append(comment)
                elif sub_tree_tag == "Filters":
                    filter_trees = list(sub_tree)
                    for filter_tree in filter_trees:
                        assert filter_tree.tag == "Filter"
                        filter = Filter(tree=filter_tree, table=table)
                        filters.append(filter)
                else:
                    assert False

        else:
            # Grab *name*, *comments* and *table* from *arguments_table*:
            name = arguments_table["name"]
            assert isinstance(name, str)
            comments = arguments_table["comments"]
            assert isinstance(comments, list)
            table = arguments_table["table"]
            assert isinstance(table, Table)
            for comment in comments:
                assert isinstance(comment, SearchComment)
            filters = list()

        # Load arguments into *search* (i.e. *self*):
        search = self
        search.comments = comments
        search.filters = filters
        search.name = name
        search.table = table

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=Search(*):name={1}".format(tracing, name))

    # Search::
    def filters_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>Search.filters_update()".format(tracing))

        # Now we have to make sure that there is a one-to-one corresondance between *filters*
        # and *parameters*:
        search = self
        table = search.table
        if not table is None:
            # Sweep through *filters* and stuff each one into *filters_table* keyed from
            # the *parameter_name* (which is unique):
            filters_table = dict()
            filters = search.filters
            for filter in filters:
                parameter_name = filter.parameter.name
                filters_table[filter.parameter.name] = filter

            # Rebuild *filters* in the exact same order as *parameters*:
            del filters[:]
            parameters = table.parameters
            for parameter_index, parameter in enumerate(parameters):
                # Reuse the *fiter* from *filter_table* only if it has the same name and matches
                # *parameter*:
                filter = None
                parameter_name = parameter.name
                if parameter_name in filters_table:
                    filter = filters_table[parameter.name]
                    if not filter.parameter is parameter:
                        # The names match, but the parameters do not; force generation of a new
                        # *Filter* by setting *filter* to *None*:
                        filter = None

                # If *filter* is empty, generate a new *filter*:
                if filter is None:
                    filter = Filter(parameter=parameter, use=False, table=table)
                filters.append(filter)
                #if not tracing is None:
                #    print("{0}[{1}]: '{2}'".format(tracing, parameter_index,
                #      filters[parameter_index].parameter.name))

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=Search.filters_update()".format(tracing))

    # Search::
    def table_set(self, new_table, tracing=None):
        # Verify argument types:
        assert isinstance(new_table, Table) or new_table is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>Search.table_set('{1})".
              format(tracing, "None" if new_table is None else new_table.name))

        search = self
        search.table = new_table

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=Search.table_set('{1}')".
              format(tracing, "None" if new_table is None else new_table.name))

    # Search:
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Start the `<Search...>` element:
        search = self
        table = search.table
        xml_lines.append('{0}<Search name="{1}" table="{2}">'.
          format(indent, search.name, table.name))

        # Append the `<SearchComments>` element:
        xml_lines.append('{0}  <SearchComments>'.format(indent))
        search_comments = search.comments
        search_comment_indent = indent + "    "
        for search_comment in search_comments:
            search_comment.xml_lines_append(xml_lines, search_comment_indent)
        xml_lines.append('{0}  </SearchComments>'.format(indent))

        # Append the `<Filters>` element:
        filters = search.filters
        xml_lines.append('{0}  <Filters>'.format(indent))
        filter_indent = indent + "    "
        for filter in filters:        
            filter.xml_lines_append(xml_lines, filter_indent)
        xml_lines.append('{0}  </Filters>'.format(indent))

        # Wrap up the `<Search>` element:
        xml_lines.append('{0}</Search>'.format(indent))

class SearchComment(Comment):
    # SearchComment::
    def __init__(self, **arguments_table):
        # Verify argument types:
        is_comment_tree = "comment_tree" in arguments_table
        if is_comment_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["comment_tree"], etree._Element)
        else:
            assert len(arguments_table) == 2
            assert "language" in arguments_table and isinstance(arguments_table["language"], str)
            assert "lines" in arguments_table
            lines = arguments_table["lines"]
            assert isinstance(lines, list)
            for line in lines:
                assert isinstance(line, str)

        # There are no extra attributes above a *Comment* object, so we can just use the
        # intializer for the *Coment* class:
        super().__init__("SearchComment", **arguments_table)

    # SearchComment::
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Append the <SearchComment> element:
        search_comment = self
        lines = search_comment.lines
        xml_lines.append('{0}<SearchComment language="{1}">'.
          format(indent, search_comment.language))
        for line in lines:
            xml_lines.append("{0}  {1}".format(indent, line))
        xml_lines.append('{0}</SearchComment>'.format(indent))

class Table:
    # Table::__init__()
    def __init__(self, **arguments_table):
        # Verify argument types:
        assert "file_name" in arguments_table
        file_name = arguments_table["file_name"]
        assert isinstance(file_name, str)
        is_table_tree = "table_tree" in arguments_table
        if is_table_tree:
            assert len(arguments_table) == 3
            assert "table_tree" in arguments_table and \
              isinstance(arguments_table["table_tree"], etree._Element)
        else:
            # This code also winds up pull out *name 
            assert len(arguments_table) == 5
            # Verify that *comments* is present and has correct type:
            assert "comments" in arguments_table
            comments = arguments_table["comments"]
            assert isinstance(comments, list)
            for comment in comments:
                assert isinstance(comment, TableComment)
            # Verify that *csv_file_name* is present and has correct type:
            assert "csv_file_name" in arguments_table
            csv_file_name = arguments_table["csv_file_name"]
            assert isinstance(csv_file_name, str)
            # Verify that *name* is present and has correct type:
            assert "name" in arguments_table
            name = arguments_table["name"]
            assert isinstance(name, str)
            # Verify that *parameters* is present and has correct type:
            assert "parameters" in arguments_table
            parameters = arguments_table["parameters"]
            assert isinstance(parameters, list)
            for parameter in parameters:
                assert isinstance(parameter, paraemeters)
        
        # Dispatch on *is_table_tree*:
        if is_table_tree:
            # Make sure that *table_tree* is actually a Table tag:
            table_tree = arguments_table["table_tree"]
            assert table_tree.tag == "Table"
            attributes_table = table_tree.attrib

            # Extract *name*:
            assert "name" in attributes_table
            name = attributes_table["name"]

            #FIXME: Temporary kludge:
            assert "csv_file_name" in attributes_table
            csv_file_name = attributes_table["csv_file_name"]

            # Ensure that we have exactly two elements:
            table_tree_elements = list(table_tree)
            assert len(table_tree_elements) == 2

            # Extract the *comments* from *comments_tree_element*:
            comments = list()
            comments_tree = table_tree_elements[0]
            assert comments_tree.tag == "TableComments"
            for comment_tree in comments_tree:
                comment = TableComment(comment_tree=comment_tree)
                comments.append(comment)

            # Extract the *parameters* from *parameters_tree_element*:
            parameters = list()
            parameters_tree = table_tree_elements[1]
            assert parameters_tree.tag == "Parameters"
            for parameter_tree in parameters_tree:
                parameter = Parameter(parameter_tree=parameter_tree)
                parameters.append(parameter)
        else:
            # Otherwise just dircectly grab *name*, *comments*, and *parameters*
            # from *arguments_table*:
            comments = arguments_table["comments"]
            csv_file_name = arguments_table["csv_file_name"]
            name = arguments_table["name"]
            parameters = arguments_table["parameters"]

        # Load up *table* (i.e. *self*):
        table = self
        table.comments      = comments
        table.file_name     = file_name
        table.csv_file_name = csv_file_name
        table.name          = name
        table.parameters    = parameters

    # Table::
    def __eq__(self, table2):
        # Verify argument types:
        assert isinstance(table2, Table), "{0}".format(type(table2))

        # Compare each field in *table1* (i.e. *self*) with the corresponding field in *table2*:
        table1 = self
        file_name_equal  = (table1.file_name  == table2.file_name)
        name_equal       = (table1.name       == table2.name)
        comments_equal   = (table1.comments   == table2.comments)
        parameters_equal = (table1.parameters == table2.parameters)
        all_equal = (file_name_equal and name_equal and comments_equal and parameters_equal)

        # Debugging code:
        #print("file_name_equal={0}".format(file_name_equal))
        #print("name_equal={0}".format(name_equal))
        #print("comments_equal={0}".format(comments_equal))
        #print("parameters_equal={0}".format(parameters_equal))
        #print("all_equal={0}".format(all_equal))

        return all_equal

    # Table::
    def header_labels_get(self):
        table = self
        parameters = table.parameters
        parameters_size = len(parameters)
        assert len(parameters) >= 1
        header_labels = list()
        for parameter in parameters:
            parameter_comments = parameter.comments
            header_label = "?"
            if len(parameter_comments) >= 1:
                parameter_comment = parameter_comments[0]
                short_heading = parameter_comment.short_heading
                long_heading = parameter_comment.long_heading
                header_label = short_heading if not short_heading is None else long_heading
            header_labels.append(header_label)
        return header_labels

    # Table::
    def save(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        table = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>Table.save('{1}')".format(tracing, table.name))

        # Write out *table* (i.e. *self*) to *file_name*:
        output_file_name = "/tmp/" + table.file_name
        xml_text = table.to_xml_string()
        with open(output_file_name, "w") as output_file:
            output_file.write(xml_text)

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}=>Table.save('{1}')".format(tracing, table.name))

    # Table::
    def to_xml_string(self):
        table = self
        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        table.xml_lines_append(xml_lines, "")
        xml_lines.append("")
        text = '\n'.join(xml_lines)
        return text

    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Start appending the `<Table...>` element:
        table = self
        xml_lines.append('{0}<Table name="{1}" csv_file_name="{2}">'.
          format(indent, table.name, table.csv_file_name))

        # Append the `<TableComments>` element:
        xml_lines.append('{0}  <TableComments>'.format(indent))
        for comment in table.comments:
            comment.xml_lines_append(xml_lines, indent + "    ")
        xml_lines.append('{0}  </TableComments>'.format(indent))

        # Append the `<Parameters>` element:
        xml_lines.append('{0}  <Parameters>'.format(indent))
        for parameter in table.parameters:
            parameter.xml_lines_append(xml_lines, "    ")
        xml_lines.append('{0}  </Parameters>'.format(indent))

        # Close out the `<Table>` element:
        xml_lines.append('{0}</Table>'.format(indent))

class TableComment(Comment):
    # TableComment::
    def __init__(self, **arguments_table):
        # Verify argument types:
        is_comment_tree = "comment_tree" in arguments_table
        if is_comment_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["comment_tree"], etree._Element)
        else:
            assert len(arguments_table) == 2
            assert "language" in arguments_table and isinstance(arguments_table["language"], str)
            assert "lines" in arguments_table
            lines = arguments_table["lines"]
            assert isinstance(lines, list)
            for line in lines:
                assert isinstance(line, str)

        # There are no extra attributes above a *Comment* object, so we can just use the
        # intializer for the *Coment* class:
        super().__init__("TableComment", **arguments_table)

    # TableComment::
    def __equ__(self, table_comment2):
        # Verify argument types:
        assert isinstance(table_comment2, TableComment)
        return super().__eq__(table_comment2)

    # TableComment::
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Append the <TableComment...> element:
        table_comment = self
        xml_lines.append('{0}<TableComment language="{1}">'.format(indent, table_comment.language))
        for line in table_comment.lines:
            xml_lines.append('{0}  {1}'.format(indent, line))
        xml_lines.append('{0}</TableComment>'.format(indent))

def main():
    #table_file_name = "drills_table.xml"
    #assert os.path.isfile(table_file_name)
    #with open(table_file_name) as table_read_file:
    #    table_input_text = table_read_file.read()
    #table_tree = etree.fromstring(table_input_text)
    #table = Table(file_name=table_file_name, table_tree=table_tree)
    #table_write_text = table.to_xml_string()
    #with open("/tmp/" + table_file_name, "w") as table_write_file:
    #    table_write_file.write(table_write_text)

    # Partition the command line *arguments* into *xml_file_names* and *xsd_file_names*:
    #arguments = sys.argv[1:]
    #xml_file_names = list()
    #xsd_file_names = list()
    #for argument in arguments:
    #    if argument.endswith(".xml"):
    #        xml_file_names.append(argument)
    #    elif argument.endswith(".xsd"):
    #        xsd_file_names.append(argument)
    #    else:
    #        assert "File name '{0}' does not have a suffix of '.xml' or '.xsd'"
    #
    ## Verify that we have one '.xsd' file and and one or more '.xml' files:
    #assert len(xsd_file_names) < 2, "Too many '.xsd` files specified"
    #assert len(xsd_file_names) > 0, "No '.xsd' file specified"
    #assert len(xml_file_names) > 0, "No '.xml' file specified"

    # Deal with command line *arguments*:
    arguments = sys.argv[1:]
    #print("arguments=", arguments)
    if True:
        # Read in each *table_file_name* in *arguments* and append result to *tables*:
        tables = list()
        for table_file_name in arguments:
            # Verify that *table_file_name* exists and has a `.xml` suffix:
            assert os.path.isfile(table_file_name), "'{0}' does not exist".format(table_file_name)
            assert table_file_name.endswith(".xml"), \
              "'{0}' does not have a .xml suffix".format(table_file_name)

            # Read in *table_file_name* as a *table* and append to *tables* list:
            with open(table_file_name) as table_read_file:
                table_input_text = table_read_file.read()
            table_tree = etree.fromstring(table_input_text)
            table = Table(file_name=table_file_name, table_tree=table_tree, csv_file_name="")
            tables.append(table)

            #ui_text = table.to_ui_string()
            #with open("/tmp/test.ui", "w") as ui_file:
            #    ui_file.write(ui_text)

            # For debugging only, write *table* out to the `/tmp` directory:
            debug = False
            debug = True
            if debug:
                table_write_text = table.to_xml_string()
                with open("/tmp/" + table_file_name, "w") as table_write_file:
                    table_write_file.write(table_write_text)

        # Now create the *tables_editor* graphical user interface (GUI) and run it:
        tables_editor = TablesEditor(tables, tracing="")

        # Start up the GUI:
        tables_editor.run()

    # When we get here, *tables_editor* has stopped running and we can return.
    return 0

    # Old Stuff....

    # Read the contents of the file named *xsd_file_name* into *xsd_file_text*:
    xsd_file_name = xsd_file_names[0]
    with open(xsd_file_name) as xsd_file:
        xsd_file_text = xsd_file.read()

    # Parse *xsd_file_text* into *xsd_schema*:
    xsd_schema = xmlschema.XMLSchema(xsd_file_text)

    # Iterate across all of the *xml_file_names* and verify that they are valid:
    for xml_file_name in xml_file_names:
        with open(xml_file_name) as xml_file:
            xml_file_text = xml_file.read()
        xsd_schema.validate(xml_file_text)

    # Parse the *xsd_file_text* into *xsd_root*:
    xsd_root = etree.fromstring(xsd_file_text)
    show(xsd_root, "")

    schema = Schema(xsd_root)
    assert schema == schema

    # For debugging:
    schema_text = schema.to_string()
    with open("/tmp/drills.xsd", "w") as schema_file:
        schema_file.write(schema_text)

    # Now run the *tables_editor* graphical user interface (GUI):
    tables_editor = TablesEditor(xsd_root, schema)
    tables_editor.run()

class TablesEditor:

    # TablesEditor::__init__()
    def __init__(self, tables, tracing=None):
        # Verify argument types:
        assert isinstance(tables, list)
        for table in tables:
            assert isinstance(table, Table)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.__init__(...)".format(tracing))

        # Create the *application* first:
        application = QApplication(sys.argv)

        # Create *main_window* from thie `.ui` file:
        ui_qfile = QFile("tables_editor.ui")
        ui_qfile.open(QFile.ReadOnly)
        loader = QUiLoader()
        main_window = loader.load(ui_qfile)

        
        #ui_qfile = QFile("/tmp/test.ui")
        #ui_qfile.open(QFile.ReadOnly)
        #loader.registerCustomWidget(CheckableComboBox)
        #search_window = loader.load(ui_qfile)

        for table in tables:
            break
            for parameter in table.parameters:
                if parameter.type == "enumeration":
                    name = parameter.name
                    checkable_combo_box = getattr(search_window, name + "_combo_box")
                    enumerations = parameter.enumerations
                    for enumeration in enumerations:
                        checkable_combo_box.addItem(enumeration.name)
                        #checkable_combo_box.setCheckable(True)

        # For debugging:
        for table in tables:
            break
            parameters = table.parameters
            for index, parameter in enumerate(parameters):
                name = parameter.name
                radio_button = getattr(search_window, name + "_radio_button")
                print("[{0}]: Radio Button '{1}' {2}".format(index, name, radio_button))
                check_box = getattr(search_window, name + "_check_box")
                print("[{0}]: Check Box '{1}' {2}".format(index, name, check_box))
                if parameter.type == "enumeration":
                    line_edit = getattr(search_window, name + "_combo_box")
                else:
                    line_edit = getattr(search_window, name + "_line_edit")
                print("[{0}]: Line Edit '{1}' {2}".format(index, name, line_edit))

        # Grab the file widgets from *main_window*:

        #file_line_edit   = main_window.file_line_edit
        #file_new_button  = main_window.file_new_button
        #file_open_button = main_window.file_open_button
        
        # Connect file widgets to their callback routines:
        tables_editor = self
        #file_line_edit.textEdited.connect(
        #  partial(TablesEditor.file_line_edit_changed,  tables_editor))
        #file_new_button.clicked.connect(
        #  partial(TablesEditor.file_new_button_clicked,  tables_editor))
        #nfile_open_button.clicked.connect(
        #  partial(TablesEditor.file_open_button_clicked, tables_editor))

        # Load all values into *tables_editor* before creating *combo_edit*.
        # The *ComboEdit* initializer needs to access *tables_editor.main_window*:
        current_table = tables[0] if len(tables) >= 1 else None
        tables_editor.application = application
        tables_editor.current_comment = None
        tables_editor.current_enumeration = None
        tables_editor.current_parameter = None
        tables_editor.current_search = None
        tables_editor.current_table = current_table
        tables_editor.current_tables = tables
        tables_editor.in_signal = True
        tables_editor.import_column_triples = None
        tables_editor.import_headers = None
        tables_editor.import_rows = None
        tables_editor.languages = ["English", "Spanish", "Chinese"]
        tables_editor.main_window = main_window
        tables_editor.original_tables = copy.deepcopy(tables)
        tables_editor.searches = list()
        tables_editor.tables = tables
        tables_editor.trace_signals = not tracing is None

        # Set up *tables* first, followed by *parameters*, followed by *enumerations*:

        # Set up *tables_combo_edit* and stuff into *tables_editor*:
        new_item_function = partial(TablesEditor.table_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_table_set, tables_editor)
        comment_get_function = partial(TablesEditor.table_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.table_comment_set, tables_editor)
        tables_combo_edit = ComboEdit(
          "tables",
          tables_editor,
          tables,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          combo_box       = main_window.tables_combo,
          comment_text    = main_window.tables_comment_text,
          delete_button   = main_window.tables_delete, 
          first_button    = main_window.tables_first,
          last_button     = main_window.tables_last,
          line_edit       = main_window.tables_line,
          next_button     = main_window.tables_next,
          new_button      = main_window.tables_new,
          previous_button = main_window.tables_previous,
          rename_button   = main_window.tables_rename,
          tracing         = next_tracing)
        tables_editor.tables_combo_edit = tables_combo_edit

        # Set up *parameters_combo_edit* and stuff into *tables_editor*:
        parameters = list() if current_table is None else current_table.parameters
        new_item_function = partial(TablesEditor.parameter_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_parameter_set, tables_editor)
        comment_get_function = partial(TablesEditor.parameter_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.parameter_comment_set, tables_editor)
        parameters_combo_edit = ComboEdit(
          "parameters",
          tables_editor,
          parameters,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          combo_box       = main_window.parameters_combo,
          comment_text    = main_window.parameters_comment_text,
          delete_button   = main_window.parameters_delete, 
          first_button    = main_window.parameters_first,
          last_button     = main_window.parameters_last,
          line_edit       = main_window.parameters_line,
          next_button     = main_window.parameters_next,
          new_button      = main_window.parameters_new,
          previous_button = main_window.parameters_previous,
          rename_button   = main_window.parameters_rename,
          tracing         = next_tracing)
        tables_editor.parameters_combo_edit = parameters_combo_edit

        # Set up *enumerations_combo_edit* and stuff into *tables_editor*:
        enumerations = \
          list() if parameters is None or len(parameters) == 0 else parameters[0].enumerations
        new_item_function = partial(TablesEditor.enumeration_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_enumeration_set, tables_editor)
        comment_get_function = partial(TablesEditor.enumeration_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.enumeration_comment_set, tables_editor)
        enumerations_combo_edit = ComboEdit(
          "enumerations",
          tables_editor,
          enumerations,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          combo_box       = main_window.enumerations_combo,
          comment_text    = main_window.enumerations_comment_text,
          delete_button   = main_window.enumerations_delete, 
          first_button    = main_window.enumerations_first,
          last_button     = main_window.enumerations_last,
          line_edit       = main_window.enumerations_line,
          next_button     = main_window.enumerations_next,
          new_button      = main_window.enumerations_new,
          previous_button = main_window.enumerations_previous,
          rename_button   = main_window.enumerations_rename,
          tracing         = next_tracing)
        tables_editor.enumerations_combo_edit = enumerations_combo_edit

        # Now build the *searches_combo_edit* and stuff into *tables_editor*:
        searches = tables_editor.searches
        new_item_function = partial(TablesEditor.search_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_search_set, tables_editor)
        comment_get_function = partial(TablesEditor.search_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.search_comment_set, tables_editor)
        searches_combo_edit = ComboEdit(
          "searches",
          tables_editor,
          searches,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          combo_box       = main_window.searches_combo,
          comment_text    = main_window.searches_comment_text,
          delete_button   = main_window.searches_delete, 
          first_button    = main_window.searches_first,
          last_button     = main_window.searches_last,
          line_edit       = main_window.searches_line,
          next_button     = main_window.searches_next,
          new_button      = main_window.searches_new,
          previous_button = main_window.searches_previous,
          rename_button   = main_window.searches_rename,
          tracing         = next_tracing)
        tables_editor.searches = searches
        tables_editor.searches_combo_edit = searches_combo_edit

        # Perform some global signal connections to *main_window* (abbreviated as *mw*):
        mw = main_window
        mw.root_tabs.currentChanged.connect(                tables_editor.tab_changed)
        mw.schema_tabs.currentChanged.connect(              tables_editor.tab_changed)
        mw.find_tabs.currentChanged.connect(                tables_editor.tab_changed)
        mw.common_save_button.clicked.connect(              tables_editor.save_button_clicked)
        mw.common_quit_button.clicked.connect(              tables_editor.quit_button_clicked)
        mw.parameters_csv_line.textChanged.connect(         tables_editor.parameter_csv_changed)
        mw.parameters_default_line.textChanged.connect(     tables_editor.parameter_default_changed)
        mw.parameters_long_line.textChanged.connect(        tables_editor.parameter_long_changed)
        mw.parameters_optional_check.clicked.connect(      tables_editor.parameter_optional_clicked)
        mw.parameters_short_line.textChanged.connect(       tables_editor.parameter_short_changed)
        mw.parameters_type_combo.currentTextChanged.connect(tables_editor.parameters_type_changed)
        mw.searches_table_combo.currentTextChanged.connect( tables_editor.searches_table_changed)
        mw.import_csv_file_line.textChanged.connect(     tables_editor.import_csv_file_line_changed)
        mw.import_read.clicked.connect(                    tables_editor.import_read_button_clicked)
        mw.import_bind.clicked.connect(                    tables_editor.import_bind_button_clicked)

        mw.import_csv_file_line.setText("download.csv")

        # Set the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor*:
        current_table = None
        current_parameter = None
        current_enumeration = None
        if len(tables) >= 1:
            table = tables[0]
            parameters = table.parameters
            if len(parameters) >= 1:
                parameter = parameters[0]
                current_parameter = parameter
                enumerations = parameter.enumerations
                if len(enumerations) >= 1:
                    enumeration = enumerations[0]
                    current_enumeration = enumeration
            table.current_table       = current_table
            table.current_parameter   = current_parameter
            table.current_enumeration = current_enumeration

        #tables_editor.table_setup(tracing=next_tracing)

        # Read in `/tmp/searches.xml` if it exists:
        tables_editor.searches_load("/tmp/searches.xml", tracing=next_tracing)

        # Update the entire user interface:
        tables_editor.update(tracing=next_tracing)

        tables_editor.in_signal = False

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.__init__(...)\n".format(tracing))

    # TablesEditor::comment_text_set()
    def comment_text_set(self, new_text, tracing=None):
        # Verify argument types:
        assert isinstance(new_text, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested tracing:
        tables_editor = self
        if not tracing is None:
            print("{0}=>TablesEditor.comment_text_set(...)".format(tracing))

        # Carefully set thet text:
        main_window = tables_editor.main_window
        comment_text = main_window.parameters_comment_text
        comment_text.setPlainText(new_text)

        # Wrap up any requested tracing:
        if not tracing is None:
            print("{0}<=TablesEditor.comment_text_set(...)".format(tracing))

    # TablesEditor::current_enumeration_set()
    def current_enumeration_set(self, enumeration, tracing=None):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None, \
          "{0}".format(enumeration)
        assert isinstance(tracing, str) or tracing is None

        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.current_enumeration_set('{1}')".
              format(tracing, "None" if enumeration is None else enumeration.name))

        # Only do something if we are not in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any tracing requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.current_enumeration_set('{0}')".
                  format("None" if enumeration is None else enumeration.name))

            # Finally, set the *current_enumeration*:
            tables_editor.current_enumeration = enumeration

            # Wrap up any requested tracing:
            if trace_signals:
                print("<=TablesEditor.current_enumeration_set('{0}')\n".
                  format("None" if enumeration is None else enumeration.name))
            tables_editor.in_signal = False

        if not tracing is None:
            print("{0}<=TablesEditor.current_enumeration_set('{1}')".
              format(tracing, "None" if enumeration is None else enumeration.name))

    # TablesEditor::current_parameter_set()
    def current_parameter_set(self, parameter, tracing=None):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if not tracing is None:
            name = "None" if parameter is None else parameter.name
            print("{0}=>TablesEditor.current_parameter_set(*, '{1}')".format(tracing, name))

        # Set the *current_parameter* in *tables_editor*:
        tables_editor = self
        tables_editor.current_parameter = parameter

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.current_parameter_set(*, '{1}')".format(tracing, name))

    # TablesEditor::current_search_set()
    def current_search_set(self, new_current_search, tracing=None):
        # Verify argument types:
        assert isinstance(new_current_search, Search) or new_current_search is None, \
          print(new_current_search)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if not tracing is None:
            print("{0}=>TablesEditor.current_search_set('{1}')".
              format(tracing, "None" if new_current_search is None else new_current_search.name))
    
        # Make sure *new_current_search* is in *searches*:
        tables_editor = self
        searches = tables_editor.searches
        if not new_current_search is None:
            for search_index, search in enumerate(searches):
                assert isinstance(search, Search)
                if not tracing is None:
                    print("{0}Search[{1}]: '{2}'".format(tracing, search_index, search.name))
                if search is new_current_search:
                    break
            else:
                assert False
        tables_editor.current_search = new_current_search

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.current_table_set('{1}')".
              format(tracing, "None" if new_current_search is None else new_current_search.name))

    # TablesEditor::current_table_set()
    def current_table_set(self, new_current_table, tracing=None):
        # Verify argument types:
        assert isinstance(new_current_table, Table) or new_current_table is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if not tracing is None:
            print("{0}=>TablesEditor.current_table_set('{1}')".
              format(tracing, "None" if new_current_table is None else new_current_table.name))

        # Stuff *new_current_table* into *tables_editor*:
        tables_editor = self
        if not new_current_table is None:
            tables = tables_editor.tables
            for table in tables:
                if table is new_current_table:
                    break
            else:
                assert False, "table '{0}' not in tables list".format(new_current_table.name)
        tables_editor.current_table = new_current_table 

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.current_table_set('{1}')".
              format(tracing, "None" if new_current_table is None else new_current_table.name))

    # TablesEditor::current_update()
    def current_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.current_update()".format(tracing))

        # Make sure *current_table* is valid (or *None*):
        tables = tables_editor.tables
        tables_size = len(tables)
        current_table = None
        if tables_size >= 1:
            # Figure out if *current_table* is in *tables):
            current_table = tables_editor.current_table
            if not current_table is None:
                for table_index, table in enumerate(tables):
                    #print("Table[{0}]: '{1}'".format(table_index, table.name))
                    assert isinstance(table, Table)
                    if table is current_table:
                        break
                else:
                    # *current_table* points to a *Table* object that is not in *tables* and
                    # is invalid:
                    current_table = None
        if current_table is None and tables_size >= 1:
            current_table = tables[0]
        tables_editor.current_table = current_table
        if not tracing is None:
            print("{0}current_table='{1}'".
              format(tracing, "None" if current_table is None else current_table.name))
                
        # Make sure *current_parameter* is valid (or *None*):
        current_parameter = None
        if current_table is None:
            parameters = list()
        else:
            parameters = current_table.parameters
            parameters_size = len(parameters)
            if parameters_size >= 1:
                current_parameter = tables_editor.current_parameter
                if not current_parameter is None:
                    for parameter in parameters:
                        assert isinstance(parameter, Parameter)
                        if parameter is current_parameter:
                            break
                    else:
                        # *current_parameter* is invalid:
                        current_parameter = None
            if current_parameter is None and parameters_size >= 1:
                current_parameter = parameters[0]
        tables_editor.current_parameter = current_parameter
        if not tracing is None:
            print("{0}current_parameter='{1}'".
              format(tracing, "None" if current_parameter is None else current_parameter.name))

        # Update *parameters* in *parameters_combo_edit*:
        parameters_combo_edit = tables_editor.parameters_combo_edit
        parameters_combo_edit.items_replace(parameters)

        # Make sure *current_enumeration* is valid (or *None*):
        current_enumeration = None
        if current_parameter is None:
            enumerations = list()
        else:
            enumerations = current_parameter.enumerations
            enumerations_size = len(enumerations)
            if enumerations_size >= 1:
                current_enumeration = tables_editor.current_enumeration
                if not current_enumeration is None:
                    for enumeration in enumerations:
                        assert isinstance(enumeration, Enumeration)
                        if enumeration is current_enumeration:
                            break
                    else:
                        # *current_enumeration* is invalid:
                        current_enumeration = None
                if current_enumeration is None and enumerations_size >= 1:
                    current_enuermation = enumerations[0]
        tables_editor.current_enumeration = current_enumeration
        if not tracing is None:
            print("{0}current_enumeration'{1}'".
              format(tracing, "None" if current_enumeration is None else current_enumeration.name))

        # Update *enumerations* into *enumerations_combo_edit*:
        enumerations_combo_edit = tables_editor.enumerations_combo_edit
        enumerations_combo_edit.items_replace(enumerations)

        # Make sure that *current_search* is valid (or *None*):
        searches = tables_editor.searches
        current_search = tables_editor.current_search
        if current_search is None:
            if len(searches) >= 1:
                current_search = searches[0]
        else:
            for search_index, search in enumerate(searches):
                if search is current_search:
                    break
            else:
                # *current_search* is not in *searches* and must be invalid:
                current_search = None
        tables_editor.current_search = current_search
        if not tracing is None:
            print("{0}current_search='{1}'".
              format(tracing, "None" if current_search is None else current_search.name))

        # Wrap up any requested tracing:
        if not tracing is None:
            print("{0}<=TablesEditor.current_update()".format(tracing))

    # TablesEditor::data_update()
    def data_update(self, tracing=None):
        # Verify artument types:
        assert isinstance(tracing, str) or tracing is None
        
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.data_update()".format(tracing))
        
        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if not tracing is None:
            print("{0}<=TablesEditor.data_update()".format(tracing))

    # TablesEditor::enumeration_changed()
    def enumeration_changed(self):
        assert False

    # TablesEditor::enumeration_comment_get()
    def enumeration_comment_get(self, enumeration, tracing=None):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            name = "None" if tracing is None else enumeration.name
            print("{0}=>enumeration_comment_get('{1}')".format(tracing, name))

        # Extract the comment *text* associated with *enumeration*:
        position = 0
        text = ""
        if not enumeration is None:
            comments = enumeration.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, EnumerationComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=table_enumeration_get('{1}')".format(tracing, name))
        return text, position

    # TablesEditor::enumeration_comment_set()
    def enumeration_comment_set(self, enumeration, text, position, tracing=None):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            name = "None" if tracing is None else enumeration.name
            print("{0}=>enumeration_comment_set('{1}')".format(tracing, name))

        # Stuff *text* into *enumeration*:
        if not enumeration is None:
            comments = enumeration.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, EnumerationComment)
            comment.lines = text.split('\n')
            comment.position = position

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=enumeration_comment_set('{1}')".format(tracing, name))

    # TablesEditor::enumeration_new()
    def enumeration_new(self, name):
        # Verify argument types:
        assert isinstance(name, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.enumeration_new('{0}')".format(name))

        # Create *new_parameter* named *name*:
        comments = [EnumerationComment(language="EN", lines=list())]
        new_enumeration = Enumeration(name=name, comments=comments)

        # Wrap up any requested tracing and return *new_parameter*:
        if trace_level >= 1:
            print("<=TablesEditor.enumeration_new('{0}')=>'{1}'".format(new_enumeration.name))
        return new_parameter

    # TablesEditor::enumerations_update()
    def enumerations_update(self, enumeration=None, tracing=None):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        #trace_level = tables_editor.trace_level
        #if trace_level >= 1:
        #    print("=>TablesEditor.enumerations_update()")
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.enumerations_update()".format(tracing))

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update(tracing=next_tracing)

        # Grab some widgets from *main_window*:
        main_window    = tables_editor.main_window
        table_name     = main_window.enumerations_table_name
        parameter_name = main_window.enumerations_parameter_name
        combo          = main_window.enumerations_combo

        # Upbdate the *table_name* and *parameter_name* widgets:
        current_table = tables_editor.current_table
        table_name.setText("" if current_table is None else current_table.name)
        current_parameter = tables_editor.current_parameter
        parameter_name.setText("" if current_parameter is None else current_parameter.name)

        # Empty out *enumeration_combo* widgit:
        main_window = tables_editor.main_window
        while combo.count() > 0:
            combo.removeItem(0)
        if not tracing is None:
            print("{0}Here 1".format(tracing))

        # Grab *enumerations* from *current_parameter* (if possible):
        if not current_parameter is None and current_parameter.type.lower() == "enumeration":
            enumerations = current_parameter.enumerations
            
            # Now fill in *enumerations_combo_box* from *enumerations*:
            current_enumeration_index = -1
            for index, enumeration in enumerate(enumerations):
                enumeration_name = enumeration.name
                if not tracing is None:
                    print("{0}[{1}]'{2}'".format(tracing, index, enumeration.name))
                #print("[{0}]'{1}'".format(index, enumeration_name))
                combo.addItem(enumeration_name, tracing=next_tracing)
        if not tracing is None:
            print("{0}Here 2".format(tracing))

        # Update the *enumerations_combo_edit*:
        tables_editor.enumerations_combo_edit.gui_update(tracing=next_tracing)

        # Wrap-up and requested tracing:
        #if trace_level >= 1:
        #    print("<=TablesEditor.enumerations_update()")
        if not tracing is None:
            print("{0}<=TablesEditor.enumerations_update()".format(tracing))

    # TablesEditor::filter_use_clicked()
    def filter_use_clicked(self, use_item, filter, row, column):
        # Verify argument types:
        assert isinstance(use_item, QTableWidgetItem)
        assert isinstance(filter, Filter)
        assert isinstance(row, int)
        assert isinstance(column, int)

        # Do nothing if we are already in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform an requested signal tracing:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.filter_use_clicked(*, '{0}', {1}, {2})".
                  format(filter.parameter.name, row, column))

            check_state = use_item.checkState()
            print("check-state=", check_state)
            if check_state == Qt.CheckState.Checked:
                result = "checked"
                filter.use = True
            elif check_state == Qt.CheckState.Unchecked:
                result = "unchecked"
                filter.use = False
            elif check_state == Qt.CheckState.PartiallyChecked:
                result = "partially checked"
            else:
                result = "unknown"

            # Wrap up any signal tracing:
            if trace_signals:
                print("parameter check state={0}".format(result))
                print("<=TablesEditor.filter_use_clicked(*, '{0}', {1}, {2})\n".
                  format(filter.parameter.name, row, column))
            tables_editor.in_signal = True

    # TablesEditor::filters_update()
    def filters_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.filters_update()".format(tracing))

        # Empty out *filters_table* widget:
        tables_editor = self
        main_window = tables_editor.main_window
        filters_table = main_window.filters_table
        filters_table.clearContents()
        filters_table.setHorizontalHeaderLabels(["Parameter", "Use", "?"])
        filters_table.setColumnCount(3)
        
        # Only fill in *filters_table* if there is a valid *current_search*:
        tables_editor.current_update(tracing=next_tracing)
        current_search = tables_editor.current_search
        if current_search is None:
            # No *current_search* so there is nothing to show:
            filters_table.setRowCount(0)    
        else:
            # Let's update the *filters* and load them into the *filters_table* widget:
            current_search.filters_update(tracing=next_tracing)
            filters = current_search.filters
            filters_size = len(filters)
            filters_table.setRowCount(filters_size)

            # Fill in one *filter* at a time:
            for filter_index, filter in enumerate(filters):
                # Create the header label in the first column:
                parameter = filter.parameter
                #if not tracing is None:
                #    print("{0}[{1}]: '{2}'".format(tracing, filter_index, parameter_name))
                parameter_comments = parameter.comments
                assert len(parameter_comments) >= 1
                parameter_comment = parameter_comments[0]
                assert isinstance(parameter_comment, ParameterComment)
    
                # Figure out what *heading* to use:
                parameter_name = parameter.name
                short_heading = parameter_comment.short_heading
                long_heading = parameter_comment.long_heading
                heading = short_heading
                if heading is None:
                    heading = long_heading
                if heading is None:
                    heading = parameter_name
                if not tracing is None:
                    print("{0}[{1}]: sh='{2}' lh='{3}' pn='{4}".format(
                      tracing, filter_index, short_heading, long_heading, parameter_name))
    
                header_item = QTableWidgetItem(heading)
                header_item.setData(Qt.UserRole, parameter)
                filters_table.setItem(filter_index, 0, header_item)
                
                # Create the use [] check box in the second column:
                use_item = QTableWidgetItem("")
                assert isinstance(use_item, QTableWidgetItem)
                #print(type(use_item))
                #print(use_item.__class__.__bases__)
                flags = use_item.flags()
                use_item.setFlags(flags | Qt.ItemIsUserCheckable)
                check_state = Qt.Checked if filter.use else Qt.Unchecked
                use_item.setCheckState(check_state)
                #use_item.itemChanged.connect(
                #  partial(TablesEditor.search_use_clicked, tables_editor, use_item, parameter))
                #filter.use = False
                filters_table.setItem(filter_index, 1, use_item)
                filters_table.cellClicked.connect(
                  partial(TablesEditor.filter_use_clicked, tables_editor, use_item, filter))
    
                pattern_item = QTableWidgetItem("")
                pattern_item.setData(Qt.UserRole, parameter)
                filters_table.setItem(filter_index, 2, pattern_item)

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.filters_update()".format(tracing))

    # TablesEditor::find_update():
    def find_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing == None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.find_update()".format(tracing))

        tables_editor = self
        main_window = tables_editor.main_window
        find_tabs = main_window.find_tabs
        find_tabs_index = find_tabs.currentIndex()
        if find_tabs_index == 0:
            tables_editor.searches_update(tracing=next_tracing)
        elif find_tabs_index == 1:
            tables_editor.filters_update(tracing=next_tracing)
        elif find_tabs_index == 2:
            tables_editor.results_update(tracing=next_tracing)
        else:
            assert False

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.find_update()".format(tracing))

    # TablesEditor::import_bind_clicked():
    def import_bind_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals
        next_tracing = "" if trace_signals else None
        if trace_signals:
            print("=>TablesEditor.import_bind_button_clicked()")
        
        # Update *current_table* an *parameters* from *tables_editor*:
        tables_editor.current_update(tracing=next_tracing)
        current_table = tables_editor.current_table
        if not current_table is None:
            parameters = current_table.parameters
            headers        = tables_editor.import_headers
            column_triples = tables_editor.import_column_triples
            for column_index, triples in enumerate(column_triples):
                header = headers[column_index]
                if len(triples) >= 1:
                    triple = triples[0]
                    count, name, value = triple
                    for parameter_index, parameter in enumerate(parameters):
                        if parameter.csv == name:
                            break
                    else:
                        scrunched_name = \
                          "".join([character for character in header if character.isalnum()])
                        comments = [ ParameterComment( language="EN",
                          long_heading=scrunched_name, lines=list() ) ]
                        parameter = Parameter(name=scrunched_name,
                          type=name, csv=header, comments=comments)
                        parameters.append(parameter)
                
            tables_editor.update(tracing=next_tracing)

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("<=TablesEditor.import_bind_button_clicked()")

    # TablesEditor::import_button_clicked():
    def import_read_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals
        next_tracing = "" if trace_signals else None
        if trace_signals:
            print("=>TablesEditor.import_read_button_clicked()")

        # Update *current_table* an *parameters* from *tables_editor*:
        tables_editor.current_update(tracing=next_tracing)
        current_table = tables_editor.current_table
        assert not current_table is None
        parameters = current_table.parameters
        assert not parameters is None

        # Read the *csv_file_name* from the *import_csv_file_line* widget:
        main_window = tables_editor.main_window
        import_csv_file_line = main_window.import_csv_file_line
        csv_file_name = import_csv_file_line.text()

        # Open *csv_file_name* and start processing it:
        with open(csv_file_name, newline="") as csv_file:
            # Read in *csv_file* using *csv_reader*:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
            column_tables = None
            headers = None
            columns_count = -1

            # Process each *row* that comes in from *csv_reader*:
            data_rows = list()
            column_tables = None
            for row_index, row in enumerate(csv_reader):
                if row_index == 0:
                    # The first *row* is a header line:
                    for header in row:
                        scrunched_header = header.replace(" ", "").replace(".", "")
                        for parameter in parameters:
                            if parameter.name == scrunched_header:
                                break
                        else:
                            comments = [ ParameterComment(language="EN",
                              lines=list(), long_heading=scrunched_header) ]
                            #parameter = Parameter(name=scrunched_header,
                            #  type="string",  csv=header, comments = comments)
                            #parameters.append(parameter)

                    # Create *column_tables* which is used to process the following *row*'s:
                    column_tables = [ dict() for header in row ]
                    headers = row
                else:
                    # The second and subsequent *row*'s a contain data.  Build up a count of each
                    # of the different data values in for a givin column in *column_table*:
                    data_rows.append(row)
                    for column_index, value in enumerate(row):
                        column_table = column_tables[column_index]
                        if value in column_table:
                            # We have seen *value* before, so increment its count:
                            column_table[value] += 1
                        else:
                            # This is the first time we seen *value*, so insert it into
                            # *column_table* as the first one:
                            column_table[value] = 1

                # Now *column_tables* has a list of tables (i.e. *dict*'s) where it entry
                # has a count of the number of times that value occured in the column.

                # Create some regular expressions and stuff the into *re_list*:
                integer_re = re.compile("-?[0-9]+$")
                float_re   = re.compile("-?[0-9]*\.[0-9]*$")
                url_re     = re.compile("(https?://)|(//).*$")
                empty_re   = re.compile("-?$")
                funits_re  = re.compile("-?[0-9]*\.[0-9]* *.?[a-zA-Z]+$")
                iunits_re  = re.compile("-?[0-9]+.? *[a-zA-Z]+$")
                range_re   = re.compile(".+ ~ .+$")
                list_re    = re.compile("([^,]+,)+[^,]*$")
                re_list = [
                  ["Empty",   empty_re],
                  ["Float",   float_re],
                  ["FUnits",  funits_re],
                  ["Integer", integer_re],
                  ["IUnits",  iunits_re],
                  ["List",    list_re],
                  ["Range",   range_re],
                  ["URL",     url_re],
                ]
    
                # Now sweep through *column_tables*:
                column_triples = list()
                for column_index, column_table in enumerate(column_tables):
                    # Create *column_list* such that the most common value in the columns
                    # come first:
                    column_list = sorted(list(column_table.items()),
                      key=lambda pair: (pair[1], pair[0]), reverse=True)
    
                    # Build up *matches* which is the regular expressions that match best:
                    regex_table = dict()
                    regex_table["String"] = list()
                    total_count = 0
                    for value, count in column_list:
                        #print("Column[{0}]:'{1}': {2} ".format(column_index, value, count))
                        total_count += count
                        match_count = 0
                        for regex_name, regex in re_list:
                            if not regex.match(value) is None:
                                if regex_name in regex_table:
                                    regex_table[regex_name].append((value, count) )
                                else:
                                    regex_table[regex_name] = [ (value, count) ]
    
                                match_count += 1
                        if match_count == 0:
                            regex_table["String"].append( (value, count) )
                    assert total_count == len(data_rows)
    
                    #if not tracing is None:
                    #    print("{0}Column[{1}]: regex_table={2}".
                    #      format(tracing, column_index, regex_table))
    
                    triples = list()
                    for regex_name, pair_list in regex_table.items():
                        total_count = 0
                        value = ""
                        for pair in pair_list:
                            value, count = pair
                            total_count += count
                        triples.append( (total_count, regex_name, value) )
                    triples.sort(reverse=True)
                    column_triples.append(triples)

            # Save some values into *tables_editor* for the update routine:
            tables_editor.import_column_triples = column_triples
            tables_editor.import_headers = headers
            tables_editor.import_rows = data_rows

        # Force an update:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("<=TablesEditor.import_read_button_clicked()\n")
        tables_editor.in_signal = False

    # TablesEditor::import_file_line_changed():
    def import_csv_file_line_changed(self):
        tables_editor = self
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            next_tracing = "" if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.import_csv_file_line_changed()")

            # Make sure *current_table* is up-to-date:
            tables_editor.current_update(tracing=next_tracing)
            current_table = tables_editor.current_table

            # Read *csv_file_name* out of the *import_csv_file_line* widget and stuff into *table*:
            if not current_table is None:
                main_window = tables_editor.main_window
                import_csv_file_line = main_window.import_csv_file_line
                csv_file_name = import_csv_file_line.text()
                current_table.csv_file_name = csv_file_name

            # Force an update:
            tables_editor.update(tracing=next_tracing)

            # Wrap up any requested signal tracing:
            if trace_signals:
                print("<=TablesEditor.import_csv_file_line_changed()\n")
            tables_editor.in_signal = False

    # TablesEditor::import_update():
    def import_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TabledsEditor.import_update".format(tracing))

        # Make sure *current_table* is up to date:
        tables_editor = self
        tables_editor.current_update()
        current_table = tables_editor.current_table

        # Grab some widgets from *tables_editor*:
        main_window          = tables_editor.main_window
        import_bind          = main_window.import_bind
        import_csv_file_line = main_window.import_csv_file_line
        import_read          = main_window.import_read
        import_table         = main_window.import_table

        # Update the *import_csv_file_name* widget:
        csv_file_name = "" if current_table is None else current_table.csv_file_name
        previous_csv_file_name = import_csv_file_line.text()
        if previous_csv_file_name != csv_file_name:
            import_csv_file_line.setText(csv_file_name)

        # Load up *import_table*:
        headers      = tables_editor.import_headers
        #rows         = tables_editor.import_rows
        column_triples = tables_editor.import_column_triples
        import_table.clearContents()
        if not headers is None and not column_triples is None:
            if not tracing is None:
                print("{0}Have column_triples".format(tracing))
            import_table.setRowCount(len(headers))
            import_table.setColumnCount(6)
            # Fill in the left size row headers for *import_table*:
            import_table.setVerticalHeaderLabels(headers)

            assert len(column_triples) == len(headers)
            for column_index, triples in enumerate(column_triples):
                for triple_index, triple in enumerate(triples):
                    assert len(triple) == 3
                    count, name, value = triple

                    if count >= 1:
                        item = QTableWidgetItem("{0} x {1} '{2}'".
                          format(count, name, value))
                        import_table.setItem(column_index, triple_index, item)

                    #print("Column[{0}]: '{1}':{2} => {3}".
                    #  format(column_index, value, count, matches))

                    #print("Column[{0}]: {1}".format(column_index, column_table))
                    #print("Column[{0}]: {1}".format(column_index, column_list))

                    #assert column_index < len(parameters)
                    #parameter = parameters[column_index]
                    #type = "String"
                    #if len(matches) >= 1:
                    #    match = matches[0]
                    #    if match == "Integer":
                    #        type = "Integer"
                    #    elif match == "Float":
                    #        type = "Float"
                    #parameter.type = type


        if not tracing is None:
            print("{0}csv_file_name='{1}' previous='{2}'".
              format(tracing, csv_file_name, previous_csv_file_name))

        # Enable/Disable *import_read* button widget depending upon whether *csv_file_name* exists:
        import_read.setEnabled(os.path.isfile(csv_file_name))
        import_bind.setEnabled(not tables_editor.import_headers is None)

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TabledsEditor.import_update".format(tracing))

    # TablesEditor::parameter_default_changed():
    def parameter_csv_changed(self, new_csv):
        # Verify argument types:
        assert isinstance(new_csv, str)
        
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True

            # Perform any requested *tracing*:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_siginals:
                print("=>TablesEditor.parameter_csv_changed('{0}')".format(new_csv))
        
            # Stuff *new_csv* into *current_parameter* (if possible):
            tables_editor.current_parameter()
            current_parameter = tables_editor.current_parameter
            if not current_parameter is None:
                current_parameter.csv = new_csv

            tables_editor.update(tracing=next_tracing)
            # Wrap up any requested signal tracing:
            if trace_siginals:
                print("=>TablesEditor.parameter_csv_changed('{0}')\n".format(new_csv))
                tables_editor.in_signal = False

    # TablesEditor::parameter_default_changed():
    def parameter_default_changed(self, new_default):
        # Verify argument types:
        assert isinstance(new_default, str)
        
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        tracke_level = 1
        if trace_level >= 1:
            print("=>TablesEditor.parameter_default_changed('{0}')".format(new_default))
        
        # Stuff *new_default* into *current_parameter* (if possible):
        current_parameter = tables_editor.current_parameter
        if not current_parameter is None:
            current_parameter.default = new_default

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=TablesEditor.parameter_default_changed('{0}')\n".format(new_default))

    # TablesEditor::parameter_comment_get():
    def parameter_comment_get(self, parameter, tracing=None):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        text = ""
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            name = "None" if parameter is None else parameter.name
            print("{0}=>parameter_comment_get('{1}')".format(tracing, name))

        # Grab the comment *text* from *parameter*:
        position = 0
        text = ""
        if not parameter is None:
            comments = parameter.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=table_parameter_get('{1}')=>(*, {2})".format(tracing, name, position))
        return text, position

    # TablesEditor::parameter_comment_set():
    def parameter_comment_set(self, parameter, text, position, tracing=None):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            name = "None" if parameter is None else parameter.name
            print("{0}=>parameter_comment_set('{1}', *, {2})".format(tracing, name, position))

        # Stuff *text* into *parameter*:
        if not parameter is None:
            comments = parameter.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)
            comment.lines = text.split('\n')
            comment.position = position

        if not tracing is None:
            main_window = tables_editor.main_window
            comment_text = main_window.parameters_comment_text
            cursor = comment_text.textCursor()
            actual_position = cursor.position()
            print("{0}position={1}".format(tracing, actual_position))

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=parameter_comment_set('{1}', *, {2}')".format(tracing, name, position))

    # TablesEditor::parameter_long_changed():
    def parameter_long_changed(self, new_long_heading):
        # Verify argument types:
        assert isinstance(new_long_heading, str)
        
        # Only do something if we are not already in a signal:
        tables_editor = self
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.parameter_long_changed('{0}')".format(new_long_heading))

            # Update the correct *parameter_comment* with *new_long_heading*:
            current_parameter = tables_editor.current_parameter
            assert isinstance(current_parameter, Parameter)
            parameter_comments = current_parameter.comments
            assert len(parameter_comments) >= 1
            parameter_comment = parameter_comments[0]
            assert isinstance(parameter_comment, ParameterComment)
            parameter_comment.long_heading = new_long_heading

            # Update the user interface:
            tables_editor.update(tracing=next_tracing)

            # Wrap up
            if trace_signals:
                print("<=TablesEditor.parameter_long_changed('{0}')\n".format(new_long_heading))
            tables_editor.in_signal = False

    # TablesEditor::parameters_long_set():
    def parameters_long_set(self, new_long_heading, tracing=None):
        # Verify argument types:
        assert isinstance(new_long_heading, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.parameters_long_set('{1}')".format(tracing, new_long_heading))

        # Stuff *new_long_heading* into *current_parameter*:
        current_parameter = tables_editor.current_parameter
        if current_parameter is None:
            new_long_heading = ""
        else:
            assert isinstance(current_parameter, Parameter)
            current_parameter.long_heading = new_long_heading

        # Now update the user interface to shove *new_long_heading* into the *parameter_long_line*
        # widget:
        main_window = tables_editor.main_window
        long_line = main_window.parameters_long_line
        previous_long_heading = long_line.text()
        if previous_long_heading != new_long_heading:
            long_line.setText(new_long_heading)

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.parameters_long_set('{1}')".format(tracing, new_long_heading))

    # TablesEditor::parameter_new():
    def parameter_new(self, name, tracing= None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        if not tracing is None:
            print("{0}=>TablesEditor.parmeter_new('{1}')".format(tracing, name))

        # Create *new_parameter* named *name*:
        comments = [ ParameterComment(language="EN", long_heading=name, lines=list()) ]
        new_parameter = Parameter(name=name, type="boolean", csv="", comments=comments)

        # Wrap up any requested tracing and return *new_parameter*:
        if not tracing is None:
            print("{0}<=TablesEditor.parmeter_new('{1}')".format(tracing, name))
        return new_parameter

    # TablesEditor::parameter_optional_clicked():
    def parameter_optional_clicked(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.parameter_optional_clicked()")

        current_parameter = tables_editor.current_parameter
        if not current_parameter is None:
            main_window = tables_editor.main_window
            parameter_optional_check = main_window.parameter_optional_check
            optional = parameter_optional_check.isChecked()
            current_parameter.optional = optional

        # Wrap up any requested *tracing*:
        if trace_level >= 1:
            print("=>TablesEditor.parameter_optional_clicked()\n")

    # TablesEditor::parameter_short_changed():
    def parameter_short_changed(self, new_short_heading):
        # Verify argument types:
        assert isinstance(new_short_heading, str)

        # Do not do anything when we are already in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested tracing from *tables_editor* (i.e. *self*):
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.parameter_short_changed('{0}')".format(new_short_heading))

            # Update *current_parameter* to have *new_short_heading*:
            current_parameter = tables_editor.current_parameter
            assert isinstance(current_parameter, Parameter)
            parameter_comments = current_parameter.comments
            assert len(parameter_comments) >= 1
            parameter_comment = parameter_comments[0]
            assert isinstance(parameter_comment, ParameterComment)
            parameter_comment.short_heading = new_short_heading

            # Update the user interface:
            tables_editor.update(tracing=next_tracing)

            # Wrap up any requested tracing:
            if trace_signals:
                print("<=TablesEditor.parameter_short_changed('{0}')\n".format(new_short_heading))
            tables_editor.in_signal = False

    # TablesEditor::parameters_short_set():
    def parameters_short_set(self, new_short_heading, tracing=None):
        # Verify argument types:
        assert isinstance(new_short_heading, str) or new_short_heading is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        if not tracing is None:
            print("{0}=>TablesEditor.parameters_short_set('{1}')".
              format(tracing, new_short_heading))

        # Stuff *new_short_heading* into *current_parameter*:
        current_parameter = tables_editor.current_parameter
        if new_short_heading is None or current_parameter is None:
            new_short_heading = ""
        else:
            current_parameter.short_heading = new_short_heading

        # Now update the user interface to show *new_short_heading* into the *parameter_short_line*
        # widget:
        main_window = tables_editor.main_window
        short_line = main_window.parameters_short_line
        previous_short_heading = short_line.text()
        if previous_short_heading != new_short_heading:
            short_line.setText(new_short_heading)

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.parameters_short_set('{1}')".
              format(tracing, new_short_heading))

    # TablesEditor::parameters_type_changed():
    def parameters_type_changed(self):
        # Perform any requested *signal_tracing* from *tables_editor* (i.e. *self*):
        tables_editor = self
        if tables_editor.in_signal == 0:
            tables_editor.in_signal = True
            current_parameter = tables_editor.current_parameter
            trace_signals     = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.parameters_type_changed('{0}')".
                  format(None if current_parameter is None else current_parameter.name))

            # Load *type* into *current_parameter*:
            if not current_parameter is None:
                main_window = tables_editor.main_window
                parameters_type_combo = main_window.parameters_type_combo
                type = parameters_type_combo.currentText().lower()
                current_parameter.type = type

            # Wrap-up any requested *signal_tracing*:
            if trace_signals:
                print("<=TablesEditor.parameters_type_changed('{0}')\n".
                  format(None if current_parameter is None else current_parameter.name))
            tables_editor.in_signal = False

    # TablesEditor::parameters_update():
    def parameters_update(self, parameter=None, tracing=None):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested tracing from *tables_editor* (i.e. *self*):
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.parameters_update('{1}')".
              format(tracing, "None" if parameter is None else parameter.name))

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor = self

        tables_editor.current_update(tracing=next_tracing)
        current_table = tables_editor.current_table
        current_parameter = tables_editor.current_parameter
        parameter = current_parameter

        # Now we can update the other fields:
        if parameter is None:
            # *parameter* is empty:
            csv      = ""
            is_valid_parameter = False
            default  = ""
            optional = False
            type     = ""
        else:
            # Grab some values from *parameter*:
            csv      = parameter.csv
            is_valid_parameter = True
            default  = parameter.default
            optional = parameter.optional
            type     = parameter.type
            #print("type='{0}' optional={1}".format(type, optional))
        if not tracing is None:
            print("{0}Parameter.name='{1}' csv='{2}'".
              format(tracing, "None" if parameter is None else parameter.name, csv))

        # Grab some widgets from *main_window*:
        main_window    = tables_editor.main_window
        comment_text   = main_window.parameters_comment_text
        csv_line       = main_window.parameters_csv_line
        default_line   = main_window.parameters_default_line
        optional_check = main_window.parameters_optional_check
        table_name     = main_window.parameters_table_name
        type_combo     = main_window.parameters_type_combo

        # The top-level update routine should have already called *TablesEditor*.*current_update*
        # to enusure that *current_table* is up-to-date:
        current_table = tables_editor.current_table
        table_name.setText("" if current_table is None else current_table.name)

        # Set the *csv_line* widget:
        previous_csv = csv_line.text()
        if previous_csv != csv:
            csv_line.setText(csv)
            if not tracing is None:
                print("{0}Set csv to '{1}'".format(tracing, csv))

        # Stuff the values in to the *type_combo* widget:
        type_combo_size = type_combo.count()
        assert type_combo_size >= 1
        type_lower = type.lower()
        match_index = 0
        for type_index in range(type_combo_size):
            type_text = type_combo.itemText(type_index)
            if type_text.lower() == type_lower:
                match_index = type_index
                break
        type_combo.setCurrentIndex(match_index)

        default_line.setText(default)
        optional_check.setChecked(optional)

        # Enable/disable the parameter widgets:
        type_combo.setEnabled(    is_valid_parameter)
        default_line.setEnabled(  is_valid_parameter)
        optional_check.setEnabled(is_valid_parameter)

        # Update the *comments* (if they exist):
        if not parameter is None:
            comments = parameter.comments
            #Kludge for now, select the first comment
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)

            # Update the headings:
            tables_editor.parameters_long_set(comment.long_heading,   tracing=next_tracing)
            tables_editor.parameters_short_set(comment.short_heading, tracing=next_tracing)

            previous_csv = csv_line.text()
            if csv != previous_csv:
                csv_line.setText(csv)

            # Deal with comment text edit area:
            tables_editor.current_comment = comment
            lines = comment.lines
            text = '\n'.join(lines)

            tables_editor.comment_text_set(text, tracing=next_tracing)

        # Changing the *parameter* can change the enumeration combo box, so update it as well:
        #tables_editor.enumeration_update()

        # Update the *tables_combo_edit*:
        tables_editor.parameters_combo_edit.gui_update(tracing=next_tracing)

        if not tracing is None:
            print("{0}<=TablesEditor.parameters_update('{1}')".
              format(tracing, "None" if parameter is None else parameter.name))

    # TablesEditor::quit_button_clicked():
    def quit_button_clicked(self):
        tables_editor = self
        print("TablesEditor.quit_button_clicked() called")
        application = tables_editor.application
        application.quit()

    # TablesEditor::results_update():
    def results_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.results_update()".format(tracing))

        tables_editor = self
        main_window = tables_editor.main_window
        results_table = main_window.results_table        
        results_table.clearContents()
        
        with open("/home/wayne/Downloads/download (1).csv", newline="") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
            rows = list(csv_reader)
            for row_index, row in enumerate(rows):
                if row_index == 0:
                    results_table.setColumnCount(len(row))
                    results_table.setRowCount(len(rows))
                    headers = [header.replace(' ', '\n') for header in row]
                    results_table.setHorizontalHeaderLabels(headers)
                else:
                    for column_index, datum in enumerate(row):
                        assert isinstance(datum, str)
                        datum_item = QTableWidgetItem(datum)
                        if not tracing is None and row_index == 1:
                            print("{0}[{1},{2}]:'{3}'".
                              format(tracing, row_index, column_index, datum))
                        results_table.setRowCount(row_index)
                        results_table.setItem(row_index - 1, column_index, datum_item)
            results_table.resizeRowsToContents()

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.results_update()".format(tracing))

    # TablesEditor::run():
    def run(self):
        # Show the *window* and exit when done:
        tables_editor = self 
        main_window = tables_editor.main_window
        application = tables_editor.application

        main_window.show()
        
        #search_window = tables_editor.search_window
        #search_window.show()

        sys.exit(application.exec_())

    # TablesEditor::save_button_clicked():
    def save_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>TablesEditor.save_button_clicked()")
        current_tables = tables_editor.current_tables

        # Save each *table* in *current_tables*:
        for table in current_tables:
            table.save(tracing=next_tracing)

        searches = tables_editor.searches
        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        xml_lines.append('<Searches>')
        for search in searches:
            search.xml_lines_append(xml_lines, "  ")
        xml_lines.append('</Searches>')
        xml_lines.append("")
        xml_text = '\n'.join(xml_lines)
        searches_xml_file_name = "/tmp/searches.xml"
        with open(searches_xml_file_name, "w") as searches_xml_file:
            searches_xml_file.write(xml_text)

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("=>TablesEditor.save_button_clicked()\n")

    # TablesEditor::schema_update():
    def schema_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing == None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor   = self
        #trace_level = tables_editor.trace_level
        #if trace_level >= 1:
        #    print("=>TablesEditor.schema_update()")
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.schema_update()".format(tracing))

        main_window = tables_editor.main_window
        schema_tabs = main_window.schema_tabs
        schema_tabs_index = schema_tabs.currentIndex()
        if schema_tabs_index == 0:
            tables_editor.tables_update(tracing=next_tracing)
        elif schema_tabs_index == 1:
            tables_editor.import_update(tracing=next_tracing)
        elif schema_tabs_index == 2:
            tables_editor.parameters_update(tracing=next_tracing)
        elif schema_tabs_index == 3:
            tables_editor.enumerations_update(tracing=next_tracing)
        else:
            assert False
        #tables_editor.combo_edit.update()
        #tables_editor.parameters_update(None)
        #tables_editor.search_update()

        # Wrap up any tracing requested by *tables_editor*:
        #if trace_level >= 1:
        #    print("<=TablesEditor.schema_update()")
        if not tracing is None:
            print("{0}=>TablesEditor.schema_update()".format(tracing))

    # TablesEditor::searches_load():
    def searches_load(self, xml_file_name, tracing=None):
        # Veify argument types:
        assert isinstance(xml_file_name, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.searches_load('{1})".format(tracing, xml_file_name))

        # Read in *xml_file_name* (if it exists):
        if os.path.isfile(xml_file_name):
            with open(xml_file_name) as xml_file:
                xml_text = xml_file.read()

            # Parse *xml_text* into *searches_tree*:
            searches_tree = etree.fromstring(xml_text)
            assert isinstance(searches_tree, etree._Element)
            assert searches_tree.tag == "Searches"

            # Dig dow the next layer of *searches_tree*
            search_trees = list(searches_tree)

            # Grab *searches* from *tables_editor* (i.e. *self*) and empty it out:
            tables_editor = self
            searches = tables_editor.searches
            assert isinstance(searches, list)
            del searches[:]

            # Parse each *search_tree* in *search_trees*:
            for search_tree in search_trees:
                assert isinstance(search_tree, etree._Element)
                search = Search(search_tree=search_tree,
                    tables=tables_editor.tables, tracing=next_tracing)
                searches.append(search)
            
            # Set *current_search*
            tables_editor.current_search = searches[0] if len(searches) >= 1 else None

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.searches_load('{1})".format(tracing, xml_file_name))

    # TablesEditor::search_new():
    def search_new(self, name, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.search_new('{1}')".format(tracing, name))

        tables_editor = self
        tables_editor.current_update()
        current_table = tables_editor.current_table

        # Create *serach* with an empty English *serach_comment*:
        search_comment = SearchComment(language="EN", lines=list())
        search_comments = [ search_comment ]
        search = Search(name=name, comments=search_comments, table=current_table)
        search.filters_update()

        # Wrap up any requested *tracing* and return *search*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}<=TablesEditor.search_new('{1}')".format(tracing, name))
        return search

    # TablesEditor::search_update():
    def search_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.search_update(*)".format(tracing))

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor = self
        tables_editor.current_update(tracing=next_tracing)

        # Grab the *current_table* *Table* object from *tables_editor* (i.e. *self*.)
        # Grab the *seach_table* widget from *tables_editor* as well:
        current_table = tables_editor.current_table
        main_window = tables_editor.main_window
        search_table = main_window.search_table
        assert isinstance(search_table, QTableWidget)

        # Step 1: Empty out *search_table*:
        search_table.clearContents()
        search_table.setHorizontalHeaderLabels(["Parameter", "Use", "Criteria"])

        # Dispatch on whether *current_table* exists or not:
        if current_table is None:
            # We have no *current_table*, so show an empty search table:
            #search_table.setHorizontalHeaderLabels([])
            #search_table.setColumnCount(0)
            #data_table.setRowCount(0)
            pass
        else:
            # *current_table* is active, so fill in *search_table*:
            assert isinstance(current_table, Table)
            header_labels = current_table.header_labels_get()
            #print("Header_labels={0}".format(header_labels))
            search_table.setColumnCount(3)
            search_table.setRowCount(len(header_labels))

            # Now convert eacch *parameter* in *parameters into a row in *search_table*:
            parameters = current_table.parameters
            assert len(parameters) == len(header_labels)
            for parameter_index, parameter in enumerate(parameters):
                # Create the header label in the first column:
                header_item = QTableWidgetItem(header_labels[parameter_index])
                header_item.setData(Qt.UserRole, parameter)
                search_table.setItem(parameter_index, 0, header_item)

                # Create the use [] check box in the second column:
                use_item = QTableWidgetItem("")
                assert isinstance(use_item, QTableWidgetItem)
                #print(type(use_item))
                #print(use_item.__class__.__bases__)
                flags = use_item.flags()
                use_item.setFlags(flags | Qt.ItemIsUserCheckable)
                check_state = Qt.Unchecked
                if parameter.use:
                    check_state = Qt.Checked
                use_item.setCheckState(check_state)
                #use_item.itemChanged.connect(
                #  partial(TablesEditor.search_use_clicked, tables_editor, use_item, parameter))
                parameter.use = False
                search_table.setItem(parameter_index, 1, use_item)
                search_table.cellClicked.connect(
                  partial(TablesEditor.search_use_clicked, tables_editor, use_item, parameter))

                #if parameter.type == "enumeration":
                #    #combo_box = QComboBox()
                #    #combo_box = QTableWidgetItem("")
                #    combo_box = QComboBox()
                #    assert isinstance(combo_box, QWidget)
                #    model = QStandardItemModel(1, 1)
                #    enumerations = parameter.enumerations
                #    for enumeration_index, enumeration in enumerate(enumerations):
                #        assert isinstance(enumeration, Enumeration)
                #        #comments = enumeration.comments
                #        #comments_size = len(comments)
                #        #assert comments_size >= 1
                #        #comment = comments[0]
                #        #combo_box.addItem(enumeration.name, userData=enumeration)
                #        item = QStandardItem(enumeration.name)
                #        combo_box.setItem(enumeration_index, 0, item)
                #    search_table.setCellWidget(parameter_index, 2, combo_box)
                #else:
                criteria_item = QTableWidgetItem("")
                criteria_item.setData(Qt.UserRole, parameter)
                search_table.setItem(parameter_index, 2, criteria_item)

        # Update the *search_combo_edit*:
        tables_editor.search_combo_edit.gui_update(tracing=next_tracing)

        if not tracing is None:
            print("{0}<=TablesEditor.search_update(*)".format(tracing))

    # TablesEditor::search_comment_get():
    def search_comment_get(self, search, tracing=None):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>table_comment_get('{1}')".format(tracing, search.name))

        # Extract the comment *text* from *search*:
        if search is None:
            text = ""
            position = 0
        else:
            comments = search.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, SearchComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=table_comment_get('{1}')".format(tracing, search.name))
        return text, position

    # TablesEditor::search_comment_set():
    def search_comment_set(self, search, text, position, tracing=None):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.search_comment_set('{1}')".
              format(tracing, "None" if search is None else search.name))

        # Stuff *text* and *position* into *search*:
        if not search is None:
            comments = search.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, SearchComment)
            comment.lines = text.split('\n')
            comment.position = position

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.search_comment_set('{1}')".
              format(tracing, "None" if search is None else search.name))

    # TablesEditor::searches_table_changed():
    def searches_table_changed(self, new_text):
        # Verify argument types:
        assert isinstance(new_text, str)

        # Do nothing if we are already in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True
            # Perform any requested *tracing*:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.searches_table_changed('{0}')".format(new_text))

            # Make sure *current_search* is up to date:
            tables_editor = self
            tables_editor.current_update(tracing=next_tracing)
            current_search = tables_editor.current_search

            # Find the *table* that matches *new_text* and stuff it into *current_search*:
            if not current_search is None:
                match_table = None
                tables = tables_editor.tables
                for table_index, table in enumerate(tables):
                    assert isinstance(table, Table)
                    if table.name == new_text:
                        match_table = table
                        break
                current_search.table_set(match_table, tracing=next_tracing)

            # Wrap up any requested *tracing*:
            if trace_signals:
                print("<=TablesEditor.searches_table_changed('{0}')\n".format(new_text))
            tables_editor.in_signal = False

    # TablesEditor::searches_update():
    def searches_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.searches_update()".format(tracing))

        # Make sure that *current_search* is up to date:
        tables_editor = self
        tables_editor.current_update(tracing=next_tracing)
        current_search = tables_editor.current_search        

        # Update *searches_combo_edit*:
        searches_combo_edit = tables_editor.searches_combo_edit
        searches_combo_edit.gui_update(tracing=next_tracing)

        # Next: Update the table options:
        search_table = None if current_search is None else current_search.table
        tables = tables_editor.tables
        main_window = tables_editor.main_window
        searches_table_combo = main_window.searches_table_combo
        searches_table_combo.clear()
        if len(tables) >= 1:
            match_index = -1
            for table_index, table in enumerate(tables):
                assert isinstance(table, Table)
                searches_table_combo.addItem(table.name)
                if table is search_table:
                    match_index = table_index
            if match_index >= 0:
                searches_table_combo.setCurrentIndex(match_index)

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.searches_update()".format(tracing))

    # TablesEditor::tab_changed():
    def tab_changed(self, new_index):
        # Verify argument types:
        assert isinstance(new_index, int)

        # Note: *new_index* is only used for debugging.

        # Only deal with this siginal if we are not already *in_signal*:
        tables_editor = self
        if not tables_editor.in_signal:
            # Disable  *nested_signals*:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.tab_changed(*, {0})".format(new_index))

            # Perform the update:
            tables_editor.update(tracing=next_tracing)

            # Wrap up any requested signal tracing and restore *in_signal*:
            if trace_signals:
                print("<=TablesEditor.tab_changed(*, {0})\n".format(new_index))
            tables_editor.in_signal = False

    # TablesEditor::table_comment_get():
    def table_comment_get(self, table, tracing=None):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(tracing, str) or tracing is None

        curosr = 0
        text = ""
        # Perform any requested *tracing*:
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>table_comment_get('{1}')".format(tracing, table.name))

        # Extract the comment *text* from *table*:
        if not table is None:
            comments = table.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, TableComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=table_comment_get('{1}')".format(tracing, table.name))
        return text, position

    # TablesEditor::table_comment_set():
    def table_comment_set(self, table, text, position, tracing=None):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>table_comment_set('{1}')".format(tracing, table.name))

        # Stuff *text* into *table*:
        if not table is None:
            comments = table.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, TableComment)
            comment.lines = text.split('\n')
            comment.position = position

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=table_comment_set('{1}')".format(tracing, table.name))

    # TablesEditor::table_new():
    def table_new(self, name, tracing = None):
        # Verify argument types:
        assert isinstance(name, str)

        # Perform an requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.table_new('{1}')".format(tracing, name))

        file_name = "{0}.xml".format(name)
        table_comment = TableComment(language="EN", lines=list())
        table = Table(file_name=file_name,
          name=name, comments=[table_comment], parameters=list(), csv_file_name="")

        # Wrap up any requested *tracing* and return table:
        if not tracing is None:
            print("{0}<=TablesEditor.table_new('{1}')".format(tracing, name))
        return table

    # TablesEditor::table_setup():
    def table_setup(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested from *tables_editor* (i.e. *self*):
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.table_setup(*)".format(tracing))

        # Grab the *table* widget and *current_table* from *tables_editor* (i.e. *self*):
        tables_editor = self
        main_window = tables_editor.main_window
        data_table = main_window.data_table
        assert isinstance(data_table, QTableWidget)
        current_table = tables_editor.current_table

        # Dispatch on *current_table* depending upon whether it exists or not:
        if current_table is None:
            # *current_table* is empty, so we initialize the *table* widget to be empty:
            data_table.setHorizontalHeaderLabels([])
            data_table.setColumnCount(0)
            data_table.setRowCount(0)
        else:
            # *current_table* is valid, so we extract the *header_labels* and attach them to the
            # *table* widget:
            assert isinstance(current_table, Table)
            header_labels = current_table.header_labels_get()
            data_table.setHorizontalHeaderLabels(header_labels)
            data_table.setColumnCount(len(header_labels))
            data_table.setRowCount(1)

        # Wrap up any requested tracing:
        if not tracing is None:
            print("{0}=>TablesEditor.table_setup(*)".format(tracing))

    # TablesEditor::tables_update():
    def tables_update(self, table=None, tracing=None):
        # Verify argument types:
        assert isinstance(table, Table) or table is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor   = self

        # Perform any requested *trracing*:
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.tables_update()".format(tracing))
        
        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update(tracing=next_tracing)

        # Update the *tables_combo_edit*:
        tables_editor.tables_combo_edit.gui_update(tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if not tracing is None:
            print("{0}<=TablesEditor.tables_update()".format(tracing))

    # TablesEditor::update():
    def update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor   = self
        #trace_level = tables_editor.trace_level
        #if trace_level >= 1:
        #    print("=>TablesEditor.update()")
        next_tracing = None if tracing is None else tracing + " "
        if not tracing is None:
            print("{0}=>TablesEditor.update()".format(tracing))

        # Only update the visible tabs based on *root_tabs_index*:
        main_window = tables_editor.main_window
        root_tabs = main_window.root_tabs
        root_tabs_index = root_tabs.currentIndex()
        if root_tabs_index == 0:
            tables_editor.schema_update(tracing=next_tracing)
        elif root_tabs_index == 1:
            tables_editor.find_update(tracing=next_tracing)
        else:
            assert False, "Illegal tab index: {0}".format(root_tabs_index)
        
        # Wrap up any tracing requested by *tables_editor*:
        #if trace_level >= 1:
        #    print("<=TablesEditor.update()")
        if not tracing is None:
            print("{0}<=TablesEditor.update()".format(tracing))

class XXXAttribute:
    def __init__(self, name, type, default, optional, documentations, enumerates):
        # Verify argument types:
        assert isinstance(name, str) and len(name) > 0
        assert isinstance(type, str)
        assert isinstance(default, str) or default == None
        assert isinstance(optional, bool)
        assert isinstance(documentations, list)
        for documentation in documentations:
            assert isinstance(documentation, Documentation)
        assert isinstance(enumerates, list)
        for enumerate in enumerates:
            assert isinstance(enumerate, Enumerate)

        # Stuff arguments into *attribute* (i.e. *self*):
        attribute                = self
        attribute.name           = name
        attribute.type           = type
        attribute.default        = default        
        attribute.enumerates     = enumerates
        attribute.optional       = optional
        attribute.documentations = documentations

    def __eq__(self, attribute2):
        # Verify argument types:
        assert isinstance(attribute2, Attribute)
        attribute1 = self

        is_equal = (
          attribute1.name == attribute2.name and
          attribute1.type == attribute2.type and
          attribute1.default == attribute2.default and
          attribute1.optional == attribute2.optional)

        documentations1 = attribute1.documentations
        documentations2 = attribute1.documentations
        if len(documentations1) == len(documentations2):
            for index in range(len(documentations1)):
                documentation1 = documentations1[index]
                documentation2 = documentations2[index]
                if documentation1 != documentation2:
                    is_result = False
                    break
        else:
            is_equal = False
        return is_equal

    def copy(self):
        attribute = self

        new_documentations = list()
        for documentation in attribute.documentations:
            new_documentations.append(documentation.copy())
        new_attribute = Attribute(attribute.name,
          attribute.type, attribute.default, attribute.optional, new_documentations, list())
        return new_attribute

class XXXDocumentation:
    def __init__(self, language, xml_lines):
        # Verify argument types:
        assert isinstance(language, str)
        assert isinstance(xml_lines, list)
        for line in xml_lines:
           assert isinstance(line, str)

        # Load arguments into *documentation* (i.e. *self*):
        documentation          = self
        documentation.language = language
        documentation.xml_lines    = xml_lines

    def __equ__(self, documentation2):
        # Verify argument types:
        assert isinstance(documentation2, Documenation)

        documentation1 = self
        is_equal = documentation1.langauge == documentation2.language

        # Determine wheter *xml_lines1* is equal to *xml_lines2*:
        xml_lines1 = documentation1.xml_lines
        xml_lines2 = documentation2.xml_lines
        if len(xml_lines1) == len(line2):
            for index, line1 in enumerate(xml_lines1):
                line2 = xml_lines2[index]
                if line1 != line2:
                    is_equal = False
                    break
        else:
            is_equal = False
        return is_equal

    def copy(self):
        documentation = self
        new_documentation = Documentation(documentation.language, list(documentation.xml_lines))
        return new_documentation

class XEnumeration:
    """ An *Enumeration* object represents a single enumeration possibility for an attribute.
    """

    # Class: Enumeration
    def __init__(self, **arguments_table):
        """
        """
        # Verify argument types:
        assert isinstance(name, str, documents)
        assert isinstace(documentations, list)
        for documentation in documentations:
            assert isinstance(documentation, Documentation)
        
        # Stuff *name* value into *enumeration* (i.e. *self*):
        enumeration.name = name
        enumeration.documents = documents

class XXXSchema:
    def __init__(self, schema_text=None):
        # Veritfy argument types:
        assert isinstance(schema_text, str) or schema_text == None

        # Create an empty *schema*:
        target_name_space = ""
        attributes = list()
        if isinstance(schema_text, str):
            # Convert *schema_text* from XML format into *schema_root* (an *etree._element*):
            schema_root = etree.fromstring(schema_text)
            assert isinstance(schema_root, etree._Element)

            xml_name_space = "{http://www.w3.org/XML/1998/namespace}"

            assert schema_root.tag.endswith("}schema")
            attributes_table = schema_root.attrib
            assert "targetNamespace" in attributes_table
            target_name_space = attributes_table["targetNamespace"]
            xsd_elements = list(schema_root)

            assert len(xsd_elements) == 1
            table_element = xsd_elements[0]
            assert isinstance(table_element, etree._Element)
            table_element_name = table_element.tag
            assert table_element_name.endswith("}element")

            table_complex_types = list(table_element)
            assert len(table_complex_types) == 1
            table_complex_type = table_complex_types[0]
            assert isinstance(table_complex_type, etree._Element)
            assert table_complex_type.tag.endswith("}complexType")

            sequences = list(table_complex_type)
            assert len(sequences) == 1
            sequence = sequences[0]
            assert isinstance(sequence, etree._Element)
            assert sequence.tag.endswith("}sequence"), sequence.tag

            item_elements = list(sequence)
            assert len(item_elements) == 1
            item_element = item_elements[0]
            assert isinstance(item_element, etree._Element)
            assert item_element.tag.endswith("}element")
        
            item_complex_types = list(item_element)
            assert len(item_complex_types) == 1
            item_complex_type = item_complex_types[0]
            assert isinstance(item_complex_type, etree._Element)
            assert item_complex_type.tag.endswith("}complexType")

            item_attributes = list(item_complex_type)
            assert len(item_attributes) >= 1
            for attribute_child in item_attributes:
                # Extract the attributes of `<attribute ...>`:
                assert attribute_child.tag.endswith("}attribute")
                attributes_table = attribute_child.attrib
                assert "name" in attributes_table
                name = attributes_table["name"]
                #assert "type" in attributes_table  # Not present for an enumeration
                type = attributes_table["type"]
                assert type in ("xs:boolean",
                  "xs:enumeration", "xs:float", "xs:integer", "xs:string")
                optional = True
                if "use" in attributes_table:
                    use = attributes_table["use"]
                    assert use == "required"
                    optional = False
                default = None
                if "default" in attributes_table:
                    default = attributes_table["default"]
                #print("default={0}".format(default))

                annotation_children = list(attribute_child)
                assert len(annotation_children) == 1
                annotation_child = annotation_children[0]
                assert isinstance(annotation_child, etree._Element)

                # Iterate over *documentation_children* and build of a list of *Docuemtation*
                # objects in *documentations*:
                documentations = list()
                documentations_children = list(annotation_child)
                for documentation_child in documentations_children:
                    # Verify that that *documentation_child* has exactly on attribute named `lang`:
                    assert isinstance(documentation_child, etree._Element)
                    attributes_table = documentation_child.attrib
                    assert len(attributes_table) == 1
                    #print("attributes_table=", attributes_table)
                    key = xml_name_space + "lang"
                    assert key in attributes_table

                    # Extract the *language* attribute value:
                    language = attributes_table[key]

                    # Grab the *text* from *documentation_children*:
                    text = documentation_child.text.strip()
                    xml_lines = [line.strip().replace("<", "&lt;") for line in text.split('\n')]

                    # Create the *documentation* and append to *documentations*:
                    documentation = Documentation(language, xml_lines)
                    documentations.append(documentation)

                # Create *attribute* and append to *attributes*:
                enumerates = list()
                attribute = Attribute(name, type, default, optional, documentations, enumerates)
                attributes.append(attribute)

        # Construct the final *schema* (i.e. *self*):
        schema = self
        schema.target_name_space = target_name_space
        schema.attributes = attributes

    def __eq__(self, schema2):
        assert isinstance(schema2, Schema)
        schema1 = self
        attributes1 = schema1.attributes
        attributes2 = schema2.attributes
        is_equal = len(attributes1) == len(attributes2)
        if is_equal:
            for index, attribute1 in enumerate(attributes1):
                attribute2 = attributes2[index]
                if attribute1 != attribute2:
                    is_equal = False
                    break
        return is_equal

    def copy(self):
        schema = self
        new_schema = Schema()
        new_schema.target_name_space = schema.target_name_space
        new_schema_attributes = new_schema.attributes
        assert len(new_schema_attributes) == 0
        for attribute in schema.attributes:
            new_schema_attributes.append(attribute.copy())
        return new_schema        

    def to_string(self):
        schema = self
        attributes        = schema.attributes
        target_name_space = schema.target_name_space

        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        xml_lines.append('<xs:schema')
        xml_lines.append(' targetNamespace="{0}"'.format(target_name_space))
        xml_lines.append(' xmlns:xs="{0}"'.format("http://www.w3.org/2001/XMLSchema"))
        xml_lines.append(' xmlns="{0}">'.
          format("file://home/wayne/public_html/projects/manufactory_project"))
        xml_lines.append('  <xs:element name="{0}">'.format("drillBits"))
        xml_lines.append('    <xs:complexType>')
        xml_lines.append('      <xs:sequence>')
        xml_lines.append('        <xs:element name="{0}">'.format("drillBit"))
        xml_lines.append('          <xs:complexType>')
        
        for attribute in attributes:
            # Unpack the values from *attribute*:
            name           = attribute.name
            type           = attribute.type
            default        = attribute.default
            optional       = attribute.optional
            documentations = attribute.documentations

            xml_lines.append('            <xs:attribute')
            xml_lines.append('             name="{0}"'.format(name))
            if isinstance(default, str):
                xml_lines.append('             default="{0}"'.format(default))
            if not optional:
                xml_lines.append('             use="required"')
            xml_lines.append('             type="{0}">'.format(type))
            xml_lines.append('              <xs:annotation>')
            for document in documentations:
                language = document.language
                documentation_xml_lines    = document.xml_lines
                xml_lines.append('                <xs:documentation xml:lang="{0}">'.format(language))
                for documentation_line in documentation_xml_lines:
                    xml_lines.append('                  {0}'.format(documentation_line))
                xml_lines.append('                </xs:documentation>')
            xml_lines.append('              </xs:annotation>')
            xml_lines.append('            </xs:attribute>')
        xml_lines.append('          </xs:complexType>')
        xml_lines.append('        </xs:element>')
        xml_lines.append('      </xs:sequence>')
        xml_lines.append('    </xs:complexType>')
        xml_lines.append('  </xs:element>')
        xml_lines.append('</xs:schema>')

        xml_lines.append("")
        text = '\n'.join(xml_lines)
        return text

class CheckableComboBox(QComboBox):
    # once there is a checkState set, it is rendered
    # here we assume default Unchecked
    def addItem(self, item):
        super(CheckableComboBox, self).addItem(item)
        item = self.model().item(self.count()-1,0)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        item.setCheckState(QtCore.Qt.Unchecked)

    def itemChecked(self, index):
        item = self.model().item(i,0)
        return item.checkState() == QtCore.Qt.Checked

if __name__ == "__main__":
    main()


# https://stackoverflow.com/questions/5226091/checkboxes-in-a-combobox-using-pyqt?rq=1
# https://stackoverflow.com/questions/24961383/how-to-see-the-value-of-pyside-qtcore-qt-itemflag
# /usr/local/lib/python3.6/dist-packages/PySide2/examples/widgets/itemviews/stardelegate
# https://stackoverflow.com/questions/8422760/combobox-of-checkboxes


# Qt Designer application Notes:
# * Use grid layouts for everything.  This easier said than done since the designer
#   user interface is kind of clunky:
#   1. Just drop one or more widgets into the area.
#   2. Using the tree view, select the widgets using left mouse button and [Control] key.
#   3. Using right mouse button, get a drop-down, and set the grid layout.
#   4. You are not done until all the widgets with layouts are grids with no red circle
#      that indicate that now layout is active.
#
# Notes on using tab widgets:
# * Tabs are actually named in the parent tab widget (1 level up.)
# * To add a tab, hover the mouse over an existing tab, right click mouse, and select
#   Insert page.

#!/usr/bin/env python3

#<-------------------------------------------- 100 characters ------------------------------------>|

# Coding standards:
# * In general, the coding guidexml_lines PEP 8 are used.
# * All code and docmenation xml_lines must be on xml_lines of 100 characters or less.
# * Comments:
#   * All code comments are written in [Markdown](https://en.wikipedia.org/wiki/Markdown).
#   * Code is organized into blocks that are preceeded by comment that explains the code block.
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
import os
import sys
import xmlschema
import lxml.etree as etree
import copy
from functools import partial
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QWidget, QComboBox, QLineEdit, QPushButton
from PySide2.QtCore import (QFile, QByteArray, QTimer)
#from PySide2.QtNetwork import (QUdpSocket, QHostAddress)

class Comment:
    def __init__(self, tag_name, **arguments_table):
        # Verify argument types:
        assert isinstance(tag_name, str) \
          and tag_name in ("EnumerationComment", "ParameterComment", "TableComment")
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
        comment.language = language
        comment.lines = lines
        #print("Comment(): comment.lines=", tag_name, lines)

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

    def __eq__(self, enumeration2):
        # Verify argument types:
        assert isinstance(enumeration2, Enumeration)
        
        enumeration1 = self
        name_equal     = (enumeration1.name     == enumeration2.name)
        comments_equal = (enumeration1.comments == enumeration2.comments)
        return name_equal and comments_equal

    def xml_lines_append(self, xml_lines):
        enumeration = self
        xml_lines.append('        <Enumeration name="{0}">'.format(enumeration.name))
        for comment in enumeration.comments:
            comment.xml_lines_append(xml_lines)
        xml_lines.append('        </Enumeration>')

class EnumerationComment(Comment):
    def __init__(self, **arguments_table):
        #print("=>EnumerationComment.__init__()")
        enumeration_comment = self
        super().__init__("EnumerationComment", **arguments_table)
        assert isinstance(enumeration_comment.language, str)
        assert isinstance(enumeration_comment.lines, list)

    def __equ__(self, enumeration_comment2):
        assert isinstance(enumeration_comment2, EnumerationComment)
        return super.__eq__(enumeration_comment2)

    def xml_lines_append(self, xml_lines):
        #print("=>EnumerationComment.xml_lines_append()")
        enumeration_comment = self
        xml_lines.append('          <EnumerationComment language="{0}">'.
          format(enumeration_comment.language))
        for line in enumeration_comment.lines:
            xml_lines.append('            {0}'.format(line))
        xml_lines.append('          </EnumerationComment>')

class Parameter:
    def __init__(self, **arguments_table):
        is_parameter_tree = "parameter_tree" in arguments_table
        if is_parameter_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["parameter_tree"], etree._Element)
        else:
            assert "name" in arguments_table
            assert "type" in arguments_table
            assert "comments" in arguments_table
            arguments_count = 3
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
            default = arguments_table["defualt"] if "default" in arguments_table else None
            optional = arguments_table["optional"] if "optional" in arguments_table else False
            comments = arguments_table["comments"] if "comments" in arguments_table else list()
            enumerations = \
              arguments_table["enumerations"] if "enumerations" in arguments_table else list()

        # Load values into *parameter* (i.e. *self*):
        super().__init__()
        parameter = self
        parameter.name = name
        parameter.default = default
        parameter.type = type
        parameter.optional = optional
        parameter.comments = comments
        parameter.enumerations = enumerations
        #print("Paramter('{0}'): optional={1}".format(name, optional))

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

    def ui_lines_append(self, ui_lines, row):
        # Verify argument_types:
        assert isinstance(ui_lines, list)
        assert isinstance(row, int) and row >= 2

        parameter = self
        name = parameter.name
        comments = parameter.comments
        assert len(comments) >= 1
        comment = comments[0]
        long_heading = comment.long_heading

        # Output the *long_heading* radio button:
        ui_lines.append('     <item row="{0}" column="0">'.format(row))
        ui_lines.append('      <widget class="QRadioButton" name="{0}_radio_button">'.format(name))
        ui_lines.append('       <property name="text">')
        ui_lines.append('        <string>{0}</string>'.format(long_heading))
        ui_lines.append('       </property>')
        ui_lines.append('      </widget>')
        ui_lines.append('     </item>')

        # Output the use check box:
        ui_lines.append('     <item row="{0}" column="1">'.format(row))
        ui_lines.append('      <widget class="QCheckBox" name="{0}_check_box">'.format(name))
        ui_lines.append('       <property name="text">')
        ui_lines.append('        <string/>')
        ui_lines.append('       </property>')
        ui_lines.append('      </widget>')
        ui_lines.append('     </item>')

        # Output the criteria widget (which can be either a line edit or combo box widget:
        ui_lines.append('     <item row="{0}" column="2">'.format(row))
        if parameter.type == "enumeration":
            ui_lines.append('      <widget class="QComboBox" name="{0}_combo_box">'.format(name))
            enumerations = parameter.enumerations
            for enumeration in enumerations:
                comments = enumeration.comments
                assert len(comments) >= 1
                comment = comments[0]
                assert isinstance(comment, EnumerationComment)
                #FIXME Enumeration Comment needs a translated name:
                name = enumeration.name
                ui_lines.append('       <item>')
                ui_lines.append('        <property name="text">')
                ui_lines.append('         <string>{0}</string>'.format(name))
                ui_lines.append('        </property>')
                ui_lines.append('       </item>')
            ui_lines.append('      </widget>')
        else:
            ui_lines.append('      <widget class="QLineEdit" name="{0}_line_edit"/>'.format(name))
        ui_lines.append('     </item>')

    def xml_lines_append(self, xml_lines):
        assert isinstance(xml_lines, list)
        assert isinstance(xml_lines, list)

        # Grab some values from *parameter* (i.e. *self*):
        parameter = self
        default = parameter.default
        optional = parameter.optional

        # Start the *parameter* XML add in *optional* and *default* if needed:
        xml_line = '    <Parameter name="{0}" type="{1}"'.format(parameter.name, parameter.type)
        if optional:
            xml_line += ' optional="true"'
        if not default is None:
            xml_line += ' default="{0}"'.format(default)
        xml_line += '>'
        xml_lines.append(xml_line)
        
        # Append all of the comments*:
        comments = parameter.comments
        for comment in comments:
            xml_lines.append('      <ParameterComments>')
            comment.xml_lines_append(xml_lines)
            xml_lines.append('      </ParameterComments>')

        # Append all of the *enumerations*:
        enumerations = parameter.enumerations
        if len(enumerations) >= 1:
            xml_lines.append('      <Enumerations>')
            for enumeration in enumerations:
                enumeration.xml_lines_append(xml_lines)
            xml_lines.append('      </Enumerations>')

        # Close out the *parameter*:
        xml_lines.append('    </Parameter>')

class ParameterComment(Comment):
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

class Table:
    def __init__(self, **arguments_table):
        # Verify argument types:
        assert "file_name" in arguments_table and isinstance(arguments_table["file_name"], str)
        is_table_tree = "table_tree" in arguments_table
        if is_table_tree:
            assert len(arguments_table) == 2
            assert "table_tree" in arguments_table and \
              isinstance(arguments_table["table_tree"], etree._Element)
        else:
            assert len(arguments_table) == 3
            assert "name" in arguments_table and isinstance(arguments_table["name"], str)
            assert "comments" in arguments_table
            comments = arguments_table["comments"]
            for comment in comments:
                assert isinstnace(comment, TableComment)
            assert "parameters" in arguments_table
            parameters = arguments_table["parameters"]
            for parameter in parmeters:
                assert isinstance(parameter, paraemeters)
        
        if is_table_tree:
            table_tree = arguments_table["table_tree"]
            assert table_tree.tag == "Table"
            attributes_table = table_tree.attrib

            # Extract *name*:
            assert "name" in attributes_table
            name = attributes_table["name"]
            file_name = arguments_table["file_name"]

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
            file_name = arguments_table["file_name"]
            name = arguments_table["name"]
            comments = arguments_table["comments"]
            parameters = arguments_table["parameters"]

        # Load up *table* (i.e. *self*):
        table = self
        table.file_name = arguments_table["file_name"]
        table.name = name
        table.comments = comments
        table.parameters = parameters

    def __eq__(self, table2):
        # Verify argument types:
        assert isinstance(table2, Table)

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

    def to_ui_string(self):
        table = self
        ui_lines = list()
        table.ui_lines_append(ui_lines)
        ui_text = '\n'.join(ui_lines)
        return ui_text

    def ui_lines_append(self, ui_lines):
        # Verify argument types:
        assert isinstance(ui_lines, list)

        table = self
        parameters = table.parameters
        parameters_size = len(parameters)

        # Output the initial plate:
        ui_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        ui_lines.append('<ui version="4.0">')
        ui_lines.append(' <class>MainWindow</class>')
        ui_lines.append(' <widget class="QMainWindow" name="search_window">')
        ui_lines.append('  <property name="geometry">')
        ui_lines.append('   <rect>')
        ui_lines.append('    <x>0</x>')
        ui_lines.append('    <y>0</y>')
        ui_lines.append('    <width>800</width>')
        ui_lines.append('    <height>600</height>')
        ui_lines.append('   </rect>')
        ui_lines.append('  </property>')
        ui_lines.append('  <property name="windowTitle">')
        ui_lines.append('   <string>Parametric Search</string>')
        ui_lines.append('  </property>')

        # Output the grid box:
        ui_lines.append('  <widget class="QWidget" name="centralwidget">')
        ui_lines.append('   <widget class="QWidget" name="gridLayoutWidget">')
        ui_lines.append('    <property name="geometry">')
        ui_lines.append('     <rect>')
        ui_lines.append('      <x>0</x>')
        ui_lines.append('      <y>0</y>')
        ui_lines.append('      <width>781</width>')
        ui_lines.append('      <height>531</height>')
        ui_lines.append('     </rect>')
        ui_lines.append('    </property>')

        # Output the fixed widgets:
        ui_lines.append('    <layout class="QGridLayout" name="gridLayout">'
                        ' rowstretch="0,0,{0}1" columnstretch="0,0,1"'.
                        format("0," * parameters_size) )

        # Output row 0 buttons:
        ui_lines.append('     <item row="0" column="2">')
        ui_lines.append('      <widget class="QPushButton" name="dismiss_button">')
        ui_lines.append('       <property name="text">')
        ui_lines.append('        <string>Dismiss</string>')
        ui_lines.append('       </property>')
        ui_lines.append('      </widget>')
        ui_lines.append('     </item>')
        ui_lines.append('     <item row="0" column="1">')
        ui_lines.append('      <widget class="QPushButton" name="search_button">')
        ui_lines.append('       <property name="text">')
        ui_lines.append('        <string>Search</string>')
        ui_lines.append('       </property>')
        ui_lines.append('      </widget>')
        ui_lines.append('     </item>')
        ui_lines.append('     <item row="0" column="0">')
        ui_lines.append('      <widget class="QPushButton" name="clear_button">')
        ui_lines.append('       <property name="text">')
        ui_lines.append('        <string>Clear</string>')
        ui_lines.append('       </property>')
        ui_lines.append('      </widget>')
        ui_lines.append('     </item>')

        # Output row 1 headers:
        ui_lines.append('     <item row="1" column="2">')
        ui_lines.append('      <widget class="QLabel" name="label">')
        ui_lines.append('       <property name="text">')
        ui_lines.append('        <string>Criteria</string>')
        ui_lines.append('       </property>')
        ui_lines.append('      </widget>')
        ui_lines.append('     </item>')
        ui_lines.append('     <item row="1" column="1">')
        ui_lines.append('      <widget class="QLabel" name="use_label">')
        ui_lines.append('       <property name="text">')
        ui_lines.append('        <string>Use</string>')
        ui_lines.append('       </property>')
        ui_lines.append('      </widget>')
        ui_lines.append('     </item>')
        ui_lines.append('     <item row="1" column="0">')
        ui_lines.append('      <widget class="QLabel" name="parameter_label">')
        ui_lines.append('       <property name="text">')
        ui_lines.append('        <string>Parameter</string>')
        ui_lines.append('       </property>')
        ui_lines.append('      </widget>')
        ui_lines.append('     </item>')

        # Ouput one row per *parameter* in *parameters*:
        for index, parameter in enumerate(parameters):
            parameter.ui_lines_append(ui_lines, index + 2)

        # Output the final text edit:
        ui_lines.append('     <item row="{0}" column="0" colspan="3">'.format(parameters_size + 3))
        ui_lines.append('      <widget class="QTextEdit" name="comment_text"/>')
        ui_lines.append('     </item>')

        # Wrap up the grid box
        ui_lines.append('    </layout>')
        ui_lines.append('   </widget>')
        ui_lines.append('  </widget>')

        # Output remaining boiler plate:
        ui_lines.append('  <widget class="QMenuBar" name="menubar">')
        ui_lines.append('   <property name="geometry">')
        ui_lines.append('    <rect>')
        ui_lines.append('     <x>0</x>')
        ui_lines.append('     <y>0</y>')
        ui_lines.append('     <width>800</width>')
        ui_lines.append('     <height>38</height>')
        ui_lines.append('    </rect>')
        ui_lines.append('   </property>')
        ui_lines.append('  </widget>')
        ui_lines.append('  <widget class="QStatusBar" name="statusbar"/>')
        ui_lines.append(' </widget>')
        ui_lines.append(' <resources/>')
        ui_lines.append(' <connections/>')
        ui_lines.append('</ui>')
        ui_lines.append('')

    def to_xml_string(self):
        table = self
        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        xml_lines.append('<Table name="{0}">'.format(table.name))
        xml_lines.append('  <TableComments>')
        for comment in table.comments:
            comment.xml_lines_append(xml_lines)
        xml_lines.append('  </TableComments>')
        xml_lines.append('  <Parameters>')
        for parameter in table.parameters:
            parameter.xml_lines_append(xml_lines)
        xml_lines.append('  </Parameters>')
        xml_lines.append('</Table>')
        xml_lines.append('')

        text = '\n'.join(xml_lines)
        return text

    def save(self):
        table = self
        tmp_file_name = "/tmp/" + table.file_name
        xml_text = table.to_xml_string()
        with open(tmp_file_name, "w") as tmp_file:
            tmp_file.write(xml_text)

class TableComment(Comment):
    def __init__(self, **arguments_table):
        # Verify argument types:
        is_comment_tree = "comment_tree" in arguments_table
        if is_comment_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["comment_tree"], etree._Element)
        else:
            assert len(arguments_table) == 2
            assert "language" in arguments_table and is_instance(arguments_table["language"], str)
            assert "lines" in arguments_table
            lines = arguments_table["lines"]
            for line in xml_lines:
                assert isintance(line, str)

        # There are no extra attributes above a *Comment* object, so we can just use the
        # intializer for the *Coment* class:
        super().__init__("TableComment", **arguments_table)

    def __equ__(self, table_comment2):
        # Verify argument types:
        assert isinstance(table_comment2, TableComment)
        return super().__eq__(table_comment2)

    def xml_lines_append(self, xml_lines):
        assert isinstance(xml_lines, list)
        table_comment = self
        xml_lines.append('    <TableComment language="{0}">'.format(table_comment.language))
        for line in table_comment.lines:
            xml_lines.append('      {0}'.format(line))
        xml_lines.append('    </TableComment>')

#FIXME: Old, delete!!!
def show(element, indent):
    # Verity argument types:
    assert isinstance(element, etree._Element)
    assert isinstance(indent, str)

    print("{0}{1}: {2}".format(indent, element.tag, element.attrib))
    element_text = element.text
    if isinstance(element_text, str):
        element_text = element_text.strip()
        if len(element_text) > 0:
            xml_lines = element_text.split('\n')
            for line in xml_lines:
                print("{0} {1}".format(indent, line.strip()))

    for child in element:
        show(child, indent + " ")

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
    arguments_size = len(arguments)
    if len(arguments) == 0:
        print("Usage: {0} table.xml ...".format(arguments[0]))
    else:
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
            table = Table(file_name=table_file_name, table_tree=table_tree)
            tables.append(table)

            ui_text = table.to_ui_string()
            with open("/tmp/test.ui", "w") as ui_file:
                ui_file.write(ui_text)

            # For debugging only, write *table* out to the `/tmp` directory:
            debug = False
            debug = True
            if debug:
                table_write_text = table.to_xml_string()
                with open("/tmp/" + table_file_name, "w") as table_write_file:
                    table_write_file.write(table_write_text)

        # Now create the *tables_editor* graphical user interface (GUI) and run it:
        tables_editor = TablesEditor(tables)
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
    def __init__(self, tables):
        # Verify argument types:
        assert isinstance(tables, list)
        for table in tables:
            assert isinstance(table, Table)

        # Set the *trace_level*:
        trace_level = 0
        #trace_level = 1
        if trace_level >= 1:
            print("=>TablesEditor.__init__(...)")

        # Create the *application* first:
        application = QApplication(sys.argv)

        # Create *main_window* from thie `.ui` file:
        ui_qfile = QFile("tables_editor.ui")
        ui_qfile.open(QFile.ReadOnly)
        loader = QUiLoader()
        main_window = loader.load(ui_qfile)

        ui_qfile = QFile("/tmp/test.ui")
        ui_qfile.open(QFile.ReadOnly)
        search_window = loader.load(ui_qfile)

        for table in tables:
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
        tables_editor.comment_changed_suppress = False
        tables_editor.current_comment = None
        tables_editor.current_parameter = None
        tables_editor.current_table = current_table
        tables_editor.current_tables = tables
        tables_editor.enumeration_changed_suppress = False
        tables_editor.main_window = main_window
        tables_editor.original_tables = copy.deepcopy(tables)
        tables_editor.parameter_long_changed_suppress = False
        tables_editor.parameter_short_changed_suppress = False
        tables_editor.languages = ["English", "Spanish", "Chinese"]
        tables_editor.trace_level = trace_level
        tables_editor.search_window = search_window

        attributes = current_table.parameters
        update_function = partial(TablesEditor.parameter_update, tables_editor)
        new_item_function = partial(TablesEditor.parameter_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_parameter_set, tables_editor)
        combo_edit = ComboEdit(attributes,
          update_function,
          new_item_function,
          current_item_set_function,
          combo_box       = main_window.parameter_combo,
          delete_button   = main_window.common_delete_button, 
          first_button    = main_window.common_first_button,
          last_button     = main_window.common_last_button,
          line_edit       = main_window.common_line,
          next_button     = main_window.common_next_button,
          new_button      = main_window.common_new_button,
          previous_button = main_window.common_previous_button,
          rename_button   = main_window.common_rename_button)
        tables_editor.combo_edit = combo_edit

        # Abbreviate *main_window* as *mw*:
        mw = main_window
        mw.comment_plain_text.textChanged.connect(tables_editor.comment_changed)
        mw.common_save_button.clicked.connect(             tables_editor.save_button_clicked)
        mw.common_quit_button.clicked.connect(             tables_editor.quit_button_clicked)
        mw.enumeration_combo.currentTextChanged.connect(   tables_editor.enumeration_changed)
        mw.enumeration_radio.toggled.connect(              tables_editor.enumeration_radio_toggled)
        mw.language_radio.toggled.connect(                 tables_editor.language_radio_toggled)
        mw.table_radio.toggled.connect(                    tables_editor.table_radio_toggled)
        mw.parameter_default_line.textChanged.connect(     tables_editor.parameter_default_changed)
        mw.parameter_long_line.textChanged.connect(        tables_editor.parameter_long_changed)
        mw.parameter_optional_check.clicked.connect(       tables_editor.parameter_optional_clicked)
        mw.parameter_radio.toggled.connect(                tables_editor.parameter_radio_toggled)
        mw.parameter_short_line.textChanged.connect(       tables_editor.parameter_short_changed)
        mw.parameter_type_combo.currentTextChanged.connect(tables_editor.parameter_type_changed)

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

        # Update the entire user interface:
        tables_editor.update()

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=TablesEditor.__init__(...)\n")

    def comment_changed(self):
        # Preform any tracing requested from *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 3:
            print("=>TablesEditor.comment_changed()")

        # Do nothing if *suppress* is *True*:n
        suppress = tables_editor.comment_changed_suppress
        if not suppress:
            if trace_level >= 1:
                print(" =>TablesEditor.comment_changed()")

            # Extract *actual_text* from the *comment_plain_text* widget:
            main_window = tables_editor.main_window
            comment_plain_text = main_window.comment_plain_text
            actual_text = comment_plain_text.toPlainText()
            if trace_level >= 3:
                print(actual_text)

            # Store *actual_text* into *current_comment* associated with *current_parameter*:
            current_parameter = tables_editor.current_parameter
            if not current_parameter is None:
                # FIXME: this needs to work for tables, parameter, and enumerations!!!
                lines = actual_text.split('\n')
                comments = current_parameter.comments
                assert len(comments) >= 1
                current_comment = comments[0]
                current_comment.lines = lines

            # Force the user interface to be updated:
            tables_editor.update()

            if trace_level >= 1:
                print(" <=TablesEditor.comment_changed()\n")

        if trace_level >= 3:
            print("<=TablesEditor.comment_changed()\n")

    def comment_text_set(self, new_text):
        # Perform any requested tracing:
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.comment_text_set(...)")

        # Carefully set thet text:
        main_window = tables_editor.main_window
        comment_plain_text = main_window.comment_plain_text
        tables_editor.comment_changed_suppress = True
        comment_plain_text.setPlainText(new_text)
        tables_editor.comment_changed_suppress = False

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=TablesEditor.comment_text_set(...)")

    def common_update(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor   = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.common_update()")

        # Grab some values out of *tables_editor* (i.e. *self*):
        original_tables = tables_editor.original_tables
        current_tables  = tables_editor.current_tables
        main_window     = tables_editor.main_window

        # Set the visibility for common widgets:
        tables_are_equal = (current_tables == original_tables)
        common_quit_button   = main_window.common_quit_button
        common_save_button   = main_window.common_save_button
        common_quit_button.setEnabled(tables_are_equal)
        common_save_button.setEnabled(not tables_are_equal)

        # Perform any tracing requested by *tables_editor*:
        if trace_level >= 1:
            print("<=TablesEditor.common_update()")

    def current_parameter_set(self, parameter):
        # Verify argument types:
        assert isinstance(parameter, Parameter)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>Parameter.current_parameter_set('{0}')".
              format(parameter.name if not parameter is None else "None"))

        tables_editor = self
        tables_editor.current_parameter = parameter

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=Parameter.current_parameter_set('{0}')".
              format(parameter.name if not parameter is None else "None"))

    def enumeration_changed(self):
        tables_editor = self
        suppress = tables_editor.enumeration_changed_suppress
        trace_level = tables_editor.trace_level
        if trace_level >= 3:
            print("=>TablesEdit.enumeration_changed(): suppress={0}".format(suppress))
        if not suppress:
            if trace_level >= 1:
                print("=>TablesEdit.enumeration_changed()")
            #print("do something")
            if trace_level >= 1:
                print("<=TablesEdit.enumeration_changed()\n")
        if trace_level >= 3:
            print("<=TablesEdit.enumeration_changed(): suppress={0}\n".format(suppress))

    def enumeration_radio_toggled(self):
        print("=>enumeration_radio_toggeled")
        tables_editor = self
        main_window = tables_editor.main_window
        enumeration_radio = main_window.enumeration_radio
        checked = enumeration_radio.isChecked()
        print("checked={0}".format(checked))
        current_parameter = tables_editor.current_parameter
        if not current_parameter is None:
            comments = current_parameter.comments
            assert len(comments) >= 1
            comment = comments[0]
            comment.lines = lines

    def enumeration_update(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.enumerations_update()")

        # Empty out *enumeration_combo* widgit:
        main_window = tables_editor.main_window
        enumeration_combo = main_window.enumeration_combo
        tables_editor.enumeration_changed_suppress = True
        while enumeration_combo.count() > 0:
            enumeration_combo.removeItem(0)
        tables_editor.enumeration_changed_suppress = False

        # Grab *enumerations* from *current_parameter* (if possible):
        current_parameter = tables_editor.current_parameter
        if not current_parameter is None and current_parameter.type.lower() == "enumeration":
            enumerations = current_parameter.enumerations
            
            # Now fill in *enumeration_combo_box* from *enumerations*:
            current_enumeration_index = -1
            for index, enumeration in enumerate(enumerations):
                enumeration_name = enumeration.name
                #print("[{0}]'{1}'".format(index, enumeration_name))
                tables_editor.enumeration_changed_suppress = True
                enumeration_combo.addItem(enumeration_name)
                tables_editor.enumeration_changed_suppress = False

        # Wrap-up and requested tracing:
        if trace_level >= 1:
            print("<=TablesEditor.enumerations_update()")

    def language_radio_toggled(self):
        print("=>language_radio_toggeled")
        tables_editor = self
        main_window = tables_editor.main_window
        language_radio = main_window.language_radio
        checked = language_radio.isChecked()
        print("checked={0}".format(checked))

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

    def parameter_long_changed(self, new_long_heading):
        # Verify argument types:
        assert isinstance(new_long_heading, str)
        
        # Perform any requested tracing from *tables_editor* (i.e. *self*):
        tables_editor = self
        suppress = tables_editor.parameter_long_changed_suppress
        trace_level = tables_editor.trace_level
        if trace_level >= 3:
            print("=>TablesEditor.parameter_long_changed('{0}') suppress:{1}".
              format(new_long_heading, suppress))

        # Do not further work if *supress* is set to *True*:
        if not suppress:
            if trace_level >= 1:
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
            tables_editor.update()

            if trace_level >= 1:
                print("<=TablesEditor.parameter_long_changed('{0}')\n".format(new_long_heading))

        # Perform any requested tracing from *tables_editor*:
        if trace_level >= 3:
            print("<=TablesEditor.parameter_long_changed('{0}') suppress:{1}\n".
              format(new_long_heading, suppress))

    def parameter_long_set(self, new_long_heading):
        # Verify argument types:
        assert isinstance(new_long_heading, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>parameter_long_set('{0}')".format(new_long_heading))

        # Stuff *new_long_heading* into *current_parameter*:
        current_parameter = tables_editor.current_parameter
        assert isinstance(current_parameter, Parameter)
        current_parameter.long_heading = new_long_heading

        # Now update the user interface to show *new_long_heading* into the *parameter_long_line*
        # widget:
        main_window = tables_editor.main_window
        parameter_long_line = main_window.parameter_long_line
        tables_editor.parameter_long_changed_suppress = True
        parameter_long_line.setText(new_long_heading)
        tables_editor.parameter_long_changed_suppress = False

        if trace_level >= 1:
            print("<=parameter_long_set('{0}')".format(new_long_heading))

    def parameter_new(self, name):
        # Verify argument types:
        assert isinstance(name, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.parmeter_new('{0}')".format(name))

        # Create *new_parameter* named *name*:
        comments = [ParameterComment(language="EN", long_heading=name, lines=list())]
        new_parameter = Parameter(name=name, type="boolean", comments=comments)

        # Wrap up any requested tracing and return *new_parameter*:
        if trace_level >= 1:
            print("<=TablesEditor.parmeter_new('{0}')=>'{1}'".format(new_parameter.name))
        return new_parameter

    def parameter_optional_clicked(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>Tables_Editor.parameter_optional_clicked()")

        current_parameter = tables_editor.current_parameter
        if not current_parameter is None:
            main_window = tables_editor.main_window
            parameter_optional_check = main_window.parameter_optional_check
            optional = parameter_optional_check.isChecked()
            current_parameter.optional = optional

        # Wrap up any requested *tracing*:
        if trace_level >= 1:
            print("=>Tables_Editor.parameter_optional_clicked()\n")

    def parameter_radio_toggled(self):
        print("=>parameter_radio_toggeled")
        tables_editor = self
        main_window = tables_editor.main_window
        parameter_radio = main_window.parameter_radio
        checked = parameter_radio.isChecked()
        print("checked={0}".format(checked))

    def parameter_short_changed(self, new_short_heading):
        # Verify argument types:
        assert isinstance(new_short_heading, str)

        # Perform any requested tracing from *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 3:
            print("=>TablesEditor.parameter_short_changed('{0}')".format(new_short_heading))

        # Do nothing if *parameter_short_changed_suppress* is set:
        parameter_short_changed_suppress = tables_editor.parameter_short_changed_suppress
        if not parameter_short_changed_suppress:
            # Perform any requested tracing:
            if trace_level >= 1:
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
            tables_editor.update()

            # Wrap up any requested tracing:
            if trace_level >= 1:
                print("<=TablesEditor.parameter_short_changed('{0}')\n".format(new_short_heading))

        # Wrap up any requested tracing from *tables_editor*:
        if trace_level >= 3:
            print("<=TablesEditor.parameter_short_changed('{0}')\n".format(new_short_heading))

    def parameter_short_set(self, new_short_heading):
        # Verify argument types:
        assert isinstance(new_short_heading, str) or new_short_heading is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>parameter_short_set('{0}')".format(new_short_heading))

        # Stuff *new_short_heading* into *current_parameter*:
        current_parameter = tables_editor.current_parameter
        assert isinstance(current_parameter, Parameter)
        current_parameter.short_heading = new_short_heading

        # Now update the user interface to show *new_short_heading* into the *parameter_short_line*
        # widget:
        main_window = tables_editor.main_window
        parameter_short_line = main_window.parameter_short_line
        tables_editor.parameter_short_changed_suppress = True
        parameter_short_line.setText("" if new_short_heading is None else new_short_heading)
        tables_editor.parameter_short_changed_suppress = False

        if trace_level >= 1:
            print("<=parameter_short_set('{0}')".format(new_short_heading))

    def parameter_type_changed(self):
        # Perform any requested tracing from *tables_editor* (i.e. *self*):
        tables_editor = self
        current_parameter = tables_editor.current_parameter
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.parameter_type_change('{0}')".
              format(None if current_parameter is None else current_parameter.name))

        if not current_parameter is None:
            main_window = tables_editor.main_window
            parameter_type_combo = main_window.parameter_type_combo
            current_parameter.type = parameter_type_combo.currentText().lower()

        # Wrap-up any requested tracing:
        if trace_level >= 1:
            print("<=TablesEditor.parameter_type_change('{0}')".
              format(None if current_parameter is None else current_parameter.name))

    # TablesEditor
    def parameter_update(self, parameter):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None

        # Perform any requested tracing from *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.parameter_update('{0}')".
              format(None if parameter is None else parameter.name))

        # Grab some widgets from *tables_editor*:
        main_window = tables_editor.main_window
        comment_plain_text       = main_window.comment_plain_text
        parameter_default_line   = main_window.parameter_default_line
        parameter_optional_check = main_window.parameter_optional_check
        parameter_type_combo     = main_window.parameter_type_combo

        # Now we can update the other fields:
        if parameter is None:
            parameter = tables_editor.current_parameter
        if parameter is None:
            # *parameter* is empty:
            is_valid_parameter = False
            default  = ""
            optional = False
            type     = ""
        else:
            # Grab some values from *parameter*:
            is_valid_parameter = True
            default  = parameter.default
            optional = parameter.optional
            type     = parameter.type
        #print("type='{0}' optional={1}".format(type, optional))

        # Stuff the values in to the *parameter_type_combo* widget:
        for index in range(parameter_type_combo.count()):
            item_text = parameter_type_combo.itemText(index).lower()
            #print("[{0}] '{1}'".format(index, item_text))
            if type.lower() == item_text.lower():
                #print("match")
                parameter_type_combo.setCurrentIndex(index)
                break

        parameter_default_line.setText(default)
        parameter_optional_check.setChecked(optional)

        # Enable/disable the parameter widgets:
        parameter_type_combo.setEnabled(    is_valid_parameter)
        parameter_default_line.setEnabled(  is_valid_parameter)
        parameter_optional_check.setEnabled(is_valid_parameter)

        # Update the *comments* (if they exist):
        if not parameter is None:
            comments = parameter.comments
            #Kludge for now, select the first comment
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)

            # Update the headings:
            tables_editor.parameter_long_set(comment.long_heading)
            tables_editor.parameter_short_set(comment.short_heading)

            # Deal with comment text edit area:
            tables_editor.current_comment = comment
            lines = comment.lines
            text = '\n'.join(lines)

            tables_editor.comment_text_set(text)

        # Changing the *parameter* can change the enumeration combo box, so update it as well:
        tables_editor.enumeration_update()
        tables_editor.common_update()

        # Wrap-up any requested tracing:
        if trace_level >= 1:
            print("<=TablesEditor.parameter_update('{0}')".
              format(None if parameter is None else parameter.name))

    def quit_button_clicked(self):
        tables_editor = self
        print("TablesEditor.quit_button_clicked() called")
        application = tables_editor.application
        application.quit()

    def run(self):
        # Show the *window* and exit when done:
        tables_editor = self 
        main_window = tables_editor.main_window
        application = tables_editor.application

        main_window.show()
        
        search_window = tables_editor.search_window
        search_window.show()

        sys.exit(application.exec_())

    def save_button_clicked(self):
        print("TablesEditor.save_button_clicked() called")
        tables_editor = self
        current_tables = tables_editor.current_tables
        for table in current_tables:
            table.save()

    def table_radio_toggled(self):
        print("=>table_radio_toggeled")
        tables_editor = self
        main_window = tables_editor.main_window
        table_radio = main_window.table_radio
        checked = table_radio.isChecked()
        print("checked={0}".format(checked))


    def update(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor   = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.update()")

        tables_editor.combo_edit.update()
        tables_editor.parameter_update(None)
        tables_editor.common_update()

        # Perform any tracing requested by *tables_editor*:
        if trace_level >= 1:
            print("<=TablesEditor.update()")

class ComboEdit:
    """ A *ComboEdit* object repesents the GUI controls for manuipulating a combo box widget.
    """

    # *WIDGET_CALLBACKS* is defined at the end of this class after all of the callback routines
    # are defined.
    WIDGET_CALLBACKS = dict()

    # Class: ComboEdit
    def __init__(self,
      items, update_function, new_item_function, current_item_set_function, **widgets):
        """ Initialize the *ComboEdit* object (i.e. *self*.)

        The arguments are:
        * *items*: A list of item objects to manage.
        * *update_function*: A function when the current item has changed.
        * *new_item_function*: A function that is called to create a new item.
        * *current_item_set*: A function that is called each time the current item is set.
        * *widgets*: A dictionary of widget names to widgets.  The following widget names
          are required:
          * "combo_box":    The *QComboBox* widget to be edited.
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
        assert isinstance(items, list)
        assert callable(update_function)
        assert callable(new_item_function)
        widget_callbacks = ComboEdit.WIDGET_CALLBACKS
        widget_names = list(widget_callbacks)
        assert len(widget_callbacks) == len(widgets), "Missing (or extra) widget argument(s)."
        for widget_name, widget in widgets.items():
            assert widget_name in widget_names, "Invalid widget name '{0}'".format(widget_name)
            assert isinstance(widget, QWidget), "'{0}' is not a QWidget"
                                
        # Load some values into *combo_edit* (i.e. *self*):
        trace_level = 0
        #trace_level = 1
        combo_edit = self
        combo_edit.combo_box_being_updated = False
        combo_edit.current_item_set_function = current_item_set_function
        combo_edit.items = items
        combo_edit.new_item_function = new_item_function
        combo_edit.trace_level = trace_level
        combo_edit.update_function = update_function

        # Set the current item after *current_item_set_function* has been set.
        combo_edit.current_item_set(items[0] if len(items) > 0 else None, "ComboEdit.__init__")

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
                widget.currentTextChanged.connect(partial(callback, combo_edit))
            elif isinstance(widget, QLineEdit):
                # *widget* is a *QLineEdit* and generate a callback for each character changed:
                assert widget_name == "line_edit"
                widget.textEdited.connect(        partial(callback, combo_edit))
            elif isinstance(widget, QPushButton):
                # *widget* is a *QPushButton* and generat a callback for each click:
                widget.clicked.connect(           partial(callback, combo_edit))
            else:
                assert False, "'{0}' is not a valid widget".format(widget_name)

        # Not needed, the high level code will perform the update:
        #combo_edit.update()


    def combo_box_changed(self, new_name):
        """ Callback method invoked when the *QComboBox* widget changes:

        The arguments are:
        * *new_name*: The *str* that specifies the new *QComboBox* widget value selected.
        """

        # Verify argument types:
        assert isinstance(new_name, str)

        # Perform any requested *trace*:
        combo_edit = self
        trace_level = combo_edit.trace_level
        if trace_level >= 3:
            print("=>ComboEdit.combo_box_changed('{0}')".format(new_name))

        # When *ComboEdit.update()* is updating its associated *combo_box* it generates
        # a whole bunch of spurious calls to this routine that need to be ignored.  These
        # spurious events are ignored by setting *combo_box_being_edited* to *True*:
        combo_box_being_updated = combo_edit.combo_box_being_updated

        #print("combo_box_being_updated={0}".format(combo_box_being_updated))
        if not combo_box_being_updated:
            if trace_level >= 1:
                print("=>ComboEdit.combo_box_changed('{0}')".format(new_name))

            # We have a non-spurious attribute combo box change event.  Scan *attributes*
            # to find the *attribute* that matches *new_name*:
            # Grab *attributes* (and compute *attributes_size*) from *combo_edit* (i.e. *self*):
            items = combo_edit.items
            for index, item in enumerate(items):
                if item.name == new_name:
                    # We have found the new *current_item*:
                    #print("items[{0}] '{1}'".format(index, item.name))
                    combo_edit.current_item_set(item, "combo_box_changed")
                    break

            # Force GUI update:
            combo_edit.update()

            if trace_level >= 1:
                print("=>ComboEdit.combo_box_changed('{0}')\n".format(new_name))

        if trace_level >= 3:
            print("<=ComboEdit.combo_box_changed('{0}')\n".format(new_name))

    def current_item_get(self):
        #print("=>current_item_get()")

        # Grab some values from *combo_edit* (i.e. *self*):
        combo_edit   = self
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

        # If the *current_item* has changed, we let the parrent know:
        if not new_current_item is current_item:
            combo_edit.current_item_set(new_current_item, "current_item_get")

        #print("<=current_item_get()=>'{0}'".format(
        #    "--" if combo_edit.current_item is None else combo_edit.current_item.name))
        return new_current_item

    def current_item_set(self, current_item, caller_trace):
        name_text = "??"
        if current_item is None:
            name_text = "None"
        elif isinstance(current_item, Parameter):
            name_text = current_item.name
        #print("current_item_set('{0}', from='{1}')".format(name_text, caller_trace))

        combo_edit = self
        combo_edit.current_item = current_item
        combo_edit.current_item_set_function(current_item)

    def delete_button_clicked(self):
        # Perform any requested tracing from *combo_edit* (i.e. *self*):
        combo_edit = self
        trace_level = combo_edit.trace_level
        if trace_level >= 1:
            print("=>ComboEdit.delete_button_clicked()")

        # Find the matching *item* in *items* and delete it:
        items      = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                # Delete the *current_item* from *items*:
                del items[index]

                # Update *current_item* in *combo_edit*:
                if 0 <= index < items_size:
                    current_item = items[index]
                elif 0 <= index - 1 < attributes_size:
                    current_item = items[index - 1]
                else:
                    current_item = None
                combo_edit.current_item_set(current_item, "delete_button")
                break
        combo_edit.update()

        # Wrap up any requested tracing;
        if trace_level >= 1:
            print("<=ComboEdit.delete_button_clicked()")

    def first_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        trace_level = combo_edit.trace_level
        if trace_level >= 1:
            print("=>ComboEdit.first_button_clicked()")

        # If possible, select the *first_item*:
        items      = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            first_item = items[0]
            combo_edit.current_item_set(first_item, "first_button")

        # Update the user interface:
        combo_edit.update()

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=ComboEdit.first_button_clicked()\n")

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

    def last_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        trace_level = combo_edit.trace_level
        if trace_level >= 1:
            print("=>ComboEdit.last_button_clicked()")

        # If possible select the *last_item*:
        items      = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            last_item = items[-1]
            combo_edit.current_item_set(last_item, "last_button")

        # Update the user interface:
        combo_edit.update()

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=ComboEdit.last_button_clicked()\n")

    def line_edit_changed(self, text):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        trace_level = combo_edit.trace_level
        if trace_level >= 1:
            print("=>ComboEditor.line_edit_changed('{0}')".format(text))
        combo_edit.update()
        if trace_level >= 1:
            print("<=ComboEditor.line_edit_changed('{0}')".format(text))

    def new_button_clicked(self):
        combo_edit        = self
        trace_level = combo_edit.trace_level
        if trace_level >= 1:
            print("=>ComboEdit.new_button_clicked()")

        # Grab some values from *combo_edit*:
        combo_box         = combo_edit.combo_box
        items             = combo_edit.items
        line_edit         = combo_edit.line_edit
        new_item_function = combo_edit.new_item_function

        # Create a *new_item* and append it to *items*:
        new_item_name = line_edit.text()
        #print("new_item_name='{0}'".format(new_item_name))
        new_item = new_item_function(new_item_name)
        items.append(new_item)
        combo_edit.update()

        if trace_level >= 1:
            print("<=ComboEdit.new_button_clicked()")

    def next_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        trace_level = combo_edit.trace_level
        if trace_level >= 1:
            print("=>ComboEdit.next_button_clicked()")

        # ...
        items      = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                if index + 1 < items_size:
                    current_item = items[index + 1]
                break
        combo_edit.current_item_set(current_item, "next_button")
        combo_edit.update()

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=ComboEdit.next_button_clicked()\n")

    def previous_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        trace_level = combo_edit.trace_level
        if trace_level >= 1:
            print("=>ComboEdit.previous_button_clicked()")

        # ...
        items      = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                if index > 0:
                    current_item = items[index - 1]
                break
        combo_edit.current_item_set(current_item, "previous_button")
        combo_edit.update()

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=ComboEdit.previous_button_clicked()\n")

    def rename_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        print("ComboEditor.rename_button_clicked() called")
        combo_edit = self
        line_edit = combo_edit.line_edit
        new_item_name = line_edit.text()

        current_item = combo_edit.current_item_get()
        if not current_item is None:
            current_item.name = new_item_name
        combo_edit.update()

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=ComboEdit.reuame_button_clicked()\n")

    def update(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit  = self
        trace_level = combo_edit.trace_level
        if trace_level >= 1:
            print("=>ComboEdit.update()")

        # Grab the widgets from *combo_edit*:
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
        #attribute_type_combo_box.setEnabled(    is_a_valid_item)
        #attribute_optional_check_box.setEnabled(is_a_valid_item)
        #attribute_default_line_edit.setEnabled( is_a_valid_item)


        # Changing the *combo_box* generates a bunch of spurious callbacks to
        # *ComboEdit.combo_box_changed()* callbacks.  The *combo_box_being_updated* attribute
        # is set to *True* in *combo_edit* so that these spurious callbacks can be ignored.
        combo_edit.combo_box_being_updated = True
        #print("combo_edit.combo_box_being_updated={0}".format(combo_edit.combo_box_being_updated))

        # Empty out *combo_box*:
        while combo_box.count() > 0:
            combo_box.removeItem(0)

        # Sweep through *items* updating the *combo_box*:
        current_item_index = -1
        for index, item in enumerate(items):
            combo_box.addItem(item.name)
            #print("[{0}]:item={1}".format(index,  "--" if item is None else item.name)
            if item == current_item:
                combo_box.setCurrentIndex(index)
                current_item_index = index
        assert not is_a_valid_item or current_item_index >= 0
        #print("current_item_index={0}".format(current_item_index))
        #print("items_size={0}".format(items_size))

        # We are done modifiying *combo_box*, so we no shorter have suppress spurious
        # *ComboEdit.combo_box_changed()* callbacks any more:
        combo_edit.combo_box_being_updated = False
        #print("combo_edit.combo_box_being_updated={0}".format(combo_edit.combo_box_being_updated))

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

        update_function = combo_edit.update_function
        update_function(current_item)

        if trace_level >= 1:
            print("<=ComboEdit.update()")

    # *WIDGET_CALLBACKS* is defined here **after** the actual callback routines are defined:
    WIDGET_CALLBACKS = {
      "combo_box":       combo_box_changed,
      "delete_button":   delete_button_clicked,
      "first_button":    first_button_clicked,
      "last_button":     last_button_clicked,
      "line_edit":       line_edit_changed,
      "next_button":     next_button_clicked,    
      "new_button":      new_button_clicked,
      "previous_button": previous_button_clicked,
      "rename_button":   rename_button_clicked,
    }

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

if __name__ == "__main__":
    main()



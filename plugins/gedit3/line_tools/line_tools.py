# Copyright (C) 2010 - Jens Nyman (nymanjens.nj@gmail.com)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.

from gi.repository import Gtk, GObject, Gedit
import re
import traceback

# UI Manager XML
ACTIONS_UI = """
<ui>
    <menubar name="MenuBar">
        <menu name="EditMenu" action="Edit">
            <placeholder name="EditOps_6">
                <menuitem name="ToggleComment" action="ToggleComment"/>
                <menuitem name="ToggleIndentedComment" action="ToggleIndentedComment"/>
                <menuitem name="DuplicateLine" action="DuplicateLine"/>
                <menuitem name="SelectLine" action="SelectLine"/>
                <menuitem name="SelectText" action="SelectText"/>
                <menuitem name="SelectWord" action="SelectWord"/>
                <menuitem name="AddSemicolon" action="AddSemicolon"/>
            </placeholder>
        </menu>
    </menubar>
</ui>
"""

class LineToolsPlugin(GObject.Object, Gedit.WindowActivatable):
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self._instances = {}

    def do_activate(self):
        self._instances[self.window] = LineToolsWindowHelper(self, self.window)

    def do_deactivate(self):
        self._instances[self.window].deactivate()
        del self._instances[self.window]

    def do_update_state(self):
        self._instances[self.window].update_ui()



class LineToolsWindowHelper:
    def __init__(self, plugin, window):
        self._window = window
        self._plugin = plugin
        # Insert menu items
        self._insert_menu()

    def deactivate(self):
        # Remove any installed menu items
        self._remove_menu()
        self._window = None
        self._plugin = None
        self._action_group = None

    def _insert_menu(self):
        # actions
        actions = [
            (
                "ToggleComment", # name
                None, # icon stock id
                "_Toggle Comment", # label
                "<Control>r", # shortcut
                "_Toggle Comment", # tooltip
                self.toggle_comment # callback
            ),
            (
                "ToggleIndentedComment", # name
                None, # icon stock id
                "Toggle _Indented Comment", # label
                "<Control><Shift>r", # shortcut
                "Toggle _Indented Comment", # tooltip
                self.toggle_indented_comment # callback
            ),
            (
                "DuplicateLine", # name
                None, # icon stock id
                "_Duplicate Line", # label
                "<Control>b", # shortcut
                "_Duplicate Line", # tooltip
                self.duplicate_line # callback
            ),
            (
                "SelectLine", # name
                None, # icon stock id
                "_Select Line", # label
                "<Control>l", # shortcut
                "_Select Line", # tooltip
                self.select_line # callback
            ),
            (
                "SelectText", # name
                None, # icon stock id
                "Select _Text", # label
                "<Control>j", # shortcut
                "Select _Text", # tooltip
                self.select_text # callback
            ),
            (
                "SelectWord", # name
                None, # icon stock id
                "Select _Word", # label
                "<Control>m", # shortcut
                "Select _Word", # tooltip
                self.select_word # callback
            ),
            (
                "AddSemicolon", # name
                None, # icon stock id
                "Add Semicolon", # label
                "<Control>semicolon", # shortcut
                "Add Semicolon", # tooltip
                self.add_semicolon # callback
            ),
        ]

        # Create a new action group
        self._action_group = Gtk.ActionGroup(self.__class__.__name__)
        self._action_group.add_actions(actions)
        # Get the GtkUIManager
        manager = self._window.get_ui_manager()
        # Insert the action group
        manager.insert_action_group(self._action_group, -1)
        # Merge the UI
        self._ui_id = manager.add_ui_from_string(ACTIONS_UI)

    def _remove_menu(self):
        # Get the GtkUIManager
        manager = self._window.get_ui_manager()
        # Remove the ui
        manager.remove_ui(self._ui_id)
        # Remove the action group
        manager.remove_action_group(self._action_group)
        # Make sure the manager updates
        manager.ensure_update()

    def update_ui(self):
        self._action_group.set_sensitive(self._window.get_active_document() != None)

        
    ############ plugin core functions ############
    ###################### TOGGLE COMMENT ######################
    # Menu activate handlers
    def toggle_comment(self, action, indented = None):
        document = self._window.get_active_document()
        if not document:
            return
        try:
            bounds = document.get_selection_bounds()
            if len(bounds) == 0:
                ### COMMENT SELECTED LINE ###
                cursor = document.get_iter_at_mark(document.get_insert())
                self.toggle_comment_at_cursor(document, cursor, indented)
            else:
                ### COMMENT SELECTED LINES ###
                # Note:
                #   Bug: when moving a line, the next line also gets selected
                #   Solution: subtract 1 char from end offset, but this would change manual selection,
                #             which can or cannot be desired
                #if bounds[1].get_offset() != document.get_iter_at_mark(document.get_insert()).get_offset():
                bounds[1].set_offset(bounds[1].get_offset() - 1);
                
                cursor = bounds[0].copy()
                start_ln_index = bounds[0].get_line()
                end_ln_index = bounds[1].get_line()
                
                uniform_comment_action = None
                for line_index in range(start_ln_index, end_ln_index + 1):
                    cursor = document.get_iter_at_mark(document.get_insert())
                    cursor.set_line(line_index)
                    (indented, uniform_comment_action) = self.toggle_comment_at_cursor(
                        document, cursor, indented, force_comment = uniform_comment_action)
        except:
            err = "Exception\n"
            err += traceback.format_exc()
            document.set_text(err)
    
    def toggle_comment_at_cursor(self, document, cursor, indented, force_comment = None):
        # get comment code
        import os.path
        path = document.get_uri_for_display()
        if path:
            spli = os.path.splitext(path)
            ext = spli[1][1:]
        else:
            ext = ""
        comment_code = {
            'php': '//',
            'js': '//',
            'c': '//',
            'cpp': '//',
            'cc': '//',
            'h': '//',
            'm': '%',
            'py': '#',
            'sql': '#',
            'java': '//',
            'groovy': '//',
            'tex': '%',
            'sh': '#',
        }.get(ext, "#")

        # get cursor at start
        if not cursor.starts_line():
            cursor.set_line_offset(0)
        # get line
        end = cursor.copy()
        if not end.ends_line():
            end.forward_to_line_end()
        line = document.get_text(cursor, end, False)
        index = 0
        for char in line:
            if char == " " or char == "\t":
                index += 1
                continue
            break
        # keep forcing in mind
        remove_comment = line[index:index + len(comment_code)] == comment_code
        if force_comment:
            if force_comment == 'REMOVE' and not remove_comment:
                return (indented, force_comment)
            remove_comment = force_comment == 'REMOVE'
        if remove_comment:
            # remove comment
            extra = 0
            # remove auto-added space
            if len(line) > index + len(comment_code) and line[index + len(comment_code)] == ' ':
                extra = 1
            # don't remove space before tab
            if len(line) > index + len(comment_code) + 1:
                if line[index + len(comment_code) + 1] == " " or line[index + len(comment_code) + 1] == "\t":
                    extra = 0
            cursor.set_line_offset(index)
            end = cursor.copy()
            end.set_line_offset(index + len(comment_code) + extra)
            document.delete(cursor, end)
            return (indented, 'REMOVE')
        else:
            # add comment
            added_space = " "
            # indented comment: comment right before code
            if indented != None:
                if type(indented) is bool:
                    indent_index = indented = index
                else:
                    indent_index = min(indented, index)
                cursor.set_line_offset(indent_index)
                added_space = ''
                    
            # don't add space before tab
            elif len(line) > 0:
                if line[0] == ' ' or line[0] == "\t":
                    added_space = ""
            cursor.get_buffer().insert(cursor, comment_code + added_space)
            return (indented, 'ADD')

    ###################### TOGGLE INDENTED COMMENT ######################
    def toggle_indented_comment(self, action):
        return self.toggle_comment(action, indented = True)
        
        
    ###################### DUPLICATE LINE ######################
    def duplicate_line(self, action):
        document = self._window.get_active_document()
        if not document:
            return
        try:
            bounds = document.get_selection_bounds()
            if len(bounds) == 0:
                ### COMMENT SELECTED LINE ###
                cursor = document.get_iter_at_mark(document.get_insert())
                start = cursor.copy()
                start.set_line_offset(0)
                end = cursor.copy()
                if not end.ends_line():
                    end.forward_to_line_end()
                self.duplicate_bounds(document, start, end)
            else:
                ### COMMENT SELECTED LINES ###
                # Note:
                #   Bug: when moving a line, the next line also gets selected
                #   Solution: subtract 1 char from end offset, but this would change manual selection,
                #             which can or cannot be desired
                #if bounds[1].get_offset() != document.get_iter_at_mark(document.get_insert()).get_offset():
                bounds[1].set_offset(bounds[1].get_offset() - 1);
                
                start = bounds[0].copy()
                start.set_line_offset(0)
                end = bounds[1].copy()
                if not end.ends_line():
                    end.forward_to_line_end()
                self.duplicate_bounds(document, start, end)
        except:
            err = "Exception\n"
            err += traceback.format_exc()
            document.set_text(err)
    
    def duplicate_bounds(self, doc, start, end):
        NL = '\n'
        text = doc.get_text(start, end, False)
        # filter newlines
        # text = ''.join(c for c in text if c not in ['\n', '\r'])
        text = NL + text
        doc.place_cursor(end)
        doc.insert_at_cursor(text)
        cursor = doc.get_iter_at_mark(doc.get_insert())
        start = cursor.copy()
        start.set_offset(cursor.get_offset() - ( len(text) - 1 ))
        doc.select_range(start, cursor)
        
    ###################### SELECT LINE ######################
    def select_line(self, action):
        document = self._window.get_active_document()
        if not document:
            return
        try:
            cursor = document.get_iter_at_mark(document.get_insert())
            start = cursor.copy()
            start.set_line_offset(0)
            end = cursor.copy()
            if not end.ends_line():
                end.forward_to_line_end()
            document.select_range(start, end)
        except:
            err = "Exception\n"
            err += traceback.format_exc()
            document.set_text(err)
        
    ###################### SELECT TEXT ######################
    def select_text(self, action):
        doc = self._window.get_active_document()
        if not doc:
            return
        try:
            # settings
            NON_TEXT = [' ', '\n', '\r', '\t', '+', '-', '>']
            # get vars
            cursor = doc.get_iter_at_mark(doc.get_insert())
            start = cursor.copy()
            start.set_line_offset(0)
            end = cursor.copy()
            if not end.ends_line():
                end.forward_to_line_end()
            line = doc.get_text(start, end, False)
            # sanity check
            if len(line) == 0:
                return
            # get index where text starts
            start_index = 0
            while start_index < len(line) and line[start_index] in NON_TEXT:
                start_index += 1
            # get index where text ends
            end_index = len(line) - 1
            while line[end_index] in NON_TEXT:
                end_index -= 1
                if end_index < 0:
                    return
            # apply indices and select
            start.set_line_offset(start_index)
            end.set_line_offset(end_index + 1)
            doc.select_range(start, end)
        except:
            err = "Exception\n"
            err += traceback.format_exc()
            doc.set_text(err)
        
    ###################### SELECT WORD ######################
    def select_word(self, action):
        doc = self._window.get_active_document()
        if not doc:
            return
        try:
            # help functions
            def valid_text(start, end):
                if not start or not end:
                    return False
                if start.get_line_offset() > end.get_line_offset():
                    (start, end) = (end, start) # swap
                text = doc.get_text(start, end, False)
                for char in text:
                    if not re.match("\w", char):
                        return False
                return True
            def increment(index, incr):
                newindex = index.copy()
                newindex.set_line_offset(index.get_line_offset() + incr)
                return newindex
            def find_word_bound(index, step):
                condition = lambda x: not index.get_line_offset() == 0 if step < 0 else lambda x: not x.ends_line()
                while condition(index):
                    newindex = increment(index, step)
                    # newindex contains word?
                    if not valid_text(newindex, index):
                        break
                    # save new index
                    index = newindex
                return index
            # get vars
            cursor = doc.get_iter_at_mark(doc.get_insert())
            start = find_word_bound(cursor, -1)
            end = find_word_bound(cursor, +1)
            # select start->end
            doc.select_range(start, end)
        except:
            err = "Exception\n"
            err += traceback.format_exc()
            doc.set_text(err)
        
    ###################### ADD SEMICOLON ######################
    def add_semicolon(self, action):
        doc = self._window.get_active_document()
        if not doc:
            return
        try:
            # get vars
            cursor = doc.get_iter_at_mark(doc.get_insert())
            if not cursor.ends_line():
                cursor.forward_to_line_end()
            # select start->end
            cursor.get_buffer().insert(cursor, ';')
        except:
            err = "Exception\n"
            err += traceback.format_exc()
            doc.set_text(err)
        
        
        
    

# -*- coding: utf8 -*-
#  Text Tools Plugin
#
#  Copyright (C) 2008 Shaddy Zeineddine <simpsomboy at gmail dot com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  Some code was got from LineTools Plugin

import gedit
import gtk

class TextToolsPlugin(gedit.Plugin):

    line_tools_str = """
        <ui>
          <menubar name="MenuBar">
            <menu name="EditMenu" action="Edit">
              <placeholder name="EditOps_6">
                <menu action="TextTools">
                  <menuitem action="ClearLine"/>
                  <menuitem action="DuplicateLine"/>
                  <menuitem action="RaiseLine"/>
                  <menuitem action="LowerLine"/>
                  <menuitem action="SelectEnclosed"/>
                  <menuitem action="SelectWord"/>
                  <menuitem action="SelectWordSpecial"/>
                </menu>
              </placeholder>
            </menu>
          </menubar>
        </ui>
        """

    bookmarks = {}

    def __init__(self):
        gedit.Plugin.__init__(self)
        self.__select_word_special = False

    def activate(self, window):
        actions = [
            ('TextTools',           None, 'Text Tools'),
            ('ClearLine',           None, 'Clear Line',         '<Shift><Control>c', 'Remove all the characters on the current line',                 self.clear_line),
            ('DuplicateLine',       None, 'Duplicate Line',     '<Shift><Control>d', 'Create a duplicate of the current line below the current line', self.duplicate_line),
            ('RaiseLine',           None, 'Move Line Up',       '<Alt>Up',           'Transpose the current line with the line above it',             self.raise_line),
            ('LowerLine',           None, 'Move Line Down',     '<Alt>Down',         'Transpose the current line with the line below it',             self.lower_line),
            ('SelectEnclosed',      None, 'Select Enclosed Text','<Alt><Control>9',  'Select the content between enclose chars, quotes or tags',      self.select_enclosed),
            ('SelectWord',          None, 'Select Word',        '<Alt>W',            'Select the word located under cursor',                          self.select_word),
            ('SelectWordSpecial',   None, 'Select Word Special','<Alt><Shift>W',     'Select the word located under cursor ignoring any delimiter',   self.select_word_special)
        ]
        windowdata = dict()
        window.set_data("TextToolsPluginWindowDataKey", windowdata)
        windowdata["action_group"] = gtk.ActionGroup("GeditTextToolsPluginActions")
        windowdata["action_group"].add_actions(actions, window)
        manager = window.get_ui_manager()
        manager.insert_action_group(windowdata["action_group"], -1)
        windowdata["ui_id"] = manager.add_ui_from_string(self.line_tools_str)
        window.set_data("TextToolsPluginInfo", windowdata)

    def deactivate(self, window):
        windowdata = window.get_data("TextToolsPluginWindowDataKey")
        manager = window.get_ui_manager()
        manager.remove_ui(windowdata["ui_id"])
        manager.remove_action_group(windowdata["action_group"])

    def update_ui(self, window):
        view = window.get_active_view()
        windowdata = window.get_data("TextToolsPluginWindowDataKey")
        windowdata["action_group"].set_sensitive(bool(view and view.get_editable()))

    def clear_line(self, action, window):
        # Got from LineTools plugin
        doc = window.get_active_document()
        doc.begin_user_action()
        itstart = doc.get_iter_at_mark(doc.get_insert())
        itstart.set_line_offset(0);
        is_end = itstart.ends_line()
        if is_end == False:
            itend = doc.get_iter_at_mark(doc.get_insert())
            is_end = itend.ends_line()
            if is_end == False:
                itend.forward_to_line_end()
            doc.delete(itstart, itend)
        doc.end_user_action()

    def duplicate_line(self, action, window):
        # Got from LineTools plugin
        doc = window.get_active_document()
        doc.begin_user_action()
        itstart = doc.get_iter_at_mark(doc.get_insert())
        itstart.set_line_offset(0);
        itend = doc.get_iter_at_mark(doc.get_insert())
        itend.forward_line()
        line = doc.get_slice(itstart, itend, True)
        doc.insert(itend, line)
        doc.end_user_action()

    def raise_line(self, action, window):
        # Got from LineTools plugin
        doc = window.get_active_document()
        doc.begin_user_action()
        itstart = doc.get_iter_at_mark(doc.get_insert())
        itstart.set_line_offset(0);
        itstart.backward_line()
        itend = doc.get_iter_at_mark(doc.get_insert())
        itend.set_line_offset(0);
        line = doc.get_slice(itstart, itend, True)
        doc.delete(itstart, itend)
        itend.forward_line()
        doc.insert(itend, line)
        doc.end_user_action()

    def lower_line(self, action, window):
        # Got from LineTools plugin
        doc = window.get_active_document()
        doc.begin_user_action()
        itstart = doc.get_iter_at_mark(doc.get_insert())
        itstart.forward_line()
        itend = doc.get_iter_at_mark(doc.get_insert())
        itend.forward_line()
        itend.forward_line()
        line = doc.get_slice(itstart, itend, True)
        doc.delete(itstart, itend)
        itstart.backward_line()
        doc.insert(itstart, line)
        doc.end_user_action()

    def select_enclosed(self, action, window):
        """Select Characters enclosed by quotes or braces"""
        starting_chars = ["`",'"', "'", "[", "(", "{", "<", ">", "/"]
        ending_chars   = ["`",'"', "'", "]", ")", "}", ">", "<", "/"]
        beg_iter = None
        end_iter = None
        char_match = None
        doc = window.get_active_document()
        itr = doc.get_iter_at_mark(doc.get_insert())
        while itr.backward_char():
            if itr.get_char() in starting_chars:
                char_match = ending_chars[starting_chars.index(itr.get_char())]
                itr.forward_char()
                beg_iter = itr.copy()
                break
        while itr.forward_char():
            if itr.get_char() == char_match:
                end_iter = itr.copy()
                break
        doc.select_range(beg_iter, end_iter)

    def select_word_special(self, action, window):
        self.__select_word_special = True
        self.select_word(action, window)
        self.__select_word_special = False

    def select_word(self, action, window):
        """Select Characters enclosed by quotes or braces"""
        beg_iter = None
        end_iter = None
        if self.__select_word_special:
            word_delimiter_chars = [" ","\n"]
        else:
            word_delimiter_chars = [" ","\n", '"', "'", "[", "(", "{", "]", ")", "}", ":", ";", "`", "="]
        char_match = None
        doc = window.get_active_document()
        itr = doc.get_iter_at_mark(doc.get_insert())
        while itr.backward_char():
            if itr.get_char() in word_delimiter_chars:
                itr.forward_char()
                beg_iter = itr.copy()
                break
        if beg_iter is None:
            beg_iter = itr.copy()

        while itr.forward_char():
            if itr.get_char() in word_delimiter_chars:
                end_iter = itr.copy()
                break
        if end_iter is None:
            end_iter = itr.copy()

        if beg_iter and end_iter:
            doc.select_range(beg_iter, end_iter)


#        Gedit gemini plugin
#        Copyright (C) 2005-2006    Gary Haran <gary.haran@gmail.com>
#
#        This program is free software; you can redistribute it and/or modify
#        it under the terms of the GNU General Public License as published by
#        the Free Software Foundation; either version 2 of the License, or
#        (at your option) any later version.
#
#        This program is distributed in the hope that it will be useful,
#        but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#        GNU General Public License for more details.
#
#        You should have received a copy of the GNU General Public License
#        along with this program; if not, write to the Free Software
#        Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
#        02110-1301  USA

import gedit
import gtk
import gobject
import re

class GeminiPlugin( gedit.Plugin):
    handler_ids = []

    def __init__(self):
        gedit.Plugin.__init__(self)

    def activate(self, window):
        view = window.get_active_view()
        self.setup_gemini (view)

    def deactivate(self, window):
        for (handler_id, view) in self.handler_ids:
            if view.handler_is_connected(handler_id):
                view.disconnect(handler_id)

    def update_ui(self, window):
        view = window.get_active_view()
        self.setup_gemini(view)


    # Starts auto completion for a given view
    def setup_gemini(self, view):
        if type(view) == gedit.View:
            if getattr(view, 'gemini_instance', False) == False:
                setattr(view, 'gemini_instance',Gemini())
                handler_id = view.connect ('key-press-event', view.gemini_instance.key_press_handler)
                self.handler_ids.append((handler_id, view))

class Gemini:
    start_keyvals = [34, 39, 96, 40, 91, 123]
    end_keyvals   = [34, 39, 96, 41, 93, 125]
    twin_start    = ['"',"'",'`','(','[','{']
    twin_end      = ['"',"'",'`',')',']','}']
    toggle        = False

    def __init__(self):
        return

    def key_press_handler(self, view, event):
        if gedit.version > (2, 30, 3):
            if self.toggle:
                self.toggle = False
                return
            else:
                self.toggle = True
        buf = view.get_buffer()
        cursor_mark = buf.get_insert()
        cursor_iter = buf.get_iter_at_mark(cursor_mark)

        if event.keyval in self.start_keyvals or event.keyval in self.end_keyvals or event.keyval in (65288, 65293):

            back_iter = cursor_iter.copy()
            back_char = back_iter.backward_char()
            back_char = buf.get_text(back_iter, cursor_iter)
            forward_iter = cursor_iter.copy()
            forward_char = forward_iter.forward_char()
            forward_char = buf.get_text(cursor_iter, forward_iter)

            if event.keyval in self.start_keyvals:
                index = self.start_keyvals.index(event.keyval)
                start_str = self.twin_start[index]
                end_str = self.twin_end[index]
            else:
                index = -1
                start_str, end_str = None, None

            # Here is the meat of the logic
            if buf.get_has_selection() and event.keyval not in (65288, 65535):
                # pad the selected text with twins
                start_iter, end_iter = buf.get_selection_bounds()
                selected_text = start_iter.get_text(end_iter)
                buf.delete(start_iter, end_iter)
                buf.insert_at_cursor(start_str + selected_text + end_str)
                return True
            elif index >= 0 and start_str == self.twin_start[index]:
                # insert the twin that matches your typed twin
                buf.insert(cursor_iter, end_str)
                if cursor_iter.backward_char():
                    buf.place_cursor (cursor_iter)
            elif event.keyval == 65288 and back_char in self.twin_start and forward_char in self.twin_end:
                # delete twins when backspacing starting char next to ending char
                if self.twin_start.index(back_char) == self.twin_end.index(forward_char):
                    buf.delete(cursor_iter, forward_iter)
            elif event.keyval in self.end_keyvals:
                # stop people from closing an already closed pair
                index = self.end_keyvals.index(event.keyval)
                if self.twin_end[index] == forward_char :
                    buf.delete(cursor_iter, forward_iter)
            elif event.keyval == 65293 and forward_char == '}':
                # add proper indentation when hitting before a closing bracket
                cursor_iter = buf.get_iter_at_mark(buf.get_insert ())
                line_start_iter = cursor_iter.copy()
                view.backward_display_line_start(line_start_iter)

                line = buf.get_text(line_start_iter, cursor_iter)
                preceding_white_space_pattern = re.compile(r'^(\s*)')
                groups = preceding_white_space_pattern.search(line).groups()
                preceding_white_space = groups[0]
                plen = len(preceding_white_space)

                buf.insert_at_cursor('\n')
                buf.insert_at_cursor(preceding_white_space)
                buf.insert_at_cursor('\n')

                cursor_mark = buf.get_insert()
                cursor_iter = buf.get_iter_at_mark(cursor_mark)

                buf.insert_at_cursor(preceding_white_space)

                cursor_mark = buf.get_insert()
                cursor_iter = buf.get_iter_at_mark(cursor_mark)

                for i in range(plen + 1):
                    if cursor_iter.backward_char():
                        buf.place_cursor(cursor_iter)
                if view.get_insert_spaces_instead_of_tabs():
                    buf.insert_at_cursor(' ' * view.get_tab_width())
                else:
                    buf.insert_at_cursor('\t')
                return True


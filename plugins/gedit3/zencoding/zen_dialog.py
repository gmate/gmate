# Zen Coding for Gedit
#
# Copyright (C) 2010 Franck Marcia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk

class ZenDialog():

    def __init__(self, editor, x, y, callback, text, last):

        self.editor = editor
        self.exit = False
        self.done = False
        self.abbreviation = text
        self.callback = callback
        self.last = last

        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_decorated(False)
        self.window.connect("destroy", self.quit)
        self.window.connect("focus-out-event", self.focus_lost)
        self.window.connect("key-press-event", self.key_pressed)
        self.window.set_resizable(False)
        self.window.move(x - 15, y - 35)

        self.frame = Gtk.Frame()
        self.window.add(self.frame)
        self.frame.show()

        self.box = Gtk.HBox()
        self.frame.add(self.box)
        self.box.show()
        
        self.entry = Gtk.Entry()
        self.entry.connect("changed", self.update)
        self.entry.set_text(text)
        self.entry.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, 'zencoding')
        self.entry.set_width_chars(48)
        self.box.pack_start(self.entry, True, True, 4)
        self.entry.show()

        self.window.show()

    def key_pressed(widget, what, event):
        if event.keyval == 65293: # Return
            widget.exit = True
            if widget.callback and widget.last:
                widget.done = widget.callback(widget.done, widget.abbreviation, True)
            widget.quit()
        elif event.keyval == 65289: # Tab
            widget.exit = True
            if widget.callback and widget.last:
                widget.done = widget.callback(widget.done, widget.abbreviation, True)
            widget.quit()
        elif event.keyval == 65307: # Escape
            widget.exit = False
            if widget.callback:
                widget.done = widget.callback(widget.done, '', True)
            widget.quit()
        else:
            return False
            
    def focus_lost(self, widget=None, event=None):
        self.exit = True
        self.quit()

    def update(self, entry):
        self.abbreviation = self.entry.get_text()
        if self.callback:
            self.done = self.callback(self.done, self.abbreviation)

    def quit(self, widget=None, event=None):
        self.window.hide()
        self.window.destroy()
        Gtk.main_quit()

    def main(self):
        Gtk.main()

def main(editor, window, callback, text = "", last = False):

    # ensure the caret is hidden
    editor.view.set_cursor_visible(False)

    # get coordinates of the cursor
    offset_start, offset_end = editor.get_selection_range()
    insert = editor.buffer.get_iter_at_offset(offset_start)
    location = editor.view.get_iter_location(insert)
    window = editor.view.get_window(Gtk.TextWindowType.TEXT)
    xo, yo, zo = window.get_origin()
    xb, yb = editor.view.buffer_to_window_coords(Gtk.TextWindowType.TEXT, location.x + location.width, location.y)

    # open dialog at coordinates with eventual text
    my_zen_dialog = ZenDialog(editor, xo + xb, yo + yb, callback, text, last)
    my_zen_dialog.main()

    # show the caret again
    editor.view.set_cursor_visible(True)

    # return exit status and abbreviation
    if callback:
        return my_zen_dialog.done and my_zen_dialog.exit, my_zen_dialog.abbreviation
    else:
        return my_zen_dialog.exit, my_zen_dialog.abbreviation


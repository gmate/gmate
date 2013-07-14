'''
@author Franck Marcia (franck.marcia@gmail.com)
'''

from gi.repository import Gtk

class ZenDialog():

    def __init__(self, editor, x, y, callback, text=""):

        self.editor = editor
        self.exit = False
        self.done = False
        self.abbreviation = text
        self.callback = callback

        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_decorated(False)
        self.window.connect("destroy", self.quit)
        self.window.connect("focus-out-event", self.focus_lost)
        self.window.connect("key-press-event", self.key_pressed)
        self.window.set_resizable(False)
        self.window.move(x, y - 27)

        self.frame = Gtk.Frame()
        self.window.add(self.frame)
        self.frame.show()

        self.box = Gtk.HBox(False, 0)
        self.frame.add(self.box)
        self.box.show()
        
        self.entry = Gtk.Entry()
        self.entry.connect("changed", self.update)
        self.entry.set_text(text)
        self.entry.set_has_frame(False)
        self.entry.set_width_chars(36)
        self.box.pack_start(self.entry, True, True, 4)
        self.entry.show()

        self.window.show()

    def key_pressed(widget, what, event):
        if event.keyval == 65293: # Return
            widget.exit = True
            widget.quit()
        elif event.keyval == 65289: # Tab
            widget.exit = True
            widget.quit()
        elif event.keyval == 65307: # Escape
            widget.exit = False
            widget.done = widget.callback(widget.done, '')
            widget.quit()
        else:
            return False
            
    def focus_lost(self, widget=None, event=None):
        self.exit = True
        self.quit()

    def update(self, entry):
        self.abbreviation = self.entry.get_text()
        self.done = self.callback(self.done, self.abbreviation)

    def quit(self, widget=None, event=None):
        self.window.hide()
        self.window.destroy()
        Gtk.main_quit()

    def main(self):
        Gtk.main()

def main(editor, window, callback, text=""):

    # Ensure the caret is hidden.
    editor.view.set_cursor_visible(False)
    
    # Get coordinates of the cursor.
    offset_start, offset_end = editor.get_selection_range()
    insert = editor.buffer.get_iter_at_offset(offset_start)
    location = editor.view.get_iter_location(insert)
    window = editor.view.get_window(Gtk.TextWindowType.TEXT)
    thing, xo, yo = window.get_origin()
    xb, yb = editor.view.buffer_to_window_coords(Gtk.TextWindowType.TEXT, location.x + location.width, location.y)

    # Open dialog at coordinates with eventual text.
    my_zen_dialog = ZenDialog(editor, xo + xb, yo + yb, callback, text)
    my_zen_dialog.main()

    # Show the caret again.
    editor.view.set_cursor_visible(True)

    # Return exit status and abbreviation.
    return my_zen_dialog.done and my_zen_dialog.exit, my_zen_dialog.abbreviation


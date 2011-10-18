# coding: utf8
# Copyright © 2011 Kozea
# Licensed under a 3-clause BSD license.

"""
Strip trailing whitespace before saving.

"""

from gi.repository import GObject, Gedit


class WhiteSpaceTerminator(GObject.Object, Gedit.WindowActivatable):
    """Strip trailing whitespace before saving."""
    window = GObject.property(type=Gedit.Window)

    def do_activate(self):
        self.handlers = []
        handler = self.window.connect("tab-added", self.on_tab_added)
        self.handlers.append((self.window, handler))
        for document in self.window.get_documents():
            document.connect("save", self.on_document_save)
            self.handlers.append((document, handler))

    def on_tab_added(self, window, tab, data=None):
        handler = tab.get_document().connect("save", self.on_document_save)
        self.handlers.append((tab, handler))

    def on_document_save(self, document, location, encoding, compression,
                         flags, data=None):
        for i, text in enumerate(document.props.text.rstrip().splitlines()):
            strip_stop = document.get_iter_at_line(i)
            strip_stop.forward_to_line_end()
            strip_start = strip_stop.copy()
            strip_start.backward_chars(len(text) - len(text.rstrip()))
            document.delete(strip_start, strip_stop)
        document.delete(strip_start, document.get_end_iter())

    def do_deactivate(self):
        for obj, handler in self.handlers:
            obj.disconnect(handler)

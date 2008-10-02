# Copyright (C) 2006-2008 Osmo Salomaa
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
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Automatically strip all trailing whitespace before saving."""

import gedit


class SaveWithoutTrailingSpacePlugin(gedit.Plugin):

    """Automatically strip all trailing whitespace before saving."""

    def activate(self, window):
        """Activate plugin."""

        handler_id = window.connect("tab-added", self.on_window_tab_added)
        window.set_data(self.__class__.__name__, handler_id)
        for doc in window.get_documents():
            self.connect_document(doc)

    def connect_document(self, doc):
        """Connect to document's 'saving' signal."""

        handler_id = doc.connect("saving", self.on_document_saving)
        doc.set_data(self.__class__.__name__, handler_id)

    def deactivate(self, window):
        """Deactivate plugin."""

        name = self.__class__.__name__
        handler_id = window.get_data(name)
        window.disconnect(handler_id)
        window.set_data(name, None)
        for doc in window.get_documents():
            handler_id = doc.get_data(name)
            doc.disconnect(handler_id)
            doc.set_data(name, None)

    def on_document_saving(self, doc, *args):
        """Strip trailing spaces in document."""

        doc.begin_user_action()
        self.strip_trailing_spaces_on_lines(doc)
        self.strip_trailing_blank_lines(doc)
        doc.end_user_action()

    def on_window_tab_added(self, window, tab):
        """Connect the document in tab."""

        name = self.__class__.__name__
        doc = tab.get_document()
        handler_id = doc.get_data(name)
        if handler_id is None:
            self.connect_document(doc)

    def strip_trailing_blank_lines(self, doc):
        """Delete trailing space at the end of the document."""

        buffer_end = doc.get_end_iter()
        if buffer_end.starts_line():
            itr = buffer_end.copy()
            while itr.backward_line():
                if not itr.ends_line():
                    itr.forward_to_line_end()
                    break
            doc.delete(itr, buffer_end)

    def strip_trailing_spaces_on_lines(self, doc):
        """Delete trailing space at the end of each line."""

        buffer_end = doc.get_end_iter()
        for line in range(buffer_end.get_line() + 1):
            line_end = doc.get_iter_at_line(line)
            line_end.forward_to_line_end()
            itr = line_end.copy()
            while itr.backward_char():
                if not itr.get_char() in (" ", "\t"):
                    itr.forward_char()
                    break
            doc.delete(itr, line_end)

# Copyright (C) 2009 Alexandre da Silva
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

"""Automatically detects if file resides in a ruby on rails application and set the properly language."""

import gedit, os

class RubyOnRailsLoader(gedit.Plugin):

    """Automatically strip all trailing whitespace before saving."""

    def activate(self, window):
        """Activate plugin."""
        self.window = window
        handler_id = window.connect("tab-added", self.on_window_tab_added)
        window.set_data(self.__class__.__name__, handler_id)
        for doc in window.get_documents():
            self.connect_document(doc)

    def connect_document(self, doc):
        """Connect to document's 'load' signal."""

        handler_id = doc.connect("loaded", self.on_document_load)
        doc.set_data(self.__class__.__name__, handler_id)


    def deactivate(self, window):
        """Deactivate plugin."""

        name = self.__class__.__name__
        handler_id = window.get_data(name)
        window.disconnect(handler_id)
        window.set_data(name, None)


    def on_window_tab_added(self, window, tab):
        """Connect the document in tab."""
        doc = tab.get_document()
        self.connect_document(doc)


    def on_document_load(self, doc, *args):
        language = doc.get_language()
        if language:
            lang = language.get_id()
            if lang == 'ruby':
                uri = doc.get_uri_for_display()
                if self.get_in_rails(uri):
                    lang = gedit.get_language_manager().get_language('rubyonrails')
                    doc.set_language(lang)
                    # Uggly workarroud to call update_ui
                    view = gedit.tab_get_from_document(doc).get_view()
                    editable = view.get_editable()
                    view.set_editable(not editable)
                    view.set_editable(editable)



    def get_in_rails(self, uri):
        rails_root = self.get_data('RailsLoaderRoot')
        if rails_root:
            return rails_root
        base_dir = os.path.dirname(uri)
        depth = 10
        while depth > 0:
            depth -= 1
            app_dir = os.path.join(base_dir, 'app')
            config_dir = os.path.join(base_dir, 'config')
            environment_file = os.path.join(base_dir, 'config', 'environment.rb')
            if os.path.isdir(app_dir) and os.path.isdir(config_dir) and os.path.isfile(environment_file):
                rails_root = base_dir
                break
            else:
                base_dir = os.path.abspath(os.path.join(base_dir, '..'))
        if rails_root:
            self.set_data('RailsLoaderRoot', rails_root)
            return True
        return False


    def set_data(self, name, value):
        self.window.get_active_tab().get_view().set_data(name, value)


    def get_data(self, name):
        return self.window.get_active_tab().get_view().get_data(name)


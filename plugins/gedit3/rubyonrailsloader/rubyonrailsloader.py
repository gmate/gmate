# Copyright (C) 2011 Hassan Zamani
# Thanks to Alexandre da Silva
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

import os
from gi.repository import GObject, Gedit, GtkSource

class RubyOnRailsLoader(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "RubyOnRailsLoader"
    name = __gtype_name__
    
    window = GObject.property(type=Gedit.Window)
    
    def __init__(self):
        GObject.Object.__init__(self)
    

    def do_activate(self):
        handler_id = self.window.connect("tab-added", self.on_tab_added)
        self.window.set_data(self.name,  handler_id)
        for doc in self.window.get_documents():
            self.connect_document(doc)


    def do_deactivate(self):
        handler_id = self.window.get_data(self.name)
        self.window.disconnect(handler_id)
        self.window.set_data(self.name, None)
    

    def do_update_state(self):
        pass
        

    def on_tab_added(self, window, tab):
        doc = tab.get_document()
        self.connect_document(doc)
        

    def connect_document(self, doc):
        """Connect to doc's `load` signal."""
        handler_id = doc.connect("loaded", self.on_document_load)
        doc.set_data(self.name, handler_id)
        

    def on_document_load(self, doc, *args):
        language = doc.get_language()
        if language:
            lang = language.get_id()
            if lang == 'ruby':
                uri = doc.get_uri_for_display()
                if self.get_in_rails(uri):
                    lang = GtkSource.LanguageManager.get_default().get_language('rubyonrails')
                    doc.set_language(lang)


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


# -*- coding: utf-8 -*-

#  Copyright (C) 2008 - Eugene Khorev
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330,
#  Boston, MA 02111-1307, USA.

import pygtk
pygtk.require("2.0")
import gtk
import gedit
import time
import os
import sys
import gettext
import ConfigParser
import bookmarks
import window_helper

APP_NAME = "plugin"
LOC_PATH = os.path.join(os.path.expanduser("~/.gnome2/gedit/plugins/advanced-bookmarks/lang"))

gettext.find(APP_NAME, LOC_PATH)
gettext.install(APP_NAME, LOC_PATH, True)

class AdvancedBookmarksPlugin(gedit.Plugin):

    def __init__(self):
        gedit.Plugin.__init__(self)
        
        self._instances = {}

        # Setup configuration file path
        conf_path = os.path.join(os.path.expanduser("~/.gnome2/gedit/plugins/"), "advanced-bookmarks/plugin.conf")
        
        # Check if configuration file does not exists
        if not os.path.exists(conf_path):
            # Create configuration file
            conf_file = file(conf_path, "wt")
            conf_file.close()
            
        # Create configuration dictionary
        self.read_config(conf_path)

        # Create bookmark list
        self._bookmarks = bookmarks.bookmark_list(self._config)
        
    def activate(self, window):
        # Create window helper for an instance
        self._instances[window] = window_helper.window_helper(self, window, self._bookmarks, self._config)
        
    def deactivate(self, window):
        self._instances[window].deactivate()
        del self._instances[window]
        
    def update_ui(self, window):
        self._instances[window].update_ui()
                        
    def create_configure_dialog(self):
        # Create configuration dialog
        self._dlg_config_glade = gtk.glade.XML(os.path.dirname( __file__ ) + "/config_dlg.glade")

        # Get dialog window
        self._dlg_config = self._dlg_config_glade.get_widget("config_dialog") 
        
        # Setup signals
        self._dlg_config_glade.signal_autoconnect(self)
        
        # Setup values of dialog widgets
        highlighting = self._config.getboolean("common", "highlighting")
        chk = self._dlg_config_glade.get_widget("chk_highlight")
        chk.set_active(highlighting)
        
        color = self._config.get("common", "highlight_color")
        btn = self._dlg_config_glade.get_widget("btn_color")
        try:
            btn.set_color(gtk.gdk.color_parse(color))
        except:
            btn.set_color(gtk.gdk.color_parse("#FFF0DC"))
        
        return self._dlg_config
        
    def on_btn_cancel_clicked(self, btn):
        self._dlg_config.response(gtk.RESPONSE_CANCEL)
        
    def on_btn_ok_clicked(self, btn):
        self._dlg_config.response(gtk.RESPONSE_OK)
        
    def on_config_dialog_response(self, dlg, res):
        if res == gtk.RESPONSE_OK:
            # Save configuration
            highlight = self._dlg_config_glade.get_widget("chk_highlight").get_active()
            self._config.set("common", "highlighting", highlight and "on" or "off")
            
            color = self._dlg_config_glade.get_widget("btn_color").get_color().to_string()
            self._config.set("common", "highlight_color", color)
            
            self.write_config()
            
            # Remove bookmark markup in all documents if necessary
            for window in self._instances:
                self._instances[window].setup_highlighting(highlight)
            
        dlg.hide()
            
    def read_config(self, conf_path): # Reads configuration from a file
        self._conf_file = file(conf_path, "r+")
        self._config = ConfigParser.ConfigParser()
        self._config.readfp(self._conf_file)
        
        # Check if there is no necessary options in config
        if not self._config.has_section("common"):
            self._config.add_section("common")
        
        if not self._config.has_option("common", "highlighting"):
            self._config.set("common", "highlighting", "on")
        
        if not self._config.has_option("common", "highlight_color"):
            self._config.set("common", "highlight_color", "#FFF0DC")
        
    def write_config(self): # Saves configuration to a file
        self._conf_file.truncate(0)
        self._conf_file.seek(0)

        self._config.write(self._conf_file)
        
#ex:ts=4:et:

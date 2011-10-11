# -*- coding: utf-8 -*-
#
#  textsize.py - Change text size plugin
#
#  Copyright (C) 2008 - Konstantin Mikhaylov <jtraub.devel@gmail.com>
#  Copyright (C) 2009 - Wouter Bolsterlee <wbolster@gnome.org>
#  Copyright (C) 2010 - Ignacio Casal Quinteiro <icq@gnome.org>
#  Copyright (C) 2010 - Jesse van den Kieboom <jessevdk@gnome.org>
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

import gtk
from gettext import gettext as _
import constants
from documenthelper import DocumentHelper
from signals import Signals

# UI manager snippet to add menu items to the View menu
ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="ViewMenu" action="View">
      <placeholder name="ViewOps_2">
        <menuitem name="IncreaseFontSize" action="IncreaseFontSizeAction"/>
        <menuitem name="DecreaseFontSize" action="DecreaseFontSizeAction"/>
        <menuitem name="ResetFontSize" action="ResetFontSizeAction"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class WindowHelper(Signals):
    def __init__(self, plugin, window):
        Signals.__init__(self)

        self._window = window
        self._plugin = plugin
        self._views  = {}

        # Insert menu items
        self._insert_menu()

        # Insert document helpers
        for view in window.get_views():
            self.add_document_helper(view)

        self.connect_signal(window, 'tab-added', self.on_tab_added)
        self.connect_signal(window, 'tab-removed', self.on_tab_removed)

        self._accel_group = gtk.AccelGroup()
        self._window.add_accel_group(self._accel_group)

        self._proxy_callback_map = {
            'IncreaseFontSizeAction': self.on_increase_font_accel,
            'DecreaseFontSizeAction': self.on_decrease_font_accel,
            'ResetFontSizeAction': self.on_reset_font_accel
        }

        self._proxy_mapping = {}
        self._init_proxy_accels()
        self._accel_map_handler_id = gtk.accel_map_get().connect('changed', self.on_accel_map_changed)

    def _install_proxy(self, action):
        if not isinstance(action, gtk.Action):
            action = self._action_group.get_action(str(action))

        if not action:
            return

        entry = gtk.accel_map_lookup_entry(action.get_accel_path())

        if not entry:
            return

        mapping = {
            gtk.keysyms.plus: gtk.keysyms.KP_Add,
            gtk.keysyms.KP_Add: gtk.keysyms.plus,
            gtk.keysyms.minus: gtk.keysyms.KP_Subtract,
            gtk.keysyms.KP_Subtract: gtk.keysyms.minus,
            gtk.keysyms._0: gtk.keysyms.KP_0,
            gtk.keysyms.KP_0: gtk.keysyms._0
        }

        if entry[0] in mapping:
            key = mapping[entry[0]]
            mod = entry[1]

            callback = self._proxy_callback_map[action.get_name()]

            self._accel_group.connect_group(key, mod, gtk.ACCEL_LOCKED, callback)
            self._proxy_mapping[action] = (key, mod)

    def _init_proxy_accels(self):
        self._install_proxy('IncreaseFontSizeAction')
        self._install_proxy('DecreaseFontSizeAction')
        self._install_proxy('ResetFontSizeAction')

    def deactivate(self):
        # Remove any installed menu items
        self._remove_menu()

        for view in self._window.get_views():
            self.remove_document_helper(view)

        self._window.remove_accel_group(self._accel_group)

        gtk.accel_map_get().disconnect(self._accel_map_handler_id)

        self._window = None
        self._plugin = None
        self._accel_group = None
        self._action_group = None

    def _insert_menu(self):
        # Get the GtkUIManager
        manager = self._window.get_ui_manager()

        # Create a new action group
        self._action_group = gtk.ActionGroup("TextSizePluginActions")
        self._action_group.add_actions([("IncreaseFontSizeAction", None, _("_Increase font size"),
                                         "<Ctrl>plus", None,
                                         self.on_increase_font_size_activate),
                                         ("DecreaseFontSizeAction", None, _("_Decrease font size"),
                                         "<Ctrl>minus", None,
                                         self.on_decrease_font_size_activate),
                                         ("ResetFontSizeAction", None, _("_Reset font size"),
                                         "<Ctrl>0", None,
                                         self.on_reset_font_size_activate)])

        # Insert the action group
        manager.insert_action_group(self._action_group, -1)

        # Merge the UI
        self._ui_id = manager.add_ui_from_string(ui_str)

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

    def get_helper(self, view):
        return view.get_data(constants.DOCUMENT_HELPER_KEY)

    def add_document_helper(self, view):
        if self.get_helper(view) != None:
            return

        DocumentHelper(view)

    def remove_document_helper(self, view):
        helper = self.get_helper(view)

        if helper != None:
            helper.stop()

    def call_helper(self, cb):
        view = self._window.get_active_view()

        if view:
            cb(self.get_helper(view))

    # Menu activate handlers
    def on_increase_font_size_activate(self, action):
        self.call_helper(lambda helper: helper.increase_font_size())

    def on_decrease_font_size_activate(self, action):
        self.call_helper(lambda helper: helper.decrease_font_size())

    def on_reset_font_size_activate(self, action):
        self.call_helper(lambda helper: helper.reset_font_size())

    def on_increase_font_accel(self, group, accel, key, mod):
        self.call_helper(lambda helper: helper.increase_font_size())

    def on_decrease_font_accel(self, group, accel, key, mod):
        self.call_helper(lambda helper: helper.decrease_font_size())

    def on_reset_font_accel(self, group, accel, key, mod):
        self.call_helper(lambda helper: helper.reset_font_size())

    def on_tab_added(self, window, tab):
        self.add_document_helper(tab.get_view())

    def on_tab_removed(self, window, tab):
        self.remove_document_helper(tab.get_view())

    def _remap_proxy(self, action):
        # Remove previous proxy

        if action in self._proxy_mapping:
            item = self._proxy_mapping[action]
            self._accel_group.disconnect_key(item[0], item[1])

        self._install_proxy(action)

    def on_accel_map_changed(self, accelmap, path, key, mod):
        for action in self._action_group.list_actions():
            if action.get_accel_path() == path:
                self._remap_proxy(action)
                return

# ex:ts=4:et:

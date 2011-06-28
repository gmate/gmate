# -*- coding: utf-8 -*-
#
# Zoom - gedit plugin
# Copyright (C) 2010 Christian Luginbühl
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import os

from view_helper import ViewHelper
from localization import Localization

class WindowHelper:
    """Adding ability to change the size of the text."""

    _UI_FILE = os.path.join(os.path.dirname(__file__), 'zoom_menu.ui.xml')

    # defining the accelerators for the different "actions". the first entry
    # is used as the one that generates the accelerator name in the menu
    _ENLARGE_ACCELERATORS = ['<Ctrl>plus', '<Ctrl>equal', '<Ctrl>KP_Add']
    _SHRINK_ACCELERATORS = ['<Ctrl>minus', '<Ctrl>KP_Subtract']
    _RESET_ACCELERATORS = ['<Ctrl>0', '<Ctrl>KP_0', '<Ctrl>KP_Insert']

    def __init__(self, window):
        """Constructor."""
        self._window = window
        self._views = {}

        self._action_group = None
        self._ui_id = None
        self._accel_group = None

        Localization.setup()

        self._insert_menu()
        self._setup_supplementary_accelerators()

        for view in self._window.get_views():
            self._initialize_viewhelper(view)

        self._tab_add_handler = self._window.connect('tab-added',
                                                     self._on_tab_added)
        self._tab_remove_handler = self._window.connect('tab-removed',
                                                        self._on_tab_removed)

    def deactivate(self):
        """Deactivates the plugin for a window."""
        for view in self._window.get_views():
            self._deactivate_viewhelper(view)

        self._views = None

        self._remove_menu()
        self._window.remove_accel_group(self._accel_group)
        self._window.disconnect(self._tab_add_handler)
        self._window.disconnect(self._tab_remove_handler)

        self._plugin = None
        self._window = None

    def update_ui(self):
        """Reacts on user interface updates for a window."""
        self._action_group.set_sensitive(self._has_active_view())

    def _insert_menu(self):
        """Adds the menu entries for zooming."""
        manager = self._window.get_ui_manager()

        self._action_group = gtk.ActionGroup('ZoomPluginActions')

        action_submenu = gtk.Action('ZoomSubMenu',
                                    _('_Zoom'),
                                    _('_Zoom'),
                                    None)

        action_enlarge_font = gtk.Action('EnlargeFont',
                                         _('Zoom _In'),
                                         _('Zoom _In'),
                                         None)
        action_enlarge_font.connect('activate', self._enlarge_font)

        action_shrink_font = gtk.Action('ShrinkFont',
                                        _('Zoom _Out'),
                                        _('Zoom _Out'),
                                        None)
        action_shrink_font.connect('activate', self._shrink_font)

        action_reset_font = gtk.Action('OriginalSize',
                                       _('_Reset'),
                                       _('_Reset'),
                                       None)
        action_reset_font.connect('activate', self._reset_font)

        self._action_group.add_action(action_submenu)

        self._action_group.add_action_with_accel(
                               action_enlarge_font,
                               self.__class__._ENLARGE_ACCELERATORS[0])
        self._action_group.add_action_with_accel(
                               action_shrink_font,
                               self.__class__._SHRINK_ACCELERATORS[0])
        self._action_group.add_action_with_accel(
                               action_reset_font,
                               self.__class__._RESET_ACCELERATORS[0])

        manager.insert_action_group(self._action_group)

        self._ui_id = manager.add_ui_from_file(self.__class__._UI_FILE)

    def _remove_menu(self):
        """Removes the additional menu entries."""
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)

        manager.ensure_update()

    def _setup_supplementary_accelerators(self):
        """Adds all supplementary accelerators to the main window."""
        self._accel_group = gtk.AccelGroup()
        self._window.add_accel_group(self._accel_group)

        self._connect_accelerators(self.__class__._ENLARGE_ACCELERATORS[1:],
                                   self._enlarge_font)
        self._connect_accelerators(self.__class__._SHRINK_ACCELERATORS[1:],
                                   self._shrink_font)
        self._connect_accelerators(self.__class__._RESET_ACCELERATORS[1:],
                                   self._reset_font)

    def _connect_accelerators(self, accelerator_list, callback_function):
        """Connects accelerators from a list to a callback."""
        for accelerator in accelerator_list:
            key, mod = gtk.accelerator_parse(accelerator)
            self._accel_group.connect_group(key, mod, 0, callback_function)

    def _on_tab_added(self, window, tab):
        """Callback on new tab added."""
        self._initialize_viewhelper(tab.get_view())

    def _on_tab_removed(self, window, tab):
        """Callback on tab removal - deactivates the ViewHelper."""
        self._deactivate_viewhelper(tab.get_view())

    def _initialize_viewhelper(self, view):
        """Initializes a ViewHelper for view if unknown as of now."""
        if (view and (not view in self._views)):
            self._views[view] = ViewHelper(view)

    def _deactivate_viewhelper(self, view):
        """Deactivates the ViewHelper of view if known."""
        if (view and (view in self._views)):
            self._views[view].deactivate()
            del self._views[view]

    # below are the callbacks that are used for both action and accelerators
    # from the main window. because they have a different method signature
    # but none of the arguments are used, this quite ugly looking all-catching
    # agrs-attribute is used for both.

    def _enlarge_font(self, *args):
        """Callback to enlarge the font on menu click or accelerator."""
        if (self._has_active_view()):
            self._get_active_viewhelper().enlarge_font()

    def _shrink_font(self, *args):
        """Callback to shrink the font on menu click or main accelerator."""
        if (self._has_active_view()):
            self._get_active_viewhelper().shrink_font()

    def _reset_font(self, *args):
        """Callback to reset the font on menu click or main accelerator."""
        if (self._has_active_view()):
            self._get_active_viewhelper().reset_font()

    def _has_active_view(self):
        """Returns 'true' if there is an active view."""
        return (self._window.get_active_view() != None)

    def _get_active_viewhelper(self):
        """Returns the ViewHelper of the active view."""
        return self._views[self._window.get_active_view()]

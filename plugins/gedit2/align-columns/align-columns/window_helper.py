# Align columns - Gedit plugin
#
# Copyright (c) 2011 Hugo Henriques Maia Vieira
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
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

from localization import Localization

from text_block import TextBlock, DifferentNumberOfColumnsError, WhiteSpacesError

class WindowHelper:
    """Align text blocks into columns separated by pipe ( | )"""

    _UI_FILE = os.path.join(os.path.dirname(__file__), 'align_columns_menu.ui.xml')

    def __init__(self, window):
        """Constructor."""
        self._window = window
        self._action_group = None
        Localization.setup()
        self._insert_menu()

    def deactivate(self):
        """Deactivates the plugin for a window."""
        self._remove_menu()
        self._window = None
        self._action_group = None

    def update_ui(self):
        """Reacts on user interface updates for a window."""
        self._action_group.set_sensitive(self._has_active_view())

    def _insert_menu(self):
        """Adds the menu entries."""
        manager = self._window.get_ui_manager()

        self._action_group = gtk.ActionGroup("AlignColumnsActions")

        action_align_columns = gtk.Action("AlignColumns",
                                          _("Align columns"),
                                          _("Align columns"),
                                          None)
        action_align_columns.connect('activate', self.on_align_columns_activate)

        self._action_group.add_action_with_accel(action_align_columns,
                                                 '<Shift><Alt>a')

        manager.insert_action_group(self._action_group)

        # Merge the UI
        self._ui_id = manager.add_ui_from_file(self.__class__._UI_FILE)

    def _remove_menu(self):
        """Removes the additional menu entries."""
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()

    def on_align_columns_activate(self, action):
        """Callback to align columns on menu click or accelerator."""
        doc = self._window.get_active_document()
        bounds = doc.get_selection_bounds()

        if not doc or not bounds:
            return

        text = doc.get_text(*bounds)
        try:
            text_block = TextBlock(text)
            aligned_columns = text_block.align()
            doc.delete_interactive(*bounds, default_editable=True)
            doc.insert(bounds[0], aligned_columns)
        except WhiteSpacesError:
            return
        except DifferentNumberOfColumnsError:
            message = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                        'The selection has lines with different numbers of columns.')
            message.run()
            message.destroy()

    def _has_active_view(self):
        """Returns 'true' if there is an active view."""
        return (self._window.get_active_view() != None)


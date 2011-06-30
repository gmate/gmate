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

import gedit

from window_helper import WindowHelper

class AlignColumnsPlugin(gedit.Plugin):
    """Align text blocks into columns separated by pipe ( | )"""

    def __init__(self):
        """Constructor."""
        gedit.Plugin.__init__(self)
        self._instances = {}

    def activate(self, window):
        """Activate the plugin for a window."""
        self._instances[window] = WindowHelper(window)

    def deactivate(self, window):
        """Deactivate the plugin for a window."""
        self._instances[window].deactivate()
        del self._instances[window]

    def update_ui(self, window):
        """Update the user interface for a window."""
        self._instances[window].update_ui()


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

class FontsizeManipulator:
    """Manipulates the fontsize of a specific view."""

    ZOOM_STEP = 1.090507733 # sqrt(sqrt(sqrt(2)))
    # allowing 16 steps in both directions, 25% - 400% of original size (with
    # a little extra range to deal with rounding errors)
    ZOOM_MAX = 4.1
    ZOOM_MIN = 0.24

    def __init__(self, view):
        """Constructor."""
        self._view = view
        self._context = self._view.get_pango_context()
        self._fontdescription = self._context.get_font_description()

        self._zoomlevel = 1.0

        self._original_fontsize = self._get_pango_fontsize()

    def enlarge(self):
        """Enlarges the font up to a defined maximum."""
        new_zoomlevel = self._zoomlevel * self.__class__.ZOOM_STEP
        if (new_zoomlevel < self.__class__.ZOOM_MAX):
            self._zoomlevel = new_zoomlevel
            self._update_font()

    def shrink(self):
        """Shrinks the font down to a defined minimum."""
        new_zoomlevel = self._zoomlevel / self.__class__.ZOOM_STEP
        if (new_zoomlevel > self.__class__.ZOOM_MIN):
            self._zoomlevel = new_zoomlevel
            self._update_font()

    def reset(self):
        """Resets the font to its original size."""
        self._zoomlevel = 1.0
        self._update_font()

    def _update_font(self):
        """Does the actual change of the font in the view."""
        self._fontdescription.set_size(self._calculate_pango_fontsize())
        self._view.set_font(False, self._get_fontname())

    def _calculate_pango_fontsize(self):
        """Calculate the fontsize based on original size and zoomlevel."""
        return int(self._original_fontsize * self._zoomlevel)

    def _get_fontname(self):
        """Returns the fontname to be used in gedit.View.set_font."""
        return self._fontdescription.to_string()

    def _get_pango_fontsize(self):
        """Gets the current font size in pango units."""
        return self._fontdescription.get_size()

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

from fontsize_manipulator import FontsizeManipulator

class ViewHelper:
    """Controls a specific view for font manipulation."""

    def __init__(self, view):
        """Constructor."""
        self._view = view
        self._scroll_handler = self._view.connect('scroll_event',
                                                  self._on_scrolling)
        self._fontsize_manipulator = FontsizeManipulator(self._view)

    def deactivate(self):
        """Resets the font and disconnects the scroll-event."""
        self.reset_font()
        self._view.disconnect(self._scroll_handler)

    def _on_scrolling(self, view, event):
        """Callback on scroll wheel movement."""
        event_consumed = False

        if (event.state & gtk.gdk.CONTROL_MASK):
            if event.direction == gtk.gdk.SCROLL_UP:
                self.enlarge_font()
                event_consumed = True
            elif event.direction == gtk.gdk.SCROLL_DOWN:
                self.shrink_font()
                event_consumed = True
        return event_consumed

    def enlarge_font(self):
        """Enlarges the font of this view."""
        self._fontsize_manipulator.enlarge()

    def shrink_font(self):
        """Shrinks the font of this view."""
        self._fontsize_manipulator.shrink()

    def reset_font(self):
        """Resets the font of this view to ist original size."""
        self._fontsize_manipulator.reset()

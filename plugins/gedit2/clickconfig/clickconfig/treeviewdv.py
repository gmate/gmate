# -*- coding: utf8 -*-
#  TreeViewDV
#
#  Copyright (C) 2010 Derek Veit
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module provides a subclass of a GTK TreeView with improved behavior for
drag-and-drop of multiple selections.

Problem:    When multiple rows are selected in a TreeView and a row is clicked
            (without the Shift key) to start dragging them, the row clicked is
            selected individually and the rest of the selection is deselected.
            The multiple selection can sometimes be dragged by holding down the
            Shift key while dragging, but the results are unpredictable in many
            cases because clicking with the Shift will still cause a select
            action.  And dragging a multiple-row selection that has a
            non-continuous set of rows, i.e. a selection made using the Control
            key, is not even possible because of this.

Solution:   Make selection happen on button releases instead of button presses,
            and if the mouse has moved while the button is pressed, allow for
            dragging (for drag-and-drop) or rubberbanding (drag selecting)
            depending on whether the clicked row is already selected.
            1.  Use TreeSelection.set_select_function() to make the select
                action subject to a boolean instance attribute, 'selectable'.
            2.  Connect a handler to the TreeView's button-press-event signal.
            3.  If a (left) button-press-event happens, use the 'selectable'
                    attribute to prevent the default selection action, connect
                    a handler to the button-release-event signal, and...
                a.  If the clicked row is selected, connect a handler to the
                    drag-begin signal.
                b.  If the clicked row is not selected, connect a handler to
                    the motion-notify-event signal.
            4.  If a button-release-event happens, normal selecting is
                intended, so re-enable normal selecting, disconnect any event
                handlers and select rows as appropriate for the click.
            5.  If a drag-begin happens, the unwanted selecting has been
                avoided, so re-enable normal selecting and disconnect any
                event handlers.
            6.  If a motion-notify-event happens, rubberbanding may start, so
                re-enable normal selecting and disconnect any event handlers.

Additionally, in a drag-and-drop, gtk.TreeView only shows a drag icon
representing the clicked row, even if the selection is of multiple rows.  This
subclass replaces the default single-row drag icon with a multiple-row icon.

Classes:
TreeViewDV -- This can be used in place of a gtk.TreeView.

"""

import logging
import os
import sys

import gtk

class TreeViewDV(gtk.TreeView):
    
    """
    This can be used in place of a gtk.TreeView.
    
    Usage:
        from treeviewdv import TreeViewDV
        treeview = TreeViewDV()
      or
        treeview = TreeViewDV(model)
    
    """
    
    def __init__(self, model=None):
        """
        """
        gtk.TreeView.__init__(self, model)
        
        instance_id = repr(self)
        self.logger = logging.getLogger('Logger of ' + instance_id)
        handler = logging.StreamHandler(sys.stdout)
        log_format = "%(levelname)s - %(message)s"
        #log_format = "%(asctime)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.WARNING)
        self.log('TreeViewDV logging started. '.ljust(72, '-'))
        self.log(self.logger.name)
        self.log()

        self.selectable = True
        """If False, GTK will not select rows in response to clicks."""
        
        self.anchor_path = None
        """Identifies the row at the start of a multiple-row selection."""
        
        self.button_release_handlerid = None
        """The handler id for the button-release-event handler."""
        
        self.drag_begin_handlerid = None
        """The handler id for the drag-begin handler."""
        
        self.motion_notify_handlerid = None
        """The handler id for the motion-notify-event handler."""
        
        self.press_x = 0
        """Pointer x location (in tree coordinates) at button press."""
        
        self.press_y = 0
        """Pointer y location (in tree coordinates) at button press."""
        
        treeselection = self.get_selection()
        treeselection.set_select_function(lambda info: self.selectable)
        
        self.connect('button-press-event', self.on_button_press)
        
        self.connect_after('drag-begin', self.after_drag_begin)
    
    # Event handlers
    
    def on_button_press(self, widget, event):
        """
        1.  If the Shift key is not pressed, set the anchor for any future
            multiple-row selections with the Shift key.
        2.  Allow either for dragging or for rubberbanding.
        """
        self.log()
        if event.button == 1:
            path = self._get_path_of_event(event)
            if not path:
                return
            # 1. Set the anchor for future multiple-row selections.
            state = event.get_state()
            with_shift = state & gtk.gdk.SHIFT_MASK
            if not with_shift:
                self.anchor_path = path
            # 2. Allow either for dragging or for rubberbanding.
            treeselection = self.get_selection()
            is_selected = treeselection.path_is_selected(path)
            self._disable_gtk_selecting()
            if is_selected:
                self._set_press_coords(event)
                self._prepare_for_dragging()
            else:
                self._prepare_for_rubberbanding()
    
    def _set_press_coords(self, event):
        widget_x, widget_y = event.get_coords()
        self.press_x, self.press_y = \
            self.convert_widget_to_tree_coords(int(widget_x), int(widget_y))
    
    def on_button_release(self, widget, event):
        """Allow normal GTK selecting and make the selection for the click."""
        self.log()
        self._enable_gtk_selecting()
        self._select_with_event(event)
    
    def on_drag_begin(self, widget, drag_context):
        """Allow normal GTK selecting again after this drag."""
        self.log()
        self._enable_gtk_selecting()
    
    def after_drag_begin(self, widget, drag_context):
        """Allow normal GTK selecting again after this drag."""
        self.log()
        self._set_drag_icon(drag_context)
    
    def _set_drag_icon(self, drag_context):
        self.log()
        treeselection = self.get_selection()
        if not treeselection.count_selected_rows():
            return
        pixmap = self._create_rows_drag_icon()
        width, height = pixmap.get_size()
        hot_x, hot_y = self.press_x, self.press_y
        pixbuf = gtk.gdk.Pixbuf(
            colorspace=gtk.gdk.COLORSPACE_RGB,
            has_alpha=False,
            bits_per_sample=8,
            width=width,
            height=height)
        pixbuf.get_from_drawable(
            src=pixmap,
            cmap=pixmap.get_colormap(),
            src_x=0,
            src_y=0,
            dest_x=0,
            dest_y=0,
            width=width,
            height=height)
        pixbuf = pixbuf.add_alpha(
            substitute_color=True,
            r=chr(1),
            g=chr(1),
            b=chr(1))
        drag_context.set_icon_pixbuf(pixbuf=pixbuf, hot_x=hot_x, hot_y=hot_y)
    
    def on_motion_notify(self, widget, event):
        """Allow normal GTK selecting again after this drag."""
        self.log()
        self._enable_gtk_selecting()
        self._select_with_event(event)
    
    # Event handler control methods (modes)
    
    def _enable_gtk_selecting(self):
        self.log()
        """Allow normal GTK selecting."""
        if self.button_release_handlerid:
            self.disconnect(self.button_release_handlerid)
            self.button_release_handlerid = None
        if self.drag_begin_handlerid:
            self.disconnect(self.drag_begin_handlerid)
            self.drag_begin_handlerid = None
        if self.motion_notify_handlerid:
            self.disconnect(self.motion_notify_handlerid)
            self.motion_notify_handlerid = None
        self.selectable = True
    
    def _disable_gtk_selecting(self):
        """Prevent normal GTK selecting and prepare for button release."""
        self.log()
        if not self.button_release_handlerid:
            self.button_release_handlerid = self.connect(
                'button-release-event', self.on_button_release)
        self.selectable = False
    
    def _prepare_for_dragging(self):
        """Allow for dragging of multiple-row selections."""
        self.log()
        if not self.drag_begin_handlerid:
            self.drag_begin_handlerid = self.connect(
                'drag-begin', self.on_drag_begin)
    
    def _prepare_for_rubberbanding(self):
        """Allow for dragging of multiple-row selections."""
        self.log()
        if not self.motion_notify_handlerid:
            self.motion_notify_handlerid = self.connect(
                'motion-notify-event', self.on_motion_notify)
    
    # Selection methods
    
    def _get_path_of_event(self, event):
        """Return the path (row) where the event (mouse click) occurred."""
        x, y = event.get_coords()
        path_etc = self.get_path_at_pos(int(x), int(y))
        if path_etc:
            path = path_etc[0]
            return path
    
    def _select_with_event(self, event):
        """Select and deselect rows based on the click event."""
        self.log()
        treeselection = self.get_selection()
        path = self._get_path_of_event(event)
        if not path:
            return
        is_selected = treeselection.path_is_selected(path)
        state = event.get_state()
        with_shift = state & gtk.gdk.SHIFT_MASK
        with_control = state & gtk.gdk.CONTROL_MASK
        if with_control:
            if with_shift:
                treeselection.select_range(self.anchor_path, path)
            else:
                if is_selected:
                    treeselection.unselect_path(path)
                else:
                    treeselection.select_path(path)
        else:
            if with_shift:
                treeselection.unselect_all()
                treeselection.select_range(self.anchor_path, path)
            else:
                treeselection.unselect_all()
                treeselection.select_path(path)
    
    # Miscellaneous methods
    
    def log(self, message=None, level='debug'):
        """Log the message or log the calling function."""
        if message:
            logger = {'debug': self.logger.debug,
                      'info': self.logger.info,
                      'warning': self.logger.warning,
                      'error': self.logger.error,
                      'critical': self.logger.critical}[level]
            logger(message)
        else:
            self.logger.debug(self._whoami())
    
    def _whoami(self):
        """Identify the calling function for logging."""
        filename = os.path.basename(sys._getframe(2).f_code.co_filename)
        line = sys._getframe(2).f_lineno
        class_name = sys._getframe(2).f_locals['self'].__class__.__name__
        function_name = sys._getframe(2).f_code.co_name
        return '%s Line %s %s.%s' % (filename, line, class_name, function_name)
    
    def _create_rows_drag_icon(self):
        """Create a multiple-row drag icon."""
        self.log()
        treeselection = self.get_selection()
        paths = [row[0] for row in treeselection.get_selected_rows()[1]]
        row_pixmaps = [self.create_row_drag_icon(path)
                       for path in paths]
        first_pixmap = row_pixmaps[0]
        row_width, row_height = first_pixmap.get_size()
        width = row_width
        height = (self._get_row_y(paths[-1]) -
                  self._get_row_y(paths[0]) +
                  row_height)
        pixmap = gtk.gdk.Pixmap(first_pixmap, width, height)
        pixmap_gc = gtk.gdk.GC(first_pixmap)
        # Clear the new Pixmap before drawing on it:
        pixmap_gc.set_rgb_fg_color(gtk.gdk.Color(256, 256, 256))
        pixmap_gc.set_function(gtk.gdk.COPY)
        pixmap.draw_rectangle(
            gc=pixmap_gc,
            filled=True,
            x=0,
            y=0,
            width=width,
            height=height)
        for index, row_pixmap in enumerate(row_pixmaps):
            # Copy the row icon onto the full image
            ydest = self._get_row_y(paths[index]) - self._get_row_y(paths[0])
            pixmap_gc.set_function(gtk.gdk.COPY)
            pixmap.draw_drawable(
                gc=pixmap_gc,
                src=row_pixmap,
                xsrc=0,
                ysrc=0,
                xdest=0,
                ydest=ydest,
                width=row_width,
                height=row_height)
        self.press_y -= self._get_row_y(paths[0])
        return pixmap
    
    def _get_row_y(self, path):
        """Return y tree coordinate of the top of cell at path."""
        column = self.get_column(0)
        cell_area = self.get_cell_area(path, column)
        x, y = self.convert_widget_to_tree_coords(cell_area.x, cell_area.y)
        return y
    
    # Public methods
    
    def remove_from_treeview(treeview, row):
        """Remove the row from the TreeView."""
        treemodel = treeview.get_model()
        treemodel_list = self._get_list_from_liststore(liststore)
        path = liststore_list.index(value)
        iter_ = liststore.get_iter(path)
        liststore.remove(iter_)
        if len(liststore) == 0:
            treeview.set_property('can-focus', False)
    
    def add_to_treeview(treeview, row):
        """Add the row to the TreeView."""
        liststore = treeview.get_model()
        liststore_list = self._get_list_from_liststore(liststore)
        liststore_list.append(value)
        liststore_list.sort()
        path = liststore_list.index(value)
        if path == len(liststore):
            liststore.append([value])
        else:
            iter_ = liststore.get_iter(path)
            liststore.insert_before(iter_, row=[value])
        treeview.set_property('can-focus', True)
    


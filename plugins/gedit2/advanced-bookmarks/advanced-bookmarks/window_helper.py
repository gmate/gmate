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
import pango
import bookmarks
import toggle_dlg

class window_helper:
    def __init__(self, plugin, window, bookmarks, config):
        self._window = window
        self._plugin = plugin
        
        self._bookmarks = bookmarks
        self._config = config
        
        self._doc_lines = {}

        # Create icon
        self._icon = gtk.Image()
        self._icon.set_from_icon_name('stock_help-add-bookmark', gtk.ICON_SIZE_MENU)
        
        # Insert main menu items
        self._insert_menu()
        
        # Create bookmark toggle dialog
        self._dlg_toggle = toggle_dlg.toggle_dlg(None, self._config)
        self._dlg_toggle.connect("response", self._on_dlg_toggle_response)
        
        # Create bottom pane tree
        self._tree = gtk.TreeView()
        
        # Create line number column
        self._line_column = gtk.TreeViewColumn(_('Line'))
        self._tree.append_column(self._line_column)
        
        self._line_cell = gtk.CellRendererText()
        self._line_column.pack_start(self._line_cell, True)

        self._line_column.add_attribute(self._line_cell, 'text', 0)
        
        # Create comment column
        self._comment_column = gtk.TreeViewColumn(_('Source / Comment'))
        self._tree.append_column(self._comment_column)
        
        self._comment_cell = gtk.CellRendererText()
        self._comment_column.pack_start(self._comment_cell, True)

        self._comment_column.add_attribute(self._comment_cell, 'text', 1)
        self._comment_column.set_cell_data_func(self._comment_cell, self._render_comment_callback)
        
        # Addtitional settings
        self._tree.set_enable_tree_lines(True)
        self._tree.set_search_column(1)
        self._tree.set_rules_hint(True)
        self._tree.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        
        # Create bottom pane
        self._pane = gtk.ScrolledWindow()

        # Add tree to bottom pane
        self._pane.add(self._tree);
        self._tree.show()

        # Setup row selection event
        self._tree.connect("row-activated", self._on_row_activated)
        self._tree.connect("cursor-changed", self._on_row_selected)
        self._tree.connect("focus-in-event", self._on_tree_focused)

        # Create popup menu for tree
        self._popup_menu = gtk.Menu()
        
        self._pop_toggle = gtk.MenuItem(_("Toggle bookmark"))
        self._pop_toggle.connect("activate", self._on_toggle_bookmark)
        self._pop_toggle.show()
        self._popup_menu.append(self._pop_toggle)
        
        self._pop_edit = gtk.MenuItem(_("Edit bookmark"))
        self._pop_edit.set_sensitive(False)
        self._pop_edit.connect("activate", self._on_edit_clicked)
        self._pop_edit.show()
        self._popup_menu.append(self._pop_edit)
        
        self._popup_menu.attach_to_widget(self._tree, None)
        self._tree.connect("button-release-event", self._on_tree_clicked)
        
        # Create button boxes
        self._btn_hbox = gtk.HBox(False, 5)
        self._btn_vbox = gtk.VBox(False, 0)

        # Create buttons
        self._btn_toggle = gtk.Button(_("Toggle"))
        self._btn_toggle.set_focus_on_click(False)
        self._btn_toggle.connect("clicked", self._on_toggle_bookmark)
        self._btn_vbox.pack_start(self._btn_toggle, False, False, 5)
        
        self._btn_edit = gtk.Button(_("Edit"))
        self._btn_edit.set_sensitive(False)
        self._btn_edit.set_focus_on_click(False)
        self._btn_edit.connect("clicked", self._on_edit_clicked)
        self._btn_vbox.pack_start(self._btn_edit, False, False, 0)
        
        # Pack vbox into hbox
        self._btn_hbox.pack_start(self._btn_vbox, False, False, 5)
        self._btn_vbox.show_all()
        
        # Create layout table
        table = gtk.Table(2, 1)

        table.attach(self._pane,    0, 1, 0, 1)
        table.attach(self._btn_hbox, 1, 2, 0, 1, 0)

        table.show_all()

        # Install layout table into bottom pane
        pane = window.get_bottom_panel()
        pane.add_item(table, _('Bookmarks'), self._icon)

        # Setup handlers for all documents
        for doc in window.get_documents():
            doc.connect("loaded", self._on_doc_loaded)
            
        # Setup tab handlers
        window.connect("tab-added", self._on_tab_added)
        window.connect("tab-removed", self._on_tab_removed)
        window.connect("active-tab-changed", self._on_tab_changed)
    
    def deactivate(self):
        # Remove any installed menu items
        self._remove_menu()

        self._window = None
        self._plugin = None
        self._action_group = None

    def update_ui(self):
        self._action_group.set_sensitive(self._window.get_active_document() != None)
        
        # Swicth bookmark store for current document
        doc = self._window.get_active_document()
        if doc:
            uri = doc.get_uri()
            self._tree.set_model(self._bookmarks.get_store(uri))
            
    def _insert_menu(self):
        # Get UI manager
        manager = self._window.get_ui_manager()

        # Create menu actions
        self._action_group = gtk.ActionGroup("AdvancedBookmarksActions")
        
        self._act_ab = gtk.Action("AdvancedBookmarks", _("Bookmarks"), _("Bookmarks"), None)

        self._act_toggle = gtk.Action("ToggleBookmark", _("Toggle"), _("Toggle"), None)
        self._act_toggle.connect("activate", self._on_toggle_bookmark)
        
        self._act_toggle_adv = gtk.Action("ToggleBookmarkAdvanced", _("Toggle & edit"), _("Toggle & edit"), None)
        self._act_toggle_adv.connect("activate", self._on_toggle_bookmark, True)
        
        self._act_edit = gtk.Action("EditBookmark", _("Edit bookmark"), _("Edit bookmark"), None)
        self._act_edit.connect("activate", self._on_edit_clicked)
        self._act_edit.set_sensitive(False)
        
        self._act_nb = gtk.Action("NumberedBookmarks", _("Numbered bookmarks"), _("Numbered bookmarks"), None)
        hot_key = 0
        self._act_hot_key = {}
        while hot_key < 10:
            self._act_hot_key[hot_key] = gtk.Action("ToggleBookmark%d" % hot_key, _("Toggle bookmark #%s") % hot_key, _("Toggle bookmark #%s") % hot_key, None)
            self._action_group.add_action_with_accel(self._act_hot_key[hot_key], "<Ctrl><Alt>%d" % hot_key)
            hot_key += 1

        self._action_group.add_action(self._act_ab)
        self._action_group.add_action(self._act_nb)
        self._action_group.add_action_with_accel(self._act_toggle, "<Ctrl>b")
        self._action_group.add_action_with_accel(self._act_toggle_adv, "<Ctrl><Shift>b")
        self._action_group.add_action_with_accel(self._act_edit, "<Ctrl><Alt>b")

        # Insert action group
        manager.insert_action_group(self._action_group, -1)

        # Merge UI
        ui_path = os.path.join(os.path.dirname(__file__), "menu.ui.xml")
        self._ui_id = manager.add_ui_from_file(ui_path)

    def _remove_menu(self):
        # Get the GtkUIManager
        manager = self._window.get_ui_manager()

        # Remove the ui
        manager.remove_ui(self._ui_id)

        # Remove the action group
        manager.remove_action_group(self._action_group)

        # Make sure the manager updates
        manager.ensure_update()
        
    def _on_toggle_bookmark(self, action, add_comment=False, hot_key=None):
        # Get document uri
        doc = self._window.get_active_document()
        
        if doc:
        	uri = uri = doc.get_uri()
        else:
        	uri = None
        	
        if uri:
            # Get current position
            text_iter = doc.get_iter_at_mark(doc.get_insert())

            # Get current line number (strarting from 0)
            line = text_iter.get_line()

            exists = self._bookmarks.exists(uri, line+1)
            
            # Clean up comment dialog field (DO NOT MOVE THINS LINE INTO "IF" STATEMENT)
            self._dlg_toggle.reset("")
            
            if not exists and add_comment:
                res = self._dlg_toggle.run()
            else:
                res = gtk.RESPONSE_OK
            
            if res == gtk.RESPONSE_OK:
                comment = self._dlg_toggle.get_comment()
                
                # Get position of the current and the next lines
                start = doc.get_iter_at_line(line)
                end   = doc.get_iter_at_line(line+1)
                
                # Check if we are at the last line
                if start.get_offset() == end.get_offset():
                    end = doc.get_end_iter()
                
                # Get line text
                source = doc.get_text(start, end, False).strip()
                
                # Toggle bookmark
                added = self._bookmarks.toggle(uri, line+1, source, comment)
                
                # Save bookmarks
                self._plugin.write_config()

                # Update sensitivity of edit button and menu item
                self._btn_edit.set_sensitive(added)
                self._act_edit.set_sensitive(added)
                self._pop_edit.set_sensitive(added)

                # Highlight the bookmark and the line
                if added:
                    store = self._bookmarks.get_store(uri)
                    iters = self._bookmarks.get_iters(uri)
                    
                    path = store.get_path(iters[line+1])
                    
                    self._tree.set_model(store)
                    self._tree.set_cursor(path[0])

                highlight = self._config.getboolean("common", "highlighting")
                self.set_line_highlighting(doc, start, end, added and highlight)
                        
	        buf = self._window.get_active_view()
            buf.grab_focus()
        else:
            m = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, _("You can toggle the bookmarks in the saved documents only"))
            m.connect("response", lambda dlg, res: dlg.hide())
            m.run()
                
    def _on_dlg_toggle_response(self, dlg_toggle, res): # Handles toggle dialog response
        # Hide configuration dialog
        dlg_toggle.hide()
    	
    def _on_insert_text(self, textbuffer, iter, text, length):
        # Get document uri
        doc = self._window.get_active_document()
        uri = doc.get_uri()
        
        if uri is not None:
            # Get current line number (strarting from 0)
            line = iter.get_line()            

            # Check if the cursor is placed inside a bookmark
            iters = self._bookmarks.get_iters(uri)
            if iters.has_key(line+1) and iter.get_visible_line_offset() > 0:
                line += 1

            # Get new document line count
            count = doc.get_line_count() + text.count("\n")
			
            # Update bookmarks and number of document lines
            self._update_doc_lines(doc, count, line+1)

    def _on_delete_text(self, textbuffer, start, end):
        # Get document uri
        doc = self._window.get_active_document()
        uri = doc.get_uri()
        
        if uri is not None:
            # Get start and end line numbers (strarting from 0)
            start_line = start.get_line()
            end_line = end.get_line()

            # Check if the cursor is placed at the start of the line next a bookmark
            iters = self._bookmarks.get_iters(uri)
            if iters.has_key(end_line) and end.get_visible_line_offset() == 0:
                start_line += 1
            
            # Get new document line count
            count = doc.get_line_count() - int(abs(end_line - start_line))

            # Update document line count and bookmarks
            self._update_doc_lines(doc, count, start_line+1, end_line)

    def _update_doc_lines(self, doc, line_count, line, end = -1):
        uri = doc.get_uri()
        if uri:
            # Check if there is no number of lines stored yet
            if not self._doc_lines.has_key(uri):
                self._doc_lines[uri] = doc.get_line_count()
                
            # Check if number of lines have to be changed
            if self._doc_lines[uri] != line_count:
                # Update bookmarks
                self._bookmarks.update(uri, self._doc_lines[uri] - line_count, line, end)
                
                # Setup new line count
                self._doc_lines[uri] = line_count
	
            # Save bookmarks
            self._plugin.write_config()
            
    def _on_tab_added(self, window, tab):
        # Get tab document
        doc = tab.get_document()
        
        # Setup document load handler
        doc.connect("loaded", self._on_doc_loaded)

    def _on_tab_removed(self, window, tab):
        docs = window.get_documents()

        if len(docs) <= 0:
            self._tree.set_model()
            self._btn_edit.set_sensitive(False)
            self._act_edit.set_sensitive(False)
            self._pop_edit.set_sensitive(False)
    
    def _on_tab_changed(self, window, tab):
        # Swicth bookmark store for current document
        doc = tab.get_document()
        if doc:
            uri = doc.get_uri()
            self._tree.set_model(self._bookmarks.get_store(uri))

    def _on_doc_changed(self, doc):
        uri = doc.get_uri()
        
        if uri:
            # Update number of lines of the document
            self._doc_lines[uri] = doc.get_line_count()
            
            # Refresh highlighting if needed
            highlight = self._config.getboolean("common", "highlighting")
            if highlight:
                # Cleanup highlighting
                self.setup_highlighting(False, doc)
                
                # Put highlighting back
                self.setup_highlighting(True, doc)
            
            iters = self._bookmarks.get_iters(uri)
            
            # Get current position
            text_iter = doc.get_iter_at_mark(doc.get_insert())

            # Get current line number (strarting from 0)
            line = text_iter.get_line() + 1

            if iters.has_key(line):
                it = iters[line]

                store = self._bookmarks.get_store(uri)
                
                if self._config.get(uri, str(line)) == "":
                    # Get position of the current and the next lines
                    start = doc.get_iter_at_line(line-1)
                    end   = doc.get_iter_at_line(line)
                    
                    # Check if we are at the last line
                    if start.get_offset() == end.get_offset():
                        end = doc.get_end_iter()
                    
                    # Get line text
                    source = doc.get_text(start, end, False).strip()
                    
                    store.set_value(it, 1, source.strip())

    def _on_doc_loaded(self, doc, arg, put=True, connect_signals=True):
        # Update comments
        uri = doc.get_uri()
        
        if uri:
            highlight = self._config.getboolean("common", "highlighting")
            
            store = self._bookmarks.get_store(uri)
            iters = self._bookmarks.get_iters(uri)
            
            for i in iters:
                it = iters[i]

                line = int(store.get_value(it, 0)) - 1
                
                start = doc.get_iter_at_line(line)
                end   = doc.get_iter_at_line(line+1)
                
                # Check if we are at the last line
                if start.get_offset() == end.get_offset():
                    end = doc.get_end_iter()
                
                self.set_line_highlighting(doc, start, end, put and highlight)
                    
                if store.get_value(it, 1) == "":
                    source = doc.get_text(start, end, False)
                    store.set_value(it, 1, source.strip())
            
        if connect_signals:
            # Setup update handlers
            doc.connect("insert-text",  self._on_insert_text)
            doc.connect("delete-range", self._on_delete_text)
            doc.connect("changed",      self._on_doc_changed)
            doc.connect("cursor-moved", self._on_cursor_moved)
        
    def _on_edit_clicked(self, btn):
        model = self._tree.get_model()

        cursor = self._tree.get_cursor()
        
        if cursor and cursor[0]:
            row = cursor[0][0]

            self._on_row_activated(self._tree, row, 0)

    def _on_tree_clicked(self, tree, event):
    	if event.button == 3:
	    	self._popup_menu.popup(None, None, None, event.button, event.time)
    	
    	return False

    def _on_row_selected(self, tree):
        model = tree.get_model()
        cursor = tree.get_cursor()
        
        if cursor:
            row = cursor[0][0]
            
            # Set comment button sensitivity
            self._btn_edit.set_sensitive(True)
            self._act_edit.set_sensitive(True)
            self._pop_edit.set_sensitive(True)
            
            # Get bookmark line
            bookmark = model.get_iter(row)
            line = model.get_value(bookmark, 0)
            
            # Get active document
            doc = self._window.get_active_document()
            buf = self._window.get_active_view()
            
            # Get current position
            text_iter = doc.get_iter_at_mark(doc.get_insert())

            if line != text_iter.get_line()+1:
                # Jump to bookmark
                doc.goto_line(int(line)-1)
                buf.scroll_to_cursor()
                buf.grab_focus()

    def _on_row_activated(self, tree, row, column):
        # Get document uri
        doc = self._window.get_active_document()
        uri = doc.get_uri()

        # Get bookmark line
        model = tree.get_model()
        bookmark = model.get_iter(row)
        line = model.get_value(bookmark, 0)
        
        comment = self._config.get(uri, str(line))
        
        self._dlg_toggle.reset(comment)
        res = self._dlg_toggle.run()

        if res == gtk.RESPONSE_OK:
            comment = self._dlg_toggle.get_comment()
            
            # Delete existing bookmark 
            self._bookmarks.delete(uri, line)

            # Get position of the current and the next lines
            start = doc.get_iter_at_line(line-1)
            end   = doc.get_iter_at_line(line)
            
            # Check if we are at the last line
            if start.get_offset() == end.get_offset():
                end = doc.get_end_iter()
            
            # Get line text
            source = doc.get_text(start, end, False).strip()
            
            # Add bookmark
            self._bookmarks.add(uri, line, source, comment)
            self._tree.set_model(self._bookmarks.get_store(uri))
            
            # Save bookmarks
            self._plugin.write_config()
        
    def _on_tree_focused(self, tree, direction):
        view = self._window.get_active_view()
        view.grab_focus()
        
    def _render_comment_callback(self, column, cell_renderer, tree_model, iter):
        doc = self._window.get_active_document()
        uri = doc.get_uri()
        
        if uri:
            line = tree_model.get_value(iter, 0)
            text = tree_model.get_value(iter, 1)
            
            if self._bookmarks.exists(uri, line):
                comment = self._config.get(uri, str(line))
                
                if comment != "":
                    cell_renderer.set_property("style", pango.STYLE_ITALIC)
                    cell_renderer.set_property("text", "'"+text+"'")
                else:
                    cell_renderer.set_property("style", pango.STYLE_NORMAL)
    
    def _on_cursor_moved(self, doc):
        uri = doc.get_uri()

        store = self._bookmarks.get_store(uri)
        
        # Get current position
        text_iter = doc.get_iter_at_mark(doc.get_insert())

        # Get current line number (strarting from 0)
        line = text_iter.get_line() + 1

        exists = self._bookmarks.exists(uri, line)
        
        if exists:
            iters = self._bookmarks.get_iters(uri)
            
            path = store.get_path(iters[line])
            
            self._tree.set_cursor(path[0])
        else:
            sel = self._tree.get_selection()
            sel.unselect_all()
            
            self._btn_edit.set_sensitive(False)
            self._act_edit.set_sensitive(False)
            self._pop_edit.set_sensitive(False)
    
    def set_line_highlighting(self, doc, start, end, highlight):
        tag_table = doc.get_tag_table()
        tag = tag_table.lookup("bookmark")
        
        if tag is None:
            color = self._config.get("common", "highlight_color")
            tag = doc.create_tag("bookmark", paragraph_background_gdk = gtk.gdk.color_parse(color))
        
        if highlight:
            doc.apply_tag(tag, start, end)
        else:
            doc.remove_tag(tag, start, end)
    
    def _remove_highlighting(self, doc):
        tag_table = doc.get_tag_table()
        tag = tag_table.lookup("bookmark")
        
        if tag is not None:
            start = doc.get_start_iter()
            end = doc.get_end_iter()
            doc.remove_tag(tag, start, end)
    
    def setup_highlighting(self, highlight, doc=None):
        func = highlight and (lambda doc: self._on_doc_loaded(doc, None, True, False)) or (lambda doc: self._remove_highlighting(doc))
        
        if doc is None:
            docs = self._window.get_documents()
        else:
            docs = [doc]
            
        for d in docs:
            tag_table = d.get_tag_table()
            tag = tag_table.lookup("bookmark")
            
            if tag is not None:
                tag_table.remove(tag)
                color = self._config.get("common", "highlight_color")
                tag = d.create_tag("bookmark", paragraph_background_gdk = gtk.gdk.color_parse(color))

            func(d)
    
# ex:ts=4:et:

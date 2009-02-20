# Gedit Go to File plugin - Easily open and switch between files
# Copyright (C) 2008  Eric Butler <eric@extremeboredom.net>
#
# Based on "Snap Open" (C) 2006 Mads Buus Jensen <online@buus.net>
# Inspired by TextMate
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

import pygtk
import gtk, gobject, pango
import sexy
import relevance
import os

class GotoFileWindow(gtk.Window):
	def __init__(self, plugin):
		gtk.Window.__init__(self)

		self._plugin = plugin

		self.set_title('Go to File')
		self.set_default_size(300, 250)
		self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
		self.set_position(gtk.WIN_POS_CENTER) # _ON_PARENT
		self.connect('show', self._windowShow)
		self.connect('delete-event', self._windowDeleteEvent)

		theme = gtk.icon_theme_get_default()
		searchPixbuf = theme.load_icon('search', 16, gtk.ICON_LOOKUP_USE_BUILTIN)

		self._entry = sexy.IconEntry()
		self._entry.add_clear_button()
		self._entry.set_icon(sexy.ICON_ENTRY_PRIMARY, gtk.image_new_from_pixbuf(searchPixbuf))
		self._entry.connect('changed', self._entryChanged)
		self._entry.connect('key-press-event', self._entryKeyPress)
		self._entry.connect('activate', self._entryActivated)

		cell = gtk.CellRendererText()
		cell.set_property('ellipsize', pango.ELLIPSIZE_START)

		self._tree = gtk.TreeView()
		self._tree.set_headers_visible(False)
		self._tree.append_column(gtk.TreeViewColumn("Name", cell, markup=0))
		self._tree.connect('button-press-event', self._treeButtonPress)
		self._tree.get_selection().connect('changed', self._treeSelectionChanged)

		# Model columns: formattedName, formattedPath, path, score
		self._store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_FLOAT)

		self._sortModel = gtk.TreeModelSort(self._store)
		self._sortModel.set_sort_column_id(3, gtk.SORT_DESCENDING)
		self._tree.set_model(self._sortModel)

		vbox = gtk.VBox()

		alignment = gtk.Alignment(0, 0, 1, 1)
		alignment.set_padding(6, 6, 6, 6)
		alignment.add(self._entry)
		vbox.pack_start(alignment, False, False, 0)

		vbox.pack_start(gtk.HSeparator(), False, False, 0)

		swindow = gtk.ScrolledWindow()
		swindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		swindow.add(self._tree)
		vbox.pack_start(swindow, True, True, 0)

		vbox.pack_start(gtk.HSeparator(), False, False, 0)

		label = gtk.Label()
		#label.set_ellipsize(pango.ELLIPSIZE_START)
		self._expander = gtk.Expander(None)
		self._expander.set_label_widget(label)
		
		table = gtk.Table(2,3, False)
		table.set_property('row-spacing', 6)
		table.set_property('column-spacing', 6)
		table.set_border_width(6)
		table.attach(gtk.Label("Include:"), 0, 1, 0, 1, gtk.SHRINK, gtk.SHRINK, 0, 0)
		self._includeFilterEntry = gtk.Entry()
		self._includeFilterEntry.set_text(self._plugin.getIncludeFilter())
		self._includeFilterEntry.connect('changed', self._filtersChanged)
		table.attach(self._includeFilterEntry, 1, 2, 0, 1, gtk.FILL|gtk.EXPAND, gtk.SHRINK, 0, 0)

		table.attach(gtk.Label("Exclude:"), 0, 1, 1, 2, gtk.SHRINK, gtk.SHRINK, 0, 0)
		self._excludeFilterEntry = gtk.Entry()
		self._excludeFilterEntry.set_text(self._plugin.getExcludeFilter())
		self._excludeFilterEntry.connect('changed', self._filtersChanged)
		table.attach(self._excludeFilterEntry, 1, 2, 1, 2, gtk.FILL|gtk.EXPAND, gtk.SHRINK, 0, 0)

		self._showHiddenCheck = gtk.CheckButton("Show hidden files/folders")
		self._showHiddenCheck.connect('toggled', self._filtersChanged)
		table.attach(self._showHiddenCheck, 0, 2, 2, 3, gtk.FILL|gtk.EXPAND, gtk.SHRINK, 0, 0)

		self._expander.add(table)

		vbox.pack_start(self._expander, False, False, 0)

		self.add(vbox)
		
		try:
			import texas
			self._walker = texas.WalkerTexasRanger(self._onWalkResult, self._onWalkClear, self._onWalkFinish)
		except:
			print "async walker not available"
			import moonwalk
			self._walker = moonwalk.MoonWalker(self._onWalkResult, self._onWalkClear, self._onWalkFinish)

	def _windowShow(self, win):
		self._rootDirectory = self._plugin.getRootDirectory()
		self._entry.set_text('')
		self._entry.grab_focus()
		self._expander.set_expanded(False)
		self._search('')

	def _windowDeleteEvent(self, win, event):
		self._walker.cancel()
		self.hide()
		return True
	
	def _entryActivated(self, entry):
		self._openSelectedFile()

	def _entryChanged(self, entry):
		 self._search(entry.get_text())

	def _entryKeyPress(self, entry, event):
                if event.keyval == gtk.keysyms.Escape:
			self.hide()
                else:
			model, iter = self._tree.get_selection().get_selected()
			if iter:
				path = model.get_path(iter)
				if event.keyval == gtk.keysyms.Up:
					path = (path[0] - 1,)
					if path[0] >= 0:
						iter = model.get_iter(path)
						self._tree.get_selection().select_iter(iter)
					return True
				elif event.keyval == gtk.keysyms.Down:
					path = (path[0] + 1,)
					if path[0] < model.iter_n_children(None):
						iter = model.get_iter(path)
						self._tree.get_selection().select_iter(iter)
					return True
		return False
	
	def _filtersChanged(self, sender):
		self._plugin.setShowHidden(self._showHiddenCheck.get_active())
		self._plugin.setIncludeFilter(self._includeFilterEntry.get_text())
		self._plugin.setExcludeFilter(self._excludeFilterEntry.get_text())
		self._search(self._entry.get_text())
			
	def _treeButtonPress(self, tree, event):
		self._openSelectedFile()

	def _treeSelectionChanged(self, selection):
		model, iter = selection.get_selected()
		if iter:
			self._expander.get_label_widget().set_markup(model.get_value(iter, 1))
	
	def _onWalkResult(self, walker, dirname, dirs, files, text):
		if text == None: text = ''
		for file, score in self._plugin.filterFiles(text, files):
			name = relevance.formatCommonSubstrings(file, text)
			self._store.append((name, os.path.join(dirname, name), os.path.join(dirname, file), score))
			total = self._store.iter_n_children(None)
			if total == self._plugin.getMaxResults():
				print "Max results reached",self._plugin.getMaxResults()
				walker.cancel()
				break
	
	def _onWalkClear(self, walker, text):
		self._store.clear()
	
	def _onWalkFinish(self, walker, text):
		iter = self._sortModel.get_iter_first()
		if iter:
			self._tree.get_selection().select_iter(iter)
			path = self._sortModel.get_path(iter)
			self._tree.scroll_to_cell(path, None, True, 0, 0)
	
	def _search(self, text):
		text = text.replace(' ', '')
		ignoreDot = not self._plugin.getShowHidden()
		maxDepth  = self._plugin.getMaxDepth()
		self._walker.walk(self._rootDirectory, ignoredot = ignoreDot, maxdepth = maxDepth, user_data=text)
	
	def _openSelectedFile(self):
		model, iter = self._tree.get_selection().get_selected()
		if iter:
			path = model.get_value(iter, 2)
			self._plugin.openFile(path)
			self.hide()

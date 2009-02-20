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

import gedit
import pygtk
import gtk, gconf
import os
import relevance
from urlparse import urlparse, urljoin
from fnmatch import fnmatch
from gotofile_window import GotoFileWindow

UI_STRING = """<ui>
<menubar name="MenuBar">
	<menu name="FileMenu" action="File">
		<placeholder name="FileOps_2">
			<menuitem name="GotoFile" action="GotoFileAction"/>
		</placeholder>
	</menu>
</menubar>
</ui>
"""

class GotoFilePluigin(gedit.Plugin):
	def __init__(self):
		self._gconf = gconf.client_get_default()
		gedit.Plugin.__init__(self)
		self._window = GotoFileWindow(self)
	
	def activate(self, window):
		self._geditWindow = window

		ui = window.get_ui_manager()
		self._actionGroup = gtk.ActionGroup('GotoFileActions')
		action = gtk.Action(name='GotoFileAction', label='Go to File...', tooltip='', stock_id=None)
		action.connect('activate', self._menuActivated)

		self._actionGroup.add_action_with_accel(action, '<Ctrl><Alt>o')
		ui.insert_action_group(self._actionGroup, 1)
		self._mergeId =  ui.add_ui_from_string(UI_STRING)

		self._window.set_transient_for(window)
	
	def deactivate(self, window):
		ui = window.get_ui_manager()
		ui.remove_ui(self._mergeId)
		ui.remove_action_group(self._actionGroup)
		self._geditWindow = None
	
	def getMaxDepth(self):
		return self._readSetting('max_depth', gconf.VALUE_INT, 10)
	
	def setMaxDepth(self, depth):
		self._writeSetting('max_depth', gconf.VALUE_INT, depth)

	def getMaxResults(self):
		return self._readSetting('max_results', gconf.VALUE_INT, 100)

	def setMaxResults(self, results):
		self._writeSetting('max_results', gconf.VALUE_INT, results)

	def getIncludeFilter(self):
		return self._readSetting('include_filter', gconf.VALUE_STRING, '')
		
	def setIncludeFilter(self, text):
		self._writeSetting('include_filter', gconf.VALUE_STRING, text)
	
	def getExcludeFilter(self):
		return self._readSetting('exclude_filter', gconf.VALUE_STRING, '*.swp .* *~')
	
	def setExcludeFilter(self, text):
		self._writeSetting('exclude_filter', gconf.VALUE_STRING, text)

	def getShowHidden(self):
		return self._readSetting('show_hidden', gconf.VALUE_BOOL, False)
	
	def setShowHidden(self, value):
		self._writeSetting('show_hidden', gconf.VALUE_BOOL, value)

	def getRootDirectory(self):
		fbRoot = self._getFilebrowserRoot()
		if fbRoot and os.path.isdir(fbRoot):
			return fbRoot
		else:
			doc = self._geditWindow.get_active_document()
			if doc:
				uri = doc.get_uri()
				if uri:
					url = urlparse(uri)
					if url.scheme == 'file' and os.path.isfile(url.path):
						return os.path.dirname(url.path)
			return os.getcwd()

	def openFile(self, path):
		uri = urljoin('file://', path)
		tab = self._geditWindow.get_tab_from_uri(uri)
		if tab == None:
			tab = self._geditWindow.create_tab_from_uri(uri, gedit.encoding_get_current(), 0, False, False)
		self._geditWindow.set_active_tab(tab)

	def filterFiles(self, text, files):
		for file in files:
			score = relevance.score(file, text)
			if score > 0:
				add = True
				for pattern in self.getExcludeFilter().split(' '):
					if fnmatch(file, pattern):
						add = False
						break
				includeFilter = self.getIncludeFilter()
				if includeFilter:
					for pattern in includeFilter.split(' '):
						if fnmatch(file, pattern):
							add = True
							break
						else:
							add = False
				if add:
					yield file, score

	def _menuActivated(self, menu):
		self._window.show_all()
		self._window.present()

	def _getFilebrowserRoot(self):
		base = '/apps/gedit-2'
		activePlugins = map(lambda v: v.get_string(), self._gconf.get(base + '/plugins/active-plugins').get_list())
		sidepaneVisible = self._gconf.get(base + '/preferences/ui/side_pane/side_pane_visible').get_bool()
		if 'filebrowser' in activePlugins and sidepaneVisible:
			val = self._gconf.get(base + '/plugins/filebrowser/on_load/virtual_root')
			if val is not None:
				url = urlparse(val.get_string())
				return url.path
	
	def _writeSetting(self, name, gconfType, value):
		base = '/apps/gedit-2/plugins/gotofile/'
		if gconfType == gconf.VALUE_STRING:
			self._gconf.set_string(base + name, value)
		elif gconfType == gconf.VALUE_INT:
			self._gconf.set_int(base + name, value)			
		elif gconfType == gconf.VALUE_BOOL:
			self._gconf.set_bool(base + name, value)
		else:
			raise "Not supported"

	def _readSetting(self, name, gconfType, default):
		base = '/apps/gedit-2/plugins/gotofile/'
		val = self._gconf.get(base + name)
		if val:
			if gconfType == gconf.VALUE_INT:
				return val.get_int()
			elif gconfType == gconf.VALUE_STRING:
				return val.get_string()
			elif gconfType == gconf.VALUE_BOOL:
				return val.get_bool()
		return default

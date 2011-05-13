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
import getopt
import ConfigParser
import gettext

APP_NAME = "plugin"
LOC_PATH = os.path.join(os.path.expanduser("~/.gnome2/gedit/plugins/reopen-tabs/lang"))

gettext.find(APP_NAME, LOC_PATH)
gettext.install(APP_NAME, LOC_PATH, True)

RELOADER_STATE_READY        = "ready"
RELOADER_STATE_INIT         = "init"
RELOADER_STATE_RELOADING    = "reloading"
RELOADER_STATE_DONE         = "done"
RELOADER_STATE_CLOSING      = "closing"

def log(msg):
	print '\033[32m' + msg + '\033[0m'


class ReopenTabsPlugin(gedit.Plugin):


	def __init__(self):
		gedit.Plugin.__init__(self)
		
		self._config = None
		
		self._state = RELOADER_STATE_INIT


	def activate(self, window):
		log('Event: app activated')
		self.read_config()

		window.connect("active-tab-changed", self._on_active_tab_changed)
		window.connect("active-tab-state-changed", self._on_active_tab_state_changed)
		window.connect("tabs-reordered", self._on_tabs_reordered)
		window.connect("tab-removed", self._on_tab_removed)

		# Register signal handler to ask a user to save tabs on exit
		window.connect("delete_event", self._on_destroy)
		

	def deactivate(self, window):
		log('Event: app deactivate')
		pass


	def read_config(self): # Reads configuration from a file
		# Get configuration dictionary
		self._conf_path = os.path.join(os.path.expanduser("~/.gnome2/gedit/plugins/"), "reopen-tabs/plugin.conf")

		# Check if configuration file does not exists
		if not os.path.exists(self._conf_path):
			# Create configuration file
			conf_file = file(self._conf_path, "wt")
			conf_file.close()

		self._conf_file = file(self._conf_path, "r+")
		self._config = ConfigParser.ConfigParser()
		self._config.readfp(self._conf_file)
		self._conf_file.close()

		# Setup default configuration if needed
		if not self._config.has_section("common"):
			self._config.add_section("common")

		if not self._config.has_option("common", "active_document"):
			self._config.set("common", "active_document", "")

		if not self._config.has_section("documents"):
			self._config.add_section("documents")

	def write_config(self): # Saves configuration to a file
		self._conf_file = file(self._conf_path, "r+")
		self._conf_file.truncate(0)
		self._config.write(self._conf_file)
		self._conf_file.close()
	
	def _on_tabs_reordered(self, window):
		log('Event: tabs reordered')
		if self._state == RELOADER_STATE_DONE:
			self._save_tabs()


	def _on_tab_removed(self, window, data):
		log('Event: tab removed (%s, %s)' % (self._state, window.get_state()))
		if self._state == RELOADER_STATE_DONE:
			self._save_tabs()


	def _on_active_tab_changed(self, window, tab):
		log('Event: active tab changed')
		if self._state == RELOADER_STATE_INIT:
			self._state = RELOADER_STATE_READY
			self._on_active_tab_state_changed(window)


	def _on_active_tab_state_changed(self, window):
		log('Event: active state tab changed: ' + str(window.get_active_tab().get_state()))
		log('Event: active state tab changed: ' + str(window.get_state()))
		# Check if we are not reloading and did not finished yet
		if self._state in (RELOADER_STATE_READY, RELOADER_STATE_DONE):
			# Get active tab
			tab = window.get_active_tab()
			# Check if we are ready to reload
			if tab and tab.get_state() == gedit.TAB_STATE_NORMAL:
				if self._state == RELOADER_STATE_READY:
					self._state = RELOADER_STATE_RELOADING
					self._reopen_tabs(window)
					self._state = RELOADER_STATE_DONE
				else:
					self._save_tabs()


	def update_ui(self, window):
		pass


	def _on_destroy(self, widget, event): # Handles window destory (saves tabs if required)
		log('Event: app destroy')
		self._state = RELOADER_STATE_CLOSING
	
	import time

	def _save_tabs(self): # Save opened tabs in configuration file
		log('ACTION save tabs')
		start = time.time()
		# Clear old document list
		self._config.remove_section("documents")

		# Get document URI list
		app = gedit.app_get_default()
		win = app.get_active_window()
		
		# Return list of documents which having URI's
		docs = [d.get_uri() for d in win.get_documents() if d.get_uri()]
		
		# Check if there is anything to save
		if len(docs) > 0:
			self._config.add_section("documents")
			self._config.remove_option("common", "active_document")
	
			cur_doc = win.get_active_document()
			if cur_doc: cur_uri = cur_doc.get_uri()
			else: cur_uri = None
			cur_doc = None
		
			# Create new document list
			n = 1
			for uri in docs:
				# Setup option name
				name = "document" + str(n).rjust(3).replace(" ", "0")
		
				# Check if current document is active
				if uri == cur_uri:
					cur_doc = name

				self._config.set("documents", name, uri)
				n = n + 1

			# Remeber active document
			if cur_doc:
				self._config.set("common", "active_document", cur_doc)

		self.write_config()
		end = time.time()
		
		if self._config.has_section("documents"):
			log(str(self._config.options("documents")))
		else:
			log('[]')
		log('>>> %0.3fms' % (1000 * (end - start)))
		
	def _reopen_tabs(self, window):
		log('ACTION load tabs')
		# Get list of open documents
		open_docs = [d.get_uri() for d in window.get_documents() if d.get_uri()]
		
		# Get saved active document
		active = self._config.get("common", "active_document")
	
		# Get document list
		docs = self._config.options("documents")
		log(str(docs))

		empty_tab = None
		active_tab = None

		# Check if active document is untitled (there is empty tab)
		if window.get_active_document().is_untitled():
			# Remember empty tab to close it later
			empty_tab = window.get_active_tab()

		# Check if document list is not empty
		if len(docs) > 0:
			
			# Process the rest documents
			for d in docs:
				# Get document uri
				uri = self._config.get("documents", d)
				
				# Check if document is not already opened
				if open_docs.count(uri) > 0: continue

				# Check if document exists
				if not os.path.exists(uri.replace('file://', '', 1)): continue

				# Create new tab
				tab = window.create_tab_from_uri(uri, None, 0, True, False)
		
				# Check if document was active (and there is NOT file in command line)
				if d == active and empty_tab != None:
					active_tab = tab

		# Connect handler that switches saved active document tab
		log('empty tab: ' + str(empty_tab))
		log('activ tab: ' + str(active_tab))
		if active_tab:
			def on_doc_loaded(doc, arg):
				window.set_active_tab(active_tab)
				if empty_tab:
					_state = self._state
					self._state = RELOADER_STATE_CLOSING
					window.close_tab(empty_tab)
					self._state = _state

			active_tab.get_document().connect("loaded", on_doc_loaded)
		if empty_tab == None:
			self._save_tabs()


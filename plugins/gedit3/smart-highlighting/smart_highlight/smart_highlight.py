# -*- encoding:utf-8 -*-


# smart_highlight.py is part of smart-highlighting-gedit.
#
#
# Copyright 2010-2012 swatch
#
# smart-highlighting-gedit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#




from gi.repository import Gtk, Gdk, Gedit
import re
import os.path
#import pango
import shutil

from . import config_manager
from .config_ui import ConfigUI

import gettext
APP_NAME = 'smart_highlight'		#Same as module name defined at .plugin file.
CONFIG_DIR = os.path.expanduser('~/.local/share/gedit/plugins/' + APP_NAME + '/config')
#LOCALE_DIR = '/usr/share/locale'
LOCALE_DIR = os.path.join(os.path.dirname(__file__), 'locale')
print(LOCALE_DIR)
if not os.path.exists(LOCALE_DIR):
	LOCALE_DIR = '/usr/share/locale'
	print('locale')
try:
	t = gettext.translation(APP_NAME, LOCALE_DIR)
	_ = t.gettext
	print('gettext')
except:
	print('none')
	pass
#gettext.install(APP_NAME, LOCALE_DIR, unicode=True)


ui_str = """<ui>
	<menubar name="MenuBar">
		<menu name="ToolsMenu" action="Tools">
			<placeholder name="ToolsOps_0">
				<separator/>
				<menu name="SmartHighlightMenu" action="SmartHighlightMenu">
					<placeholder name="SmartHighlightMenuHolder">
						<menuitem name="smart_highlight_configure" action="smart_highlight_configure"/>
					</placeholder>
				</menu>
				<separator/>
			</placeholder>
		</menu>
	</menubar>
</ui>
"""



class SmartHighlightWindowHelper:
	def __init__(self, plugin, window):
		self._window = window
		self._plugin = plugin
		self.current_selection = ''
		self.start_iter = None
		self.end_iter = None
		self.vadj_value = 0
		views = self._window.get_views()
		for view in views:
			view.get_buffer().connect('mark-set', self.on_textbuffer_markset_event)
			view.get_vadjustment().connect('value-changed', self.on_view_vadjustment_value_changed)
			#view.connect('button-press-event', self.on_view_button_press_event)
		self.active_tab_added_id = self._window.connect("tab-added", self.tab_added_action)

		user_configfile = os.path.join(CONFIG_DIR, 'config.xml')
		if not os.path.exists(user_configfile):
			if not os.path.exists(os.path.dirname(user_configfile)):
				os.makedirs(os.path.dirname(user_configfile))
			shutil.copy2(os.path.dirname(__file__) + "/config/config.xml", os.path.dirname(user_configfile))
		configfile = user_configfile
		'''		
		user_configfile = os.path.join(os.path.expanduser('~/.local/share/gedit/plugins/' + 'smart_highlight'), 'config.xml')
		if os.path.exists(user_configfile):
			configfile = user_configfile
		else:	
			configfile = os.path.join(os.path.dirname(__file__), "config.xml")
		#'''
		self.config_manager = config_manager.ConfigManager(configfile)
		self.options = self.config_manager.load_configure('search_option')
		self.config_manager.to_bool(self.options)
		self.smart_highlight = self.config_manager.load_configure('smart_highlight')
		
		self._insert_menu()

	def deactivate(self):
		# Remove any installed menu items
		self._window.disconnect(self.active_tab_added_id)
		self.config_manager.update_config_file(self.config_manager.config_file, 'search_option', self.options)
		self.config_manager.update_config_file(self.config_manager.config_file, 'smart_highlight', self.smart_highlight)
		
	def _insert_menu(self):
		# Get the GtkUIManager
		manager = self._window.get_ui_manager()

		# Create a new action group
		self._action_group = Gtk.ActionGroup("SmartHighlightActions")
		self._action_group.add_actions( [("SmartHighlightMenu", None, _('Smart Highlighting'))] + \
										[("smart_highlight_configure", None, _("Configuration"), None, _("Smart Highlighting Configure"), self.smart_highlight_configure)]) 

		# Insert the action group
		manager.insert_action_group(self._action_group, -1)

		# Merge the UI
		self._ui_id = manager.add_ui_from_string(ui_str)
	
	def _remove_menu(self):
		# Get the GtkUIManager
		manager = self._window.get_ui_manager()

		# Remove the ui
		manager.remove_ui(self._ui_id)

		# Remove the action group
		manager.remove_action_group(self._action_group)

		# Make sure the manager updates
		manager.ensure_update()

	def update_ui(self):
		self._action_group.set_sensitive(self._window.get_active_document() != None)

	'''		
	def show_message_dialog(self, text):
		dlg = Gtk.MessageDialog(self._window, 
								Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
								Gtk.MessageType.INFO,
								Gtk.ButtonsType.CLOSE,
								_(text))
		dlg.run()
		dlg.hide()
	#'''
		
		
	def create_regex(self, pattern, options):
		if options['REGEX_SEARCH'] == False:
			pattern = re.escape(str(r'%s' % pattern))
		else:
			pattern = str(r'%s' % pattern)
		
		if options['MATCH_WHOLE_WORD'] == True:
			pattern = r'\b%s\b' % pattern
			
		if options['MATCH_CASE'] == True:
			regex = re.compile(pattern, re.MULTILINE)
		else:
			regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
		
		return regex

	def smart_highlighting_action(self, doc, search_pattern, iter, clear_flg = True):
		regex = self.create_regex(search_pattern, self.options)
		if clear_flg == True:
			self.smart_highlight_off(doc)
		
		self.vadj_value = self._window.get_active_view().get_vadjustment().get_value()
		current_line = iter.get_line()
		start_line = current_line - 50
		end_line = current_line + 50
		if start_line <= 0:
			self.start_iter = doc.get_start_iter()
		else:
			self.start_iter = doc.get_iter_at_line(start_line)
		if end_line < doc.get_line_count():
			self.end_iter = doc.get_iter_at_line(end_line)
		else:
			self.end_iter = doc.get_end_iter()
			
		text = str(doc.get_text(self.start_iter, self.end_iter, True))
		
		match = regex.search(text)
		while(match):
			self.smart_highlight_on(doc, match.start()+self.start_iter.get_offset(), match.end() - match.start())
			match = regex.search(text, match.end()+1)
			
	def tab_added_action(self, action, tab):
		view = tab.get_view()
		view.get_buffer().connect('mark-set', self.on_textbuffer_markset_event)
		view.get_vadjustment().connect('value-changed', self.on_view_vadjustment_value_changed)
		#view.connect('button-press-event', self.on_view_button_press_event)
	
	def on_textbuffer_markset_event(self, textbuffer, iter, textmark):
		#print textmark.get_name()
		if textmark.get_name() != 'selection_bound' and textmark.get_name() != 'insert':
			return
		if textbuffer.get_selection_bounds():
			start, end = textbuffer.get_selection_bounds()
			self.current_selection = textbuffer.get_text(start, end, True)
			self.smart_highlighting_action(textbuffer, self.current_selection, iter)
		else:
 			self.current_selection = ''
 			self.smart_highlight_off(textbuffer)
	
	def smart_highlight_on(self, doc, highlight_start, highlight_len):
		if doc.get_tag_table().lookup('smart_highlight') == None:
			tag = doc.create_tag("smart_highlight", foreground=self.smart_highlight['FOREGROUND_COLOR'], background=self.smart_highlight['BACKGROUND_COLOR'])
		doc.apply_tag_by_name('smart_highlight', doc.get_iter_at_offset(highlight_start), doc.get_iter_at_offset(highlight_start + highlight_len))
		
	def smart_highlight_off(self, doc):
		start, end = doc.get_bounds()
		if doc.get_tag_table().lookup('smart_highlight') == None:
			tag = doc.create_tag("smart_highlight", foreground=self.smart_highlight['FOREGROUND_COLOR'], background=self.smart_highlight['BACKGROUND_COLOR'])
		doc.remove_tag_by_name('smart_highlight', start, end)
		
	def smart_highlight_configure(self, action, data = None):
		config_ui = ConfigUI(self._plugin)
		
	def on_view_vadjustment_value_changed(self, object, data = None):
		if self.current_selection == '':
			return
		if object.get_value() < self.vadj_value:	#scroll up
			self.smart_highlighting_action(self._window.get_active_document(), self.current_selection, self.start_iter, False)
		else:	#scroll down
			self.smart_highlighting_action(self._window.get_active_document(), self.current_selection, self.end_iter, False)

			

	'''		
	def auto_select_word_bounds(self, pattern=r'[_a-zA-Z][_a-zA-Z0-9]*'):
		doc = self._window.get_active_document()
		if doc.get_has_selection():
			start, end = doc.get_selection_bounds()
			return start, end
		else:
			current_iter = doc.get_iter_at_mark(doc.get_insert())
			line_num = current_iter.get_line()
			line_start = doc.get_iter_at_line(line_num)
			line_text = doc.get_text(line_start, doc.get_iter_at_line(line_num + 1), True)
			line_start_pos = line_start.get_offset()
			matches = re.finditer(pattern, line_text)
			for match in matches:
				if current_iter.get_offset() in range(line_start_pos + match.start(), line_start_pos + match.end() + 1):
					return doc.get_iter_at_offset(line_start_pos + match.start()), doc.get_iter_at_offset(line_start_pos+match.end())
			return None
	
	def on_view_button_press_event(self, object, event):
		#if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
		if event.button == 1 and event.type == 5:	#EventType 2BUTTON_PRESS
			print '2button press'
			start, end = self.auto_select_word_bounds()
			print self._window.get_active_document().get_text(start, end, True)
			self._window.get_active_document().select_range(start, end)
 	#'''
 	


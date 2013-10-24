# -*- encoding:utf-8 -*-


# advancedfind.py is part of advancedfind-gedit.
#
#
# Copyright 2010-2012 swatch
#
# advancedfind-gedit is free software; you can redistribute it and/or modify
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



from gi.repository import Gtk, Gedit, Gio
import os.path
import os
import fnmatch
import subprocess
import urllib.request, urllib.parse, urllib.error
import re
#import time
import shutil


from .advancedfind_ui import AdvancedFindUI
from .find_result import FindResultView
from . import config_manager
from .config_ui import ConfigUI


import gettext
APP_NAME = 'advancedfind'
CONFIG_DIR = os.path.expanduser('~/.local/share/gedit/plugins/' + APP_NAME + '/config')
#LOCALE_DIR = '/usr/share/locale'
LOCALE_DIR = os.path.join(os.path.dirname(__file__), 'locale')
if not os.path.exists(LOCALE_DIR):
	LOCALE_DIR = '/usr/share/locale'
try:
	t = gettext.translation(APP_NAME, LOCALE_DIR)
	_ = t.gettext
	#Gtk.glade.bindtextdomain(APP_NAME, LOCALE_DIR)
except:
	pass
#gettext.install(APP_NAME, LOCALE_DIR, unicode=True)


# Menu item example, insert a new item in the Edit menu
ui_str = """<ui>
	<menubar name="MenuBar">
		<menu name="SearchMenu" action="Search">
			<placeholder name="SearchOps_0">
				<menuitem name="advanced_find_active" action="advanced_find_active"/>
				<menuitem name="find_next" action="find_next"/>
				<menuitem name="find_previous" action="find_previous"/>
				<menuitem name="select_find_next" action="select_find_next"/>
				<menuitem name="select_find_previous" action="select_find_previous"/>
				<menuitem name="advanced_find_configure" action="advanced_find_configure"/>
			</placeholder>
		</menu>
	</menubar>
</ui>
"""


class AdvancedFindWindowHelper:
	def __init__(self, plugin, window):
		self._window = window
		self._plugin = plugin
		self.find_ui = None
		self.find_history = []
		self.replace_history = []
		self.filter_history = []
		self.path_history = []
		self.find_bookmarks = []
		self.replace_bookmarks = []
		self.filter_bookmarks = []
		self.path_bookmarks = []
		self.current_search_pattern = ""
		self.current_replace_text = ""
		self.current_file_pattern = "*"
		#self.current_path = ""
		self.forwardFlg = True
		self.scopeFlg = 0
		
		'''
		self.result_highlight_tag = Gtk.TextTag('result_highlight')
		self.result_highlight_tag.set_properties(foreground='yellow',background='red')
		self.result_highlight_tag.set_property('family', 'Serif')
		self.result_highlight_tag.set_property('size-points', 12)
		self.result_highlight_tag.set_property('weight', pango.WEIGHT_BOLD)
		self.result_highlight_tag.set_property('underline', pango.UNDERLINE_DOUBLE)
		self.result_highlight_tag.set_property('style', pango.STYLE_ITALIC)
		#'''
		
		user_configfile = os.path.join(CONFIG_DIR, 'config.xml')
		if not os.path.exists(user_configfile):
			if not os.path.exists(os.path.dirname(user_configfile)):
				os.makedirs(os.path.dirname(user_configfile))
			shutil.copy2(os.path.dirname(__file__) + "/config/config.xml", os.path.dirname(user_configfile))
		#print(os.path.dirname(user_configfile))
		configfile = user_configfile
		#print(configfile)

		self.config_manager = config_manager.ConfigManager(configfile)
		self.find_options = self.config_manager.load_configure('FindOption')
		self.config_manager.to_bool(self.find_options)
		
		self.find_dlg_setting = self.config_manager.load_configure('FindGUI')
		self.config_manager.to_bool(self.find_dlg_setting)

		self.shortcuts = self.config_manager.load_configure('Shortcut')
		self.result_highlight = self.config_manager.load_configure('ResultDisplay')
		
		self.result_gui_settings = self.config_manager.load_configure('ResultGUI')
		self.config_manager.to_bool(self.result_gui_settings)
		
		user_patterns = os.path.join(CONFIG_DIR, 'patterns.xml')
		if not os.path.exists(user_patterns):
			if not os.path.exists(os.path.dirname(user_patterns)):
				os.makedirs(os.path.dirname(user_patterns))
			shutil.copy2(os.path.dirname(__file__) + "/config/patterns.xml", os.path.dirname(user_patterns))
		#print os.path.dirname(user_patterns)
		patternsfile = user_patterns
		#print patternsfile
		
		self.patterns_manager = config_manager.ConfigManager(patternsfile)
		self.find_history = self.patterns_manager.load_list('FindHistory')
		self.replace_history = self.patterns_manager.load_list('ReplaceHistory')
		self.filter_history = self.patterns_manager.load_list('FilterHistory')
		self.path_history = self.patterns_manager.load_list('PathHistory')
		self.find_bookmarks = self.patterns_manager.load_list('FindBookmark')
		self.replace_bookmarks = self.patterns_manager.load_list('ReplaceBookmark')
		self.filter_bookmarks = self.patterns_manager.load_list('FilterBookmark')
		self.path_bookmarks = self.patterns_manager.load_list('PathBookmark')

		self._results_view = FindResultView(window, self.result_gui_settings)
		icon = Gtk.Image.new_from_stock(Gtk.STOCK_FIND_AND_REPLACE, Gtk.IconSize.MENU)
		self._window.get_bottom_panel().add_item(self._results_view, 'AdvancedFindBottomPanel', _("Advanced Find/Replace"), icon)
		
		self.msgDialog = Gtk.MessageDialog(self._window, 
						Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
						Gtk.MessageType.INFO,
						Gtk.ButtonsType.CLOSE,
						None)
		
		# Insert menu items
		self._insert_menu()

	def deactivate(self):
		# Remove any installed menu items
		self._remove_menu()

		self.config_manager.update_configure('FindOption', self.find_options)
		self.config_manager.update_configure('FindGUI', self.find_dlg_setting)
		#self.config_manager.update_configure('Shortcut', self.shortcuts)
		self.config_manager.update_configure('ResultDisplay', self.result_highlight)
		self.result_gui_settings.update(self._results_view.get_show_button_option())
		self.config_manager.update_configure('ResultGUI', self.result_gui_settings)
		self.config_manager.update_config_file(self.config_manager.config_file)
		
		if not self.find_dlg_setting['KEEP_HISTORY']:
			self.find_history = []
			self.replace_history = []
			self.filter_history = []
			self.path_history = []
		self.patterns_manager.update_list('FindHistory', self.find_history)
		self.patterns_manager.update_list('ReplaceHistory', self.replace_history)
		self.patterns_manager.update_list('FilterHistory', self.filter_history)
		self.patterns_manager.update_list('PathHistory', self.path_history)
		self.patterns_manager.update_list('FindBookmark', self.find_bookmarks)
		self.patterns_manager.update_list('ReplaceBookmark', self.replace_bookmarks)
		self.patterns_manager.update_list('FilterBookmark', self.filter_bookmarks)
		self.patterns_manager.update_list('PathBookmark', self.path_bookmarks)
		self.patterns_manager.update_config_file(self.patterns_manager.config_file)

		self._window = None
		self._plugin = None
		self.find_ui = None
		self.find_history = None
		self.replace_history = None
		self.filter_history = None
		self.path_history = None
		self.find_bookmarks = None
		self.replace_bookmarks = None
		self.filter_bookmarks = None
		self.path_bookmarks = None
		self._results_view = None
		
		'''
		self.config_manager.update_config_file(self.config_manager.config_file, 'search_option', self.find_options)
		self.config_manager.update_config_file(self.config_manager.config_file, 'find_dialog', self.find_dlg_setting)
		#self.config_manager.update_config_file(self.config_manager.config_file, 'shortcut', self.shortcuts)
		self.config_manager.update_config_file(self.config_manager.config_file, 'result_highlight', self.result_highlight)
		
		self.result_gui_settings.update(self._results_view.get_show_button_option())
		self.config_manager.update_config_file(self.config_manager.config_file, 'result_gui_settings', self.result_gui_settings)
		#'''
	
	def _insert_menu(self):
		# Get the GtkUIManager
		manager = self._window.get_ui_manager()

		# Create a new action group
		self._action_group = Gtk.ActionGroup("AdvancedFindReplaceActions")
		self._action_group.add_actions( #[("AdvancedFindMenu", None, _('Advanced Find/Replace'))] + \
										[("advanced_find_active", None, _("Advanced Find/Replace"), self.shortcuts['ACTIVATE'], _("Advanced Find/Replace"), self.advanced_find_active),
										("find_next", None, _("Find Next"), self.shortcuts['FIND_NEXT'], _("Find Next"), self.find_next),
										("find_previous", None, _("Find Previous"), self.shortcuts['FIND_PREVIOUS'], _("Find Previous"), self.find_previous),
										("select_find_next", None, _("Select and Find Next"), self.shortcuts['SELECT_FIND_NEXT'], _("Select and Find Next"), self.select_find_next),
										("select_find_previous", None, _("Select and Find Previous"), self.shortcuts['SELECT_FIND_PREVIOUS'], _("Select and Find Previous"), self.select_find_previous),
										("advanced_find_configure", None, _("Advanced Find/Replace Settings"), None, _("Advanced Find/Replace Settings"), self.advanced_find_configure)]) 

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
		
	def show_message_dialog(self, dlg, text):
		dlg.set_property('text', text)
		dlg.run()
		dlg.hide()
		
	def advanced_find_configure(self, action, data = None):
		config_ui = ConfigUI(self._plugin)
		
	def advanced_find_active(self, action, data = None):
		doc = self._window.get_active_document()
		if not doc:
			return
			
		try:
			start, end = doc.get_selection_bounds()
			search_text = str(doc.get_text(start,end,True))
		except:
			search_text = self.current_search_pattern

		if self.find_ui == None:
			self.find_ui = AdvancedFindUI(self._plugin)
		else:
			self.find_ui.findDialog.present()
			self.find_ui.findTextComboboxtext.grab_focus()
			
		if search_text != "":
			self.find_ui.findTextComboboxtext.get_child().set_text(search_text)
		
		if self.current_replace_text != "":
			self.find_ui.replaceTextComboboxtext.get_child().set_text(self.current_replace_text)


		if self.current_file_pattern != "":
			self.find_ui.filterComboboxtext.get_child().set_text(self.current_file_pattern)

		'''	
		if self.current_path != "":
			self.find_ui.pathComboboxentrytext.get_child().set_text(self.current_path)
		#'''

	def create_regex(self, pattern, find_options):
		if find_options['REGEX_SEARCH'] == False:
			try:
				pattern = re.escape(str(r'%s' % pattern, "utf-8"))
			except:
				pattern = re.escape(r'%s' % pattern)
		else:
			try:
				pattern = str(r'%s' % pattern, "utf-8")
			except:
				pattern = r'%s' % pattern
		
		if find_options['MATCH_WHOLE_WORD'] == True:
			pattern = r'\b%s\b' % pattern
		
		re_flg = re.MULTILINE
		if find_options['MATCH_CASE'] == False:
			re_flg |= re.IGNORECASE
		try:
			regex = re.compile(pattern, re_flg)
		except:
			print('regex compile failed')
			regex = None
		
		return regex
		
	def advanced_find_in_doc(self, doc, search_pattern, find_options, forward_flg = True, replace_flg = False, around_flg = False):
		if search_pattern == "":
			return

		regex = self.create_regex(search_pattern, find_options)
		if not regex:
			return

		if doc.get_has_selection():
			sel_start, sel_end = doc.get_selection_bounds()
			match = regex.search(str(doc.get_text(sel_start, sel_end, True)))
			if match and replace_flg == True:
				if find_options['REGEX_SEARCH'] == False:
					replace_text = str(self.find_ui.replaceTextComboboxtext.get_active_text())
				else:
					replace_text = match.expand(str(self.find_ui.replaceTextComboboxtext.get_active_text()))
				doc.delete_selection(False, False)
				doc.insert_at_cursor(replace_text)
				replace_flg = False
			else:
				if forward_flg == True:
					doc.place_cursor(sel_end)
				else:
					doc.place_cursor(sel_start)
			
		view = self._window.get_active_view()
		start, end = doc.get_bounds()
		text = str(doc.get_text(start, end, True))
		#around_flg = False
		
		if forward_flg == True:
			start_pos = doc.get_iter_at_mark(doc.get_insert()).get_offset()
			end_pos = doc.get_end_iter().get_offset()
			match = regex.search(text, start_pos, end_pos)
			if match:
				result_start = doc.get_iter_at_offset(match.start())
				result_end = doc.get_iter_at_offset(match.end())
				doc.select_range(result_start, result_end)
				view.scroll_to_cursor()
		else:
			start_pos = doc.get_start_iter().get_offset()
			end_pos = doc.get_iter_at_mark(doc.get_insert()).get_offset()
			results = []
			match = regex.search(text, start_pos, end_pos)
			while match:
				results.append(match.span())
				start_pos = match.end() + 1
				match = regex.search(text, start_pos, end_pos)
			results_len = len(results)
			if results_len > 0:
				result_start = doc.get_iter_at_offset(results[results_len-1][0])
				result_end = doc.get_iter_at_offset(results[results_len-1][1])
				doc.select_range(result_start, result_end)
				view.scroll_to_cursor()
				
		if not doc.get_has_selection():
			if find_options['WRAP_AROUND'] == True and around_flg == False:
				if forward_flg == True:
					doc.place_cursor(doc.get_start_iter())
				else:
					doc.place_cursor(doc.get_end_iter())
				self.advanced_find_in_doc(doc, search_pattern, find_options, forward_flg, replace_flg, True)
			else:
				self.show_message_dialog(self.msgDialog, _("Nothing is found."))
				
		if replace_flg == True and doc.get_has_selection():
			if find_options['REGEX_SEARCH'] == False:
				replace_text = str(self.find_ui.replaceTextComboboxtext.get_active_text())
			else:
				replace_text = match.expand(str(self.find_ui.replaceTextComboboxtext.get_active_text()))
			doc.delete_selection(False, False)
			doc.insert_at_cursor(replace_text)
			replace_end = doc.get_iter_at_mark(doc.get_insert())
			replace_start = doc.get_iter_at_offset(replace_end.get_offset() - len(replace_text))
			doc.select_range(replace_start, replace_end)
			view.scroll_to_cursor()

	def auto_select_word(self, pattern=r'[_a-zA-Z][_a-zA-Z0-9]*'):
		doc = self._window.get_active_document()
		if doc.get_has_selection():
			start, end = doc.get_selection_bounds()
			return doc.get_text(start, end, True)
		else:
			current_iter = doc.get_iter_at_mark(doc.get_insert())
			line_num = current_iter.get_line()
			line_start = doc.get_iter_at_line(line_num)
			line_text = doc.get_text(line_start, doc.get_iter_at_line(line_num + 1), True)
			line_start_pos = line_start.get_offset()
			matches = re.finditer(pattern, line_text)
			for match in matches:
				if current_iter.get_offset() in range(line_start_pos + match.start(), line_start_pos + match.end() + 1):
					return match.group(0)
			return ''
					
	def find_next(self, action, data = None):
		#print 'find next'
		self.advanced_find_in_doc(self._window.get_active_document(), self.current_search_pattern, self.find_options, True)
	
	def find_previous(self, action, data = None):
		#print('find previous')
		self.advanced_find_in_doc(self._window.get_active_document(), self.current_search_pattern, self.find_options, False)
		
	def select_find_next(self, action, data = None):
		#print(self.auto_select_word())
		self.advanced_find_in_doc(self._window.get_active_document(), self.auto_select_word(), self.find_options, True)

	def select_find_previous(self, action, data = None):
		#print(self.auto_select_word())
		self.advanced_find_in_doc(self._window.get_active_document(), self.auto_select_word(), self.find_options, False)
		
	def advanced_find_all_in_doc(self, parent_it, doc, search_pattern, find_options, replace_flg = False, selection_only = False):
		if search_pattern == "":
			return
		
		regex = self.create_regex(search_pattern, find_options)
		if not regex:
			return

		self.result_highlight_off(doc)
		start, end = doc.get_bounds()
		text = str(doc.get_text(start, end, True))
		
		start_pos = 0
		end_pos = end.get_offset()
		if selection_only == True:
			try:
				sel_start, sel_end = doc.get_selection_bounds()
			except:
				#print('No selection is found.')
				return

			if sel_start and sel_end:
				start_pos = sel_start.get_offset()
				end_pos = sel_end.get_offset()
			else:
				return

		tree_it = None
		match = regex.search(text, start_pos, end_pos)
		if match:
			if not tree_it:
				doc_uri = doc.get_uri_for_display()
				#print(doc_uri)
				if doc_uri == None:
					uri = ''
				else:
					tab = Gedit.Tab.get_from_document(doc)
					uri = urllib.parse.unquote(doc.get_uri_for_display())
				tree_it = self._results_view.append_find_result_filename(parent_it, doc.get_short_name_for_display(), tab, uri)
			
			if replace_flg == False:
				while(match):
					line_num = doc.get_iter_at_offset(match.start()).get_line()
					line_start_pos = doc.get_iter_at_line(line_num).get_offset()
					match_end_line_cnt = doc.get_iter_at_offset(match.end()).get_line() + 1
					if match_end_line_cnt == doc.get_line_count():
						line_end_pos = end_pos
					else:
						line_end_pos = doc.get_iter_at_line(match_end_line_cnt).get_offset()
					line_text = text[line_start_pos:line_end_pos]
					self._results_view.append_find_result(tree_it, str(line_num+1), line_text, match.start(), match.end()-match.start(), "", line_start_pos)
					if match.start() == match.end():
						start_pos = match.end() + 1
					else:
						start_pos = match.end()
					if start_pos > end_pos:
						break
					match = regex.search(text, start_pos, end_pos)
			else:
				results = []
				replace_offset = 0
				doc.begin_user_action()
				while(match):
					if find_options['REGEX_SEARCH'] == False:
						replace_text = str(self.find_ui.replaceTextComboboxtext.get_active_text())
					else:
						replace_text = match.expand(str(self.find_ui.replaceTextComboboxtext.get_active_text()))
					if match.start() == match.end():
						break
					replace_start_pos = match.start() + replace_offset
					replace_end_pos = match.end() + replace_offset
					replace_start = doc.get_iter_at_offset(replace_start_pos)
					replace_end = doc.get_iter_at_offset(replace_end_pos)
					doc.delete(replace_start, replace_end)
					doc.insert(replace_start, replace_text)
					replace_text_len = len(replace_text)
					results.append([replace_start_pos, replace_text_len])
					replace_offset += replace_text_len - (match.end() - match.start())
					start_pos = match.end()
					if start_pos > end_pos:
						break
					match = regex.search(text, start_pos, end_pos)
				doc.end_user_action()
				
				start, end = doc.get_bounds()
				text = str(doc.get_text(start, end, True))

				for result in results:
					line_num = doc.get_iter_at_offset(result[0]).get_line()
					line_start_pos = doc.get_iter_at_line(line_num).get_offset()
					#line_end_pos = result[0]+result[1]
					match_end_line_cnt = doc.get_iter_at_offset(result[0]+result[1]).get_line() + 1
					if match_end_line_cnt == doc.get_line_count():
						line_end_pos = end_pos
					else:
						line_end_pos = doc.get_iter_at_line(match_end_line_cnt).get_offset()
					'''
					line_end_pos = doc.get_iter_at_line(doc.get_iter_at_offset(result[0]+result[1]).get_line()+1).get_offset()
					if line_end_pos == line_start_pos:
						line_end_pos = end_pos
					#'''
					line_text = text[line_start_pos:line_end_pos]
					self._results_view.append_find_result(tree_it, str(line_num+1), line_text, result[0], result[1], "", line_start_pos, True)
			
		self.result_highlight_on(tree_it)
	
	'''
	def check_file_pattern(self, path, pattern_text):
		pattern_list = re.split('\s*\|\s*', pattern_text)
		#print(os.path.basename(path).strip())
		for pattern in pattern_list:
			if fnmatch.fnmatch(os.path.basename(path).strip(), pattern):
				return True
		return False
	#'''
	
	def find_all_in_dir(self, parent_it, dir_path, file_pattern, search_pattern, find_options, replace_flg = False):
		#start_time = time.time()
		if search_pattern == "":
			return
			
		#d_list = []
		file_list = []
		grep_cmd = ['grep', '-l', '-I']
		if find_options['MATCH_WHOLE_WORD'] == True:
			grep_cmd.append('-w')
		if find_options['MATCH_CASE'] == False:
			grep_cmd.append('-i')
		if find_options['INCLUDE_SUBFOLDER'] == True:
			grep_cmd.append('-R')

		if not file_pattern == '': 
			pattern_list = re.split('\s*\|\s*', file_pattern)
			for f_pattern in pattern_list:
				if f_pattern.startswith('-'):
					grep_cmd.append('--exclude=' + f_pattern[1:])
				else:
					grep_cmd.append('--include=' + f_pattern)

		if find_options['REGEX_SEARCH'] == True:
			grep_cmd = grep_cmd + ['-E', '-e', search_pattern, dir_path]
		else:
			grep_cmd = grep_cmd + ['-F', '-e', search_pattern, dir_path]
		#print(grep_cmd)

		p = subprocess.Popen(grep_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		for e in p.stderr:
			print(e)

		for f in p.stdout:
			file_list.append(f[:-1])
			
		
		'''
		for root, dirs, files in os.walk(unicode(dir_path, 'utf-8')):
			for d in dirs:
				d_list.append(os.path.join(root, d))	
			for f in files:
				if self.check_file_pattern(f, unicode(file_pattern, 'utf-8')):
					if find_options['INCLUDE_SUBFOLDER'] == True:
						file_list.append(os.path.join(root, f))
					else:
						if os.path.dirname(f) not in d_list:
							file_list.append(os.path.join(root, f))
				self.find_ui.do_events()
		#'''
					
		#mid_time = time.time()
		#print('Use ' + str(mid_time-start_time) + ' seconds to find files.')
		
		self._results_view.is_busy(True)
		self._results_view.do_events()
					
		for file_path in file_list:
			if os.path.isfile(file_path):
				temp_doc = Gedit.Document()
				#file_uri = 'file://' + file_path
				#temp_doc.load(Gio.file_new_for_uri(file_uri), Gedit.encoding_get_from_charset('utf-8'), 0, 0, False)
				temp_doc.load(Gio.file_new_for_path(bytes.decode(file_path)), Gedit.encoding_get_from_charset('utf-8'), 0, 0, False)
				f_temp = open(file_path, 'r')
				try:
					text = str(f_temp.read())
				except:
					text = f_temp.read()
				f_temp.close()
				temp_doc.set_text(text)
				
				self.advanced_find_all_in_doc(parent_it, temp_doc, search_pattern, find_options, replace_flg)
				self.find_ui.do_events()
				if self._results_view.stopButton.get_sensitive() == False:
					break
				
		self._results_view.is_busy(False)
				
		#end_time = time.time()						
		#print('Use ' + str(end_time-mid_time) + ' seconds to find results.')
		#print('Total use ' + str(end_time-start_time) + ' seconds.')
						
	def result_highlight_on(self, file_it):
		if file_it == None:
			return
		if self._results_view.findResultTreemodel.iter_has_child(file_it):
			tab = self._results_view.findResultTreemodel.get_value(file_it, 3)
			if not tab:
				return
			for n in range(0,self._results_view.findResultTreemodel.iter_n_children(file_it)):
				it = self._results_view.findResultTreemodel.iter_nth_child(file_it, n)
				
				result_start = self._results_view.findResultTreemodel.get_value(it, 4)
				result_len = self._results_view.findResultTreemodel.get_value(it, 5)
				doc = tab.get_document()
				if doc.get_tag_table().lookup('result_highlight') == None:
					tag = doc.create_tag("result_highlight", foreground=self.result_highlight['FOREGROUND_COLOR'], background=self.result_highlight['BACKGROUND_COLOR'])
				doc.apply_tag_by_name('result_highlight', doc.get_iter_at_offset(result_start), doc.get_iter_at_offset(result_start + result_len))
		
	def result_highlight_off(self, doc):
		if doc.get_tag_table().lookup('result_highlight'):
			start, end = doc.get_bounds()
			doc.remove_tag_by_name('result_highlight', start, end)
			
		'''
		start, end = doc.get_bounds()
		if doc.get_tag_table().lookup('result_highlight') == None:
			tag = doc.create_tag("result_highlight", foreground=self.result_highlight['FOREGROUND_COLOR'], background=self.result_highlight['BACKGROUND_COLOR'])
		doc.remove_tag_by_name('result_highlight', start, end)
		#'''

	def show_bottom_panel(self):
		panel = self._window.get_bottom_panel()
		if panel.get_property("visible") == False:
			panel.set_property("visible", True)
		panel.activate_item(self._results_view)
		
	def set_bottom_panel_label(self, text = None, icon = None):
		tab = self._results_view
		if text:
			tab.get_parent().get_tab_label(tab).get_children()[0].get_child().get_children()[1].set_text(_(text))
		else:
			tab.get_parent().get_tab_label(tab).get_children()[0].get_child().get_children()[1].set_text(_("Advanced Find/Replace"))
		if icon:
			tab.get_parent().get_tab_label(tab).get_children()[0].get_child().get_children()[0].set_from_file(icon)
		else:
			tab.get_parent().get_tab_label(tab).get_children()[0].get_child().get_children()[0].set_from_icon_name('gtk-find-and-replace', Gtk.IconSize.MENU)
		
		
		

# -*- encoding:utf-8 -*-


# find_result.py is part of advancedfind-gedit.
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
import urllib.request, urllib.parse, urllib.error
import re
from . import config_manager
import shutil


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


class FindResultView(Gtk.HBox):
	def __init__(self, window, result_gui_settings):
		Gtk.HBox.__init__(self)
		self._window = window
		self.result_gui_settings = result_gui_settings

		# load color theme of results list	
		user_formatfile = os.path.join(CONFIG_DIR, 'theme/'+self.result_gui_settings['COLOR_THEME']+'.xml')
		if not os.path.exists(user_formatfile):
			if not os.path.exists(os.path.dirname(user_formatfile)):
				os.makedirs(os.path.dirname(user_formatfile))
			shutil.copy2(os.path.dirname(__file__) + "/config/theme/default.xml", os.path.dirname(user_formatfile))
		#print(os.path.dirname(user_formatfile))
		format_file = user_formatfile
		#print(format_file)

		self.result_format = config_manager.ConfigManager(format_file).load_configure('result_format')
		config_manager.ConfigManager(format_file).to_bool(self.result_format)
		
		# initialize find result treeview
		self.findResultTreeview = Gtk.TreeView()
		resultsCellRendererText = Gtk.CellRendererText()
		if self.result_format['BACKGROUND']:
			resultsCellRendererText.set_property('cell-background', self.result_format['BACKGROUND'])
		resultsCellRendererText.set_property('font', self.result_format['RESULT_FONT'])
		
		self.findResultTreeview.append_column(Gtk.TreeViewColumn("line", resultsCellRendererText, markup=1))
		self.findResultTreeview.append_column(Gtk.TreeViewColumn("content", resultsCellRendererText, markup=2))
		#self.findResultTreeview.append_column(Gtk.TreeViewColumn("result_start", Gtk.CellRendererText(), text=4))
		#self.findResultTreeview.append_column(Gtk.TreeViewColumn("result_len", Gtk.CellRendererText(), text=5))
		self.findResultTreeview.append_column(Gtk.TreeViewColumn("uri", resultsCellRendererText, text=6))

		self.findResultTreeview.set_grid_lines(int(self.result_format['GRID_PATTERN']))		# 0: None; 1: Horizontal; 2: Vertical; 3: Both
		self.findResultTreeview.set_headers_visible(self.result_format['SHOW_HEADERS'])
		
		try:
			column_num = self.findResultTreeview.get_n_columns()
		except:
			# For older gtk version.
			column_num = self.findResultTreeview.get_columns()
		if self.result_format['SHOW_HEADERS']:
			for i in range(0, column_num):
				self.findResultTreeview.get_column(i).set_resizable(True)
		else:
			for i in range(0, column_num):
				self.findResultTreeview.get_column(i).set_sizing(1)	# 1=autosizing

		self.findResultTreeview.set_rules_hint(True)
		self.findResultTreemodel = Gtk.TreeStore(int, str, str, object, int, int, str)
		self.findResultTreemodel.set_sort_column_id(0, Gtk.SortType.ASCENDING)
		self.findResultTreeview.connect("cursor-changed", self.on_findResultTreeview_cursor_changed_action)
		self.findResultTreeview.connect("button-press-event", self.on_findResultTreeview_button_press_action)
		self.findResultTreeview.set_model(self.findResultTreemodel)

		# initialize scrolled window
		scrollWindow = Gtk.ScrolledWindow()
		scrollWindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		scrollWindow.add(self.findResultTreeview)
		
		# put a separator
		v_separator1 = Gtk.VSeparator()
		
		# initialize button box
		v_box = Gtk.VBox()
		v_buttonbox = Gtk.VButtonBox()
		v_buttonbox.set_layout(Gtk.ButtonBoxStyle.END)
		v_buttonbox.set_spacing(5)
		v_buttonbox.set_homogeneous(True)
		self.selectNextButton = Gtk.Button(_("Next"))
		self.selectNextButton.set_no_show_all(True)
		self.selectNextButton.connect("clicked", self.on_selectNextButton_clicked_action)
		self.expandAllButton = Gtk.Button(_("Expand All"))
		self.expandAllButton.set_no_show_all(True)
		self.expandAllButton.connect("clicked", self.on_expandAllButton_clicked_action)
		self.collapseAllButton = Gtk.Button(_("Collapse All"))
		self.collapseAllButton.set_no_show_all(True)
		self.collapseAllButton.connect("clicked", self.on_collapseAllButton_clicked_action)
		self.clearHighlightButton = Gtk.Button(_("Clear Highlight"))
		self.clearHighlightButton.set_no_show_all(True)
		self.clearHighlightButton.connect("clicked", self.on_clearHightlightButton_clicked_action)
		self.clearButton = Gtk.Button(_("Clear"))
		self.clearButton.set_no_show_all(True)
		self.clearButton.connect("clicked", self.on_clearButton_clicked_action)
		self.stopButton = Gtk.Button(_("Stop"))
		self.stopButton.set_no_show_all(True)
		self.stopButton.connect("clicked", self.on_stopButton_clicked_action)
		self.stopButton.set_sensitive(False)

		v_buttonbox.pack_start(self.selectNextButton, False, False, 5)
		v_buttonbox.pack_start(self.expandAllButton, False, False, 5)
		v_buttonbox.pack_start(self.collapseAllButton, False, False, 5)
		v_buttonbox.pack_start(self.clearHighlightButton, False, False, 5)
		v_buttonbox.pack_start(self.clearButton, False, False, 5)
		v_buttonbox.pack_start(self.stopButton, False, False, 5)
		v_box.pack_end(v_buttonbox, False, False, 5)
		
		#self._status = Gtk.Label()
		#self._status.set_text('test')
		#self._status.hide()
		#v_box.pack_end(self._status, False)
		
		self.pack_start(scrollWindow, True, True, 5)
		self.pack_start(v_separator1, False, False, 0)
		self.pack_start(v_box, False, False, 5)
		
		self.show_all()
		
		#initialize context menu
		self.contextMenu = Gtk.Menu()
		self.expandAllItem = Gtk.MenuItem.new_with_label(_('Expand All'))
		self.collapseAllItem = Gtk.MenuItem.new_with_label(_('Collapse All'))
		self.clearHighlightItem = Gtk.MenuItem.new_with_label(_('Clear Highlight'))
		self.clearItem = Gtk.MenuItem.new_with_label(_('Clear'))
		self.stopItem = Gtk.MenuItem.new_with_label(_('Stop'))
		self.stopItem.set_sensitive(False)
		self.markupItem = Gtk.MenuItem.new_with_label(_('Markup'))

		self.contextMenu.append(self.expandAllItem)
		self.contextMenu.append(self.collapseAllItem)
		self.contextMenu.append(self.clearHighlightItem)
		self.contextMenu.append(self.clearItem)
		self.contextMenu.append(self.stopItem)
		self.contextMenu.append(self.markupItem)
		
		self.expandAllItem.connect('activate', self.on_expandAllItem_activate)
		self.collapseAllItem.connect('activate', self.on_collapseAllItem_activate)
		self.clearHighlightItem.connect('activate', self.on_clearHighlightItem_activate)
		self.clearItem.connect('activate', self.on_clearItem_activate)
		self.stopItem.connect('activate', self.on_stopItem_activate)
		self.markupItem.connect('activate', self.on_markupItem_activate)

		self.expandAllItem.show()
		self.collapseAllItem.show()
		self.clearHighlightItem.show()
		self.clearItem.show()
		self.stopItem.show()
		#self.markupItem.show()
		
		self.contextMenu.append(Gtk.SeparatorMenuItem())
		
		self.showButtonsItem = Gtk.MenuItem.new_with_label(_('Show Buttons'))
		self.contextMenu.append(self.showButtonsItem)
		self.showButtonsItem.show()
		
		self.showButtonsSubmenu = Gtk.Menu()
		self.showNextButtonItem = Gtk.CheckMenuItem.new_with_label(_('Next'))
		self.showExpandAllButtonItem = Gtk.CheckMenuItem.new_with_label(_('Expand All'))
		self.showCollapseAllButtonItem = Gtk.CheckMenuItem.new_with_label(_('Collapse All'))
		self.showClearHighlightButtonItem = Gtk.CheckMenuItem.new_with_label(_('Clear Highlight'))
		self.showClearButtonItem = Gtk.CheckMenuItem.new_with_label(_('Clear'))
		self.showStopButtonItem = Gtk.CheckMenuItem.new_with_label(_('Stop'))

		self.showButtonsSubmenu.append(self.showNextButtonItem)
		self.showButtonsSubmenu.append(self.showExpandAllButtonItem)
		self.showButtonsSubmenu.append(self.showCollapseAllButtonItem)
		self.showButtonsSubmenu.append(self.showClearHighlightButtonItem)
		self.showButtonsSubmenu.append(self.showClearButtonItem)
		self.showButtonsSubmenu.append(self.showStopButtonItem)
		
		self.showNextButtonItem.connect('activate', self.on_showNextButtonItem_activate)
		self.showExpandAllButtonItem.connect('activate', self.on_showExpandAllButtonItem_activate)
		self.showCollapseAllButtonItem.connect('activate', self.on_showCollapseAllButtonItem_activate)
		self.showClearHighlightButtonItem.connect('activate', self.on_showClearHighlightButtonItem_activate)
		self.showClearButtonItem.connect('activate', self.on_showClearButtonItem_activate)
		self.showStopButtonItem.connect('activate', self.on_showStopButtonItem_activate)
		
		self.showNextButtonItem.show()
		self.showExpandAllButtonItem.show()
		self.showCollapseAllButtonItem.show()
		self.showClearHighlightButtonItem.show()
		self.showClearButtonItem.show()
		self.showStopButtonItem.show()
		
		self.showButtonsItem.set_submenu(self.showButtonsSubmenu)
		
		self.show_buttons()


		
	def do_events(self):
		while Gtk.events_pending():
			Gtk.main_iteration()
			
	def to_xml_text(self, text):
		# & -> &amp;
		# < -> &lt;
		# > -> &gt;
		# ' -> &apos;
		# " -> &quot;
		return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace("'", '&apos;').replace('"', '&quot;')
		
	def remove_markup(self, text):
		regex = re.compile(r'<.+>([^ <>]+)</.+>')
		return regex.sub(r'\1', text)
		
	def on_findResultTreeview_cursor_changed_action(self, object):
		if object.get_selection():
			model, it = object.get_selection().get_selected()
		else:
			return
		if not it:
			return
		
		try:
			m = re.search('.+(<.+>)+([0-9]+)(<.+>)+.*', model.get_value(it, 1))
			#m = re.search('.+(.+)+([0-9]+)(.+)+.*', model.get_value(it, 1))
			line_num = int(m.group(2))
		except:
			return
		
		result_start = model.get_value(it, 4)
		result_len = model.get_value(it, 5)
		
		parent_it = model.iter_parent(it)
		if parent_it:
			uri = model.get_value(parent_it, 6)
			tab = model.get_value(parent_it, 3)
		else:
			return
			
		# Tab wasn't passed, try to find one		
		if not tab:
			docs = self._window.get_documents()
			for doc in docs:
				if urllib.parse.unquote(doc.get_uri_for_display()) == uri:
					tab = Gedit.Tab.get_from_document(doc)
			
		# Still nothing? Open the file then
		if not tab:
			m = re.search('[a-zA-Z0-9]+\:\/\/.+', uri)
			if m == None:
				tab = self._window.create_tab_from_location(Gio.file_new_for_path(uri), None, line_num, 0, False, False)
			else:
				tab = self._window.create_tab_from_location(Gio.file_new_for_uri(uri), None, line_num, 0, False, False)
			self.do_events()
			
		if tab:
			self._window.set_active_tab(tab)
			doc = tab.get_document()
			doc.select_range(doc.get_iter_at_offset(result_start), doc.get_iter_at_offset(result_start + result_len))
			view = tab.get_view()
			view.scroll_to_cursor()
				
	def on_findResultTreeview_button_press_action(self, object, event):
		if event.button == 3:
			#right button click
			self.contextMenu.popup(None, None, None, None, event.button, event.time)
		
	def on_expandAllItem_activate(self, object):
		self.findResultTreeview.expand_all()
		
	def on_collapseAllItem_activate(self, object):
		self.findResultTreeview.collapse_all()
		
	def on_clearHighlightItem_activate(self, object):
		self.clear_highlight()
		
	def on_clearItem_activate(self, object):
		self.clear_find_result()
		
	def on_stopItem_activate(self, object):
		self.stopButton.set_sensitive(False)
		object.set_sensitive(False)
		
	def on_markupItem_activate(self, object):
		model, it = self.findResultTreeview.get_selection().get_selected()
		if not it:
			return

		self.markup_row(model, it)
	
	def markup_row(self, model, it):
		if not it:
			return
		
		mark_head = '<span background="gray">'
		mark_foot = '</span>'
		line_str = model.get_value(it, 1)
		text_str = model.get_value(it, 2)
		if line_str.startswith(mark_head) and line_str.endswith(mark_foot):
			model.set_value(it, 1, line_str[len(mark_head):-1*len(mark_foot)])
		else:
			model.set_value(it, 1, mark_head + line_str + mark_foot)
		if text_str.startswith(mark_head) and text_str.endswith(mark_foot):
			model.set_value(it, 2, text_str[len(mark_head):-1*len(mark_foot)])
		else:
			model.set_value(it, 2, mark_head + text_str + mark_foot)
			
		if self.findResultTreemodel.iter_has_child(it):
			for i in range(0, self.findResultTreemodel.iter_n_children(it)):
				self.markup_row(model, self.findResultTreemodel.iter_nth_child(it, i))
				
	def on_showNextButtonItem_activate(self, object):
		if self.showNextButtonItem.get_active() == True:
			self.result_gui_settings['NEXT_BUTTON'] = True
			self.selectNextButton.show()
		else:
			self.result_gui_settings['NEXT_BUTTON'] = False
			self.selectNextButton.hide()

	def on_showExpandAllButtonItem_activate(self, object):
		if self.showExpandAllButtonItem.get_active() == True:
			self.result_gui_settings['EXPAND_ALL_BUTTON'] = True
			self.expandAllButton.show()
		else:
			self.result_gui_settings['EXPAND_ALL_BUTTON'] = False
			self.expandAllButton.hide()
		
	def on_showCollapseAllButtonItem_activate(self, object):
		if self.showCollapseAllButtonItem.get_active() == True:
			self.result_gui_settings['COLLAPSE_ALL_BUTTON'] = True
			self.collapseAllButton.show()
		else:
			self.result_gui_settings['COLLAPSE_ALL_BUTTON'] = False
			self.collapseAllButton.hide()
		
	def on_showClearHighlightButtonItem_activate(self, object):
		if self.showClearHighlightButtonItem.get_active() == True:
			self.result_gui_settings['CLEAR_HIGHLIGHT_BUTTON'] = True
			self.clearHighlightButton.show()
		else:
			self.result_gui_settings['CLEAR_HIGHLIGHT_BUTTON'] = False
			self.clearHighlightButton.hide()
		
	def on_showClearButtonItem_activate(self, object):
		if self.showClearButtonItem.get_active() == True:
			self.result_gui_settings['CLEAR_BUTTON'] = True
			self.clearButton.show()
		else:
			self.result_gui_settings['CLEAR_BUTTON'] = False
			self.clearButton.hide()
			
	def on_showStopButtonItem_activate(self, object):
		if self.showStopButtonItem.get_active() == True:
			self.result_gui_settings['STOP_BUTTON'] = True
			self.stopButton.show()
		else:
			self.result_gui_settings['STOP_BUTTON'] = False
			self.stopButton.hide()

	def on_selectNextButton_clicked_action(self, object):
		path, column = self.findResultTreeview.get_cursor()
		if not path:
			return
		it = self.findResultTreemodel.get_iter(path)
		if self.findResultTreemodel.iter_has_child(it):
			self.findResultTreeview.expand_row(path, True)
			it1 = self.findResultTreemodel.iter_children(it)
		else:
			it1 = self.findResultTreemodel.iter_next(it)
			
		if not it1:
			it1 = self.findResultTreemodel.iter_parent(it)
			if not it1:
				return
			else:
				it2 = self.findResultTreemodel.iter_next(it1)
				if not it2:
					it2 = self.findResultTreemodel.iter_parent(it1)
					if not it2:
						return
					else:
						it3 = self.findResultTreemodel.iter_next(it2)
						if not it3:
							return
						else:
							path = self.findResultTreemodel.get_path(it3)
				else:
			 		path = self.findResultTreemodel.get_path(it2)
		else:
			path = self.findResultTreemodel.get_path(it1) 
		self.findResultTreeview.set_cursor(path, column, False)

	def on_clearHightlightButton_clicked_action(self, object):
		self.clear_highlight()
		
	def on_expandAllButton_clicked_action(self, object):
		self.findResultTreeview.expand_all()
		
	def on_collapseAllButton_clicked_action(self, object):
		self.findResultTreeview.collapse_all()
			
		
	def on_clearButton_clicked_action(self, object):
		self.clear_find_result()
		
	def on_stopButton_clicked_action(self, object):
		object.set_sensitive(False)

	def append_find_pattern(self, pattern, replace_flg = False, replace_text = None):
		self.findResultTreeview.collapse_all()
		idx = self.findResultTreemodel.iter_n_children(None)
		header = '#' + str(idx) + ' - '
		if replace_flg == True:
			mode = self.result_format['MODE_REPLACE'] %{'HEADER' : header, 'PATTERN' : self.to_xml_text(str(pattern)), 'REPLACE_TEXT' : self.to_xml_text(str(replace_text))}
			#mode = header + ' Replace ' + pattern + ' with ' + replace_text
			it = self.findResultTreemodel.append(None, [idx, mode, '', None, 0, 0, ''])
		else:
			mode = self.result_format['MODE_FIND'] %{'HEADER' : header, 'PATTERN' : self.to_xml_text(str(pattern))}
			#mode = header + ' Search ' + pattern
			it = self.findResultTreemodel.append(None, [idx, mode, '', None, 0, 0, ''])
		return it
	
	def append_find_result_filename(self, parent_it, filename, tab, uri):
		filename_str = self.result_format['FILENAME'] % {'FILENAME' : self.to_xml_text(str(filename))}
		#filename_str = filename
		it = self.findResultTreemodel.append(parent_it, [0, filename_str, '', tab, 0, 0, uri])
		return it
		
	def append_find_result(self, parent_it, line, text, result_offset_start = 0, result_len = 0, uri = "", line_start_pos = 0, replace_flg = False):
		result_line = self.result_format['LINE'] % {'LINE_NUM' : line}
		#result_line = 'Line ' + str(line) + ' : '
		markup_start = result_offset_start - line_start_pos
		markup_end = markup_start + result_len
		
		text_header = self.to_xml_text(text[0:markup_start])
		text_marked = self.to_xml_text(text[markup_start:markup_end])
		text_footer = self.to_xml_text(text[markup_end:])

		if replace_flg == False:
			result_text = (text_header + self.result_format['FIND_RESULT_TEXT'] % {'RESULT_TEXT' : text_marked} + text_footer).rstrip()
			#result_text = (text_header + text_marked + text_footer).rstrip()
			self.findResultTreemodel.append(parent_it, [int(line), result_line, result_text, None, result_offset_start, result_len, uri])
		else:
			result_text = (text_header + self.result_format['REPLACE_RESULT_TEXT'] % {'RESULT_TEXT' : text_marked} + text_footer).rstrip()
			#result_text = (text_header + text_marked + text_footer).rstrip()
			self.findResultTreemodel.append(parent_it, [int(line), result_line, result_text, None, result_offset_start, result_len, uri])
		
	def show_find_result(self):
		path = Gtk.TreePath.new_from_string(str(self.findResultTreemodel.iter_n_children(None) - 1))
		self.findResultTreeview.expand_row(path, True)
		pattern_it = self.findResultTreemodel.get_iter(path)
		self.findResultTreeview.set_cursor(self.findResultTreemodel.get_path(pattern_it), None, False)
		
		file_cnt = self.findResultTreemodel.iter_n_children(pattern_it)
		total_hits = 0
		for i in range(0, file_cnt):
			it1 = self.findResultTreemodel.iter_nth_child(pattern_it, i)
			hits_cnt = self.findResultTreemodel.iter_n_children(it1)
			total_hits += hits_cnt
			hits_str = self.result_format['HITS_CNT'] % {'HITS_CNT' : str(hits_cnt)}
			#hits_str = str(hits_cnt) + ' hits'
			self.findResultTreemodel.set_value(it1, 2, hits_str)
		total_hits_str = self.result_format['TOTAL_HITS'] % {'TOTAL_HITS': str(total_hits), 'FILES_CNT' : str(file_cnt)}
		#total_hits_str = 'Total ' +  str(total_hits) + ' hits in ' + str(file_cnt)
		self.findResultTreemodel.set_value(pattern_it, 2, total_hits_str)

	def clear_highlight(self):
		for doc in self._window.get_documents():
			start, end = doc.get_bounds()
			if doc.get_tag_table().lookup('result_highlight') == None:
				tag = doc.create_tag("result_highlight", foreground='yellow', background='red')
			doc.remove_tag_by_name('result_highlight', start, end)
		
	def clear_find_result(self):
		try:
			vadj = self._window.get_active_view().get_vadjustment()
			vadj_value = vadj.get_value()
		except:
			self.findResultTreemodel.clear()
			return
		self.findResultTreemodel.clear()
		vadj.set_value(vadj_value)
		
	def get_show_button_option(self):
		return self.result_gui_settings
		
	def show_buttons(self):
		if self.result_gui_settings['NEXT_BUTTON'] == True:
			self.selectNextButton.show()
			self.showNextButtonItem.set_active(True)
		if self.result_gui_settings['EXPAND_ALL_BUTTON'] == True:
			self.expandAllButton.show()
			self.showExpandAllButtonItem.set_active(True)
		if self.result_gui_settings['COLLAPSE_ALL_BUTTON'] == True:
			self.collapseAllButton.show()
			self.showCollapseAllButtonItem.set_active(True)
		if self.result_gui_settings['CLEAR_HIGHLIGHT_BUTTON'] == True:
			self.clearHighlightButton.show()
			self.showClearHighlightButtonItem.set_active(True)
		if self.result_gui_settings['CLEAR_BUTTON'] == True:
			self.clearButton.show()
			self.showClearButtonItem.set_active(True)
		if self.result_gui_settings['STOP_BUTTON'] == True:
			self.stopButton.show()
			self.showStopButtonItem.set_active(True)
			
	def is_busy(self, busy_flg = True):
		if busy_flg:
			self.clearButton.set_sensitive(False)
			self.stopButton.set_sensitive(True)
			self.clearItem.set_sensitive(False)
			self.stopItem.set_sensitive(True)
		else:
			self.clearButton.set_sensitive(True)
			self.stopButton.set_sensitive(False)
			self.clearItem.set_sensitive(True)
			self.stopItem.set_sensitive(False)
		self.do_events()		
	



if __name__ == "__main__":
	view = FindResultView(None)
	window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
	window.add(view)
	window.show_all()
	Gtk.main()



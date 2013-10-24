# -*- encoding:utf-8 -*-


# advancedfind_ui.py is part of advancedfind-gedit.
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


from gi.repository import GObject, Gtk, Gedit, Gio

import os.path
import os
import re
#import config_manager
#import gconf


#Gtk.glade.bindtextdomain('advancedfind', os.path.join(os.path.dirname(__file__), 'locale'))
#Gtk.glade.bindtextdomain('advancedfind', '/usr/share/locale')
#Gtk.glade.textdomain('advancedfind')



class AdvancedFindUI(object):
	def __init__(self, plugin):
		try:
			self._instance, self._window = plugin.get_instance()
		except:
			pass

		gladefile = os.path.join(os.path.dirname(__file__),"FindDialog.glade")
		ui = Gtk.Builder()
		ui.set_translation_domain('advancedfind')
		ui.add_from_file(gladefile)
		ui.connect_signals({ "on_findDialog_destroy" : self.on_findDialog_destroy_action,
							"on_findDialog_focus_in_event": self.on_findDialog_focus_in_event_action,
							"on_findDialog_focus_out_event" : self.on_findDialog_focus_out_event_action,
							"on_findDialog_show" : self.on_findDialog_show_action,
							#"on_findDialog_grab_focus" : self.on_findDialog_focus_in_event_action,
							#"on_findDialog_grab_broken_event" : self.on_findDialog_focus_out_event_action,
							
							"on_findEntry_icon_press" : self.findEntryIconPress,
							"on_replaceEntry_icon_press" : self.replaceEntryIconPress,
							"on_filterEntry_icon_press" : self.filterEntryIconPress,
							"on_pathEntry_icon_press" : self.pathEntryIconPress,
							
							"findTextComboboxtext_changed_cb" : self.findTextComboboxtext_changed,
							"replaceTextComboboxtext_changed_cb" : self.replaceTextComboboxtext_changed,
							"filterComboboxtext_changed_cb" : self.filterComboboxtext_changed,
							"pathComboboxtext_changed_cb" : self.pathComboboxtext_changed,
							
							"on_findButton_clicked" : self.on_findButton_clicked_action,
							"on_replaceButton_clicked" : self.on_replaceButton_clicked_action,
							"on_findAllButton_clicked" : self.on_findAllButton_clicked_action,
							"on_replaceAllButton_clicked" : self.on_replaceAllButton_clicked_action,
							"on_closeButton_clicked" : self.on_closeButton_clicked_action,
							"on_selectPathButton_clicked" : self.on_selectPathButton_clicked_action,
							"on_selectPathDialogOkButton_clicked" : self.on_selectPathDialogOkButton_clicked_action,
							"on_selectPathDialogCancelButton_clicked" : self.on_selectPathDialogCancelButton_clicked_action,
							
							"on_matchWholeWordCheckbutton_toggled" : self.on_matchWholeWordCheckbutton_toggled_action,
							"on_matchCaseCheckbutton_toggled" : self.on_matchCaseCheckbutton_toggled_action,
							"on_wrapAroundCheckbutton_toggled" : self.on_wrapAroundCheckbutton_toggled_action,
							"on_followCurrentDocCheckbutton_toggled" : self.on_followCurrentDocCheckbutton_toggled_action,
							"on_includeSubfolderCheckbutton_toggled" : self.on_includeSubfolderCheckbutton_toggled_action,
							"on_regexSearchCheckbutton_toggled" : self.on_regexSearchCheckbutton_toggled_action,
							
							"on_forwardRadiobutton_toggled" : self.directionRadiobuttonGroup_action,
							"on_backwardRadiobutton_toggled" : self.directionRadiobuttonGroup_action,
							
							"on_currentFileRadiobutton_toggled" : self.scopeRadiobuttonGroup_action,
							"on_allFilesRadiobutton_toggled" : self.scopeRadiobuttonGroup_action,
							"on_allFilesInPathRadiobutton_toggled" : self.scopeRadiobuttonGroup_action,
							"on_currentSelectionRadiobutton_toggled" : self.scopeRadiobuttonGroup_action,
							
							"on_opacityScale_vlaue_changed" : self.on_opacityScale_vlaue_changed_action })

		self.findDialog = ui.get_object("findDialog")
		#self.findDialog.set_keep_above(True)
		self.findDialog.set_transient_for(self._window)

		accelgroup = Gtk.AccelGroup()
		#key, modifier = Gtk.accelerator_parse('Escape')
		#accelgroup.connect(key, modifier, Gtk.AccelFlags.VISIBLE, self.esc_accel_action)
		key, modifier = Gtk.accelerator_parse('Return')
		accelgroup.connect(key, modifier, Gtk.AccelFlags.VISIBLE, self.return_accel_action)
		key, modifier = Gtk.accelerator_parse('KP_Enter')
		accelgroup.connect(key, modifier, Gtk.AccelFlags.VISIBLE, self.return_accel_action)
		self.findDialog.add_accel_group(accelgroup)

		self.findTextComboboxtext = ui.get_object("findTextComboboxtext")
		#self.findTextListstore = ui.get_object("findTextListstore")
		#find_cell = Gtk.CellRendererText()
		#self.findTextComboboxtext.pack_start(find_cell, True)
		#self.findTextComboboxtext.add_attribute(find_cell, 'text', 0)
		self.findTextComboboxtext.set_entry_text_column(0)
		try:
			for find_text in self._instance.find_history:
				self.findTextComboboxtext.prepend_text(find_text)
			for find_text in self._instance.find_bookmarks:
				self.findTextComboboxtext.append_text(find_text)
		except:
			pass

		self.replaceTextComboboxtext = ui.get_object("replaceTextComboboxtext")
		#self.replaceTextListstore = ui.get_object("replaceTextListstore")
		#replace_cell = Gtk.CellRendererText()
		#self.replaceTextComboboxtext.pack_start(replace_cell, True)
		#self.replaceTextComboboxtext.add_attribute(replace_cell, 'text', 0)
		self.replaceTextComboboxtext.set_entry_text_column(0)
		try:
			for replace_text in self._instance.replace_history:
				self.replaceTextComboboxtext.prepend_text(replace_text)
			for replace_text in self._instance.replace_bookmarks:
				self.replaceTextComboboxtext.append_text(replace_text)
		except:
			pass
		
		self.filterComboboxtext = ui.get_object("filterComboboxtext")
		self.filterComboboxtext.set_entry_text_column(0)
		#self.filterComboboxtext.get_child().set_text("*")
		#self.filterComboboxtext.prepend_text("*")
		try:
			for file_filter in self._instance.filter_history:
				self.filterComboboxtext.prepend_text(file_filter)
			for file_filter in self._instance.filter_bookmarks:
				self.filterComboboxtext.append_text(file_filter)
		except:
			pass
			
		self.pathExpander = ui.get_object("pathExpander")
		self.selectPathFilechooserdialog = ui.get_object("selectPathFilechooserdialog")
		
		self.pathComboboxtext = ui.get_object("pathComboboxtext")
		self.pathComboboxtext.set_entry_text_column(0)
			
		try:
			for path in self._instance.path_history:
				self.pathComboboxtext.prepend_text(path)
			for path in self._instance.path_bookmarks:
				self.pathComboboxtext.append_text(path)
		except:
			pass
		
		self.pathExpander = ui.get_object("pathExpander")
		self.pathExpander.set_expanded(self._instance.find_dlg_setting['PATH_EXPANDED'])		
		
		self.matchWholeWordCheckbutton = ui.get_object("matchWholeWordCheckbutton")
		self.matchCaseCheckbutton = ui.get_object("matchCaseCheckbutton")
		self.wrapAroundCheckbutton = ui.get_object("wrapAroundCheckbutton")
		self.followCurrentDocCheckbutton = ui.get_object("followCurrentDocCheckbutton")
		self.includeSubfolderCheckbutton = ui.get_object("includeSubfolderCheckbutton")
		self.regexSearchCheckbutton = ui.get_object("regexSearchCheckbutton")
		
		self.optionsExpander = ui.get_object("optionsExpander")
		self.optionsExpander.set_expanded(self._instance.find_dlg_setting['OPTIONS_EXPANDED'])

		self.forwardRadiobutton = ui.get_object("forwardRadiobutton")
		self.backwardRadiobutton = ui.get_object("backwardRadiobutton")
		if self._instance.forwardFlg == True:
			self.forwardRadiobutton.set_active(True)
		else:
			self.backwardRadiobutton.set_active(True)

		self.currentFileRadiobutton = ui.get_object("currentFileRadiobutton")
		self.allFilesRadiobutton = ui.get_object("allFilesRadiobutton")
		self.allFilesInPathRadiobutton = ui.get_object("allFilesInPathRadiobutton")
		self.currentSelectionRadiobutton = ui.get_object("currentSelectionRadiobutton")
		if self._instance.scopeFlg == 0:
			self.currentFileRadiobutton.set_active(True)
		elif self._instance.scopeFlg == 1:
			self.allFilesRadiobutton.set_active(True)
		elif self._instance.scopeFlg == 2:
			self.allFilesInPathRadiobutton.set_active(True)
		elif self._instance.scopeFlg == 3:
			self.currentSelectionRadiobutton.set_active(True)

		self.findButton = ui.get_object("findButton")
		self.replaceButton = ui.get_object("replaceButton")
		self.findAllButton = ui.get_object("findAllButton")
		self.replaceAllButton = ui.get_object("replaceAllButton")
		self.closeButton = ui.get_object("closeButton")
		self.selectPathButton = ui.get_object("selectPathButton")

		self.findDialog.show()

		self.matchWholeWordCheckbutton.set_active(self._instance.find_options['MATCH_WHOLE_WORD'])
		self.matchCaseCheckbutton.set_active(self._instance.find_options['MATCH_CASE'])
		self.wrapAroundCheckbutton.set_active(self._instance.find_options['WRAP_AROUND'])
		self.followCurrentDocCheckbutton.set_active(self._instance.find_options['FOLLOW_CURRENT_DOC'])
		self.includeSubfolderCheckbutton.set_active(self._instance.find_options['INCLUDE_SUBFOLDER'])
		self.regexSearchCheckbutton.set_active(self._instance.find_options['REGEX_SEARCH'])
		
		self.opacityScale = ui.get_object("opacityScale")
		self.opacityScale.set_value(float(self._instance.find_dlg_setting['OPACITY']))
		self.opacityScale.set_fill_level(float(self._instance.find_dlg_setting['OPACITY']))

	def on_findDialog_destroy_action(self, object):
		try:
			self._instance.find_dlg_setting['PATH_EXPANDED'] = self.pathExpander.get_expanded()
			self._instance.find_dlg_setting['OPTIONS_EXPANDED'] = self.optionsExpander.get_expanded()
			self._instance.find_dlg_setting['OPACITY'] = self.opacityScale.get_value()
			self._instance.find_ui = None
		except:
			pass
			
	def on_findDialog_show_action(self,object):
		if self.followCurrentDocCheckbutton.get_active() == True:
			self.pathComboboxtext.get_child().set_text(os.path.dirname(self._instance._window.get_active_document().get_uri_for_display()))
		else:
			filebrowser_root = self.get_filebrowser_root()
			if filebrowser_root != None and self._instance.find_options['ROOT_FOLLOW_FILEBROWSER'] == True:
				self.pathComboboxtext.get_child().set_text(filebrowser_root)
			else:
				self.pathComboboxtext.get_child().set_text(self.selectPathFilechooserdialog.get_filename())
				
	def findEntryIconPress(self, object, icon_pos, event):
		if icon_pos == 1:	#secondary icon
			#self.findTextComboboxtext.get_model().clear()
			for history_pos in range(0, len(self._instance.find_history)):
				self.findTextComboboxtext.remove(0)
			self._instance.find_history = []
		elif icon_pos == 0:	#primary icon
			text = object.get_text()
			if not text:
				return
			if text not in self._instance.find_bookmarks:
				self.findTextComboboxtext.append_text(text)
				self._instance.find_bookmarks.append(text)
				self.set_bookmark_icon(object, True)
			else:
				idx = self._instance.find_bookmarks.index(text)
				self._instance.find_bookmarks.remove(text)
				self.findTextComboboxtext.remove(idx + len(self._instance.find_history) + 1)
				self.set_bookmark_icon(object, False)
		
	def replaceEntryIconPress(self, object, icon_pos, event):
		if icon_pos == 1:	#secondary icon
			#self.replaceTextComboboxtext.get_model().clear()
			for history_pos in range(0, len(self._instance.replace_history)):
				self.replaceTextComboboxtext.remove(0)
			self._instance.replace_history = []
		elif icon_pos == 0:	#primary icon
			text = object.get_text()
			if not text:
				return
			if text not in self._instance.replace_bookmarks:
				self.replaceTextComboboxtext.append_text(text)
				self._instance.replace_bookmarks.append(text)
				self.set_bookmark_icon(object, True)
			else:
				idx = self._instance.replace_bookmarks.index(text)
				self._instance.replace_bookmarks.remove(text)
				self.replaceTextComboboxtext.remove(idx + len(self._instance.replace_history) + 1)
				self.set_bookmark_icon(object, False)
		
	def filterEntryIconPress(self, object, icon_pos, event):
		if icon_pos == 1:	#secondary icon
			#self.filterComboboxtext.get_model().clear()
			for history_pos in range(0, len(self._instance.filter_history)):
				self.filterComboboxtext.remove(0)
			self._instance.filter_history = []
		elif icon_pos == 0:	#primary icon
			text = object.get_text()
			if not text:
				return
			if text not in self._instance.filter_bookmarks:
				self.filterComboboxtext.append_text(text)
				self._instance.filter_bookmarks.append(text)
				self.set_bookmark_icon(object, True)
			else:
				idx = self._instance.filter_bookmarks.index(text)
				self._instance.filter_bookmarks.remove(text)
				self.filterComboboxtext.remove(idx + len(self._instance.filter_history) + 1)
				self.set_bookmark_icon(object, False)
		
	def pathEntryIconPress(self, object, icon_pos, event):
		if icon_pos == 1:	#secondary icon
			#self.pathComboboxtext.get_model().clear()
			for history_pos in range(0, len(self._instance.path_history)):
				self.pathComboboxtext.remove(0)
			self._instance.path_history = []
		elif icon_pos == 0:	#primary icon
			text = object.get_text()
			if not text:
				return
			if text not in self._instance.path_bookmarks:
				self.pathComboboxtext.append_text(text)
				self._instance.path_bookmarks.append(text)
				self.set_bookmark_icon(object, True)
			else:
				idx = self._instance.path_bookmarks.index(text)
				self._instance.path_bookmarks.remove(text)
				self.pathComboboxtext.remove(idx + len(self._instance.path_history) + 1)
				self.set_bookmark_icon(object, False)
				
	def findTextComboboxtext_changed(self, object):
		entry = object.get_child()
		if object.get_active_text() in self._instance.find_bookmarks:
			self.set_bookmark_icon(entry, True)
		else:
			self.set_bookmark_icon(entry, False)

	def replaceTextComboboxtext_changed(self, object):
		entry = object.get_child()
		if object.get_active_text() in self._instance.replace_bookmarks:
			self.set_bookmark_icon(entry, True)
		else:
			self.set_bookmark_icon(entry, False)

	def filterComboboxtext_changed(self, object):
		entry = object.get_child()
		if object.get_active_text() in self._instance.filter_bookmarks:
			self.set_bookmark_icon(entry, True)
		else:
			self.set_bookmark_icon(entry, False)

	def pathComboboxtext_changed(self, object):
		entry = object.get_child()
		if object.get_active_text() in self._instance.path_bookmarks:
			self.set_bookmark_icon(entry, True)
		else:
			self.set_bookmark_icon(entry, False)
			
	def on_findDialog_focus_in_event_action(self, object, event):
		object.set_opacity(1)
		if self.followCurrentDocCheckbutton.get_active() == True:
			self.pathComboboxtext.get_child().set_text(os.path.dirname(self._instance._window.get_active_document().get_uri_for_display()))
		'''	
		else:
			filebrowser_root = self.get_filebrowser_root()
			if filebrowser_root != None and self._instance.find_options['ROOT_FOLLOW_FILEBROWSER'] == True:
				self.pathComboboxtext.get_child().set_text(filebrowser_root)
			else:
				self.pathComboboxtext.get_child().set_text(self.selectPathFilechooserdialog.get_filename())
		#'''

	def on_findDialog_focus_out_event_action(self, object, event):
		object.set_opacity(self.opacityScale.get_value()/100)
	
	'''	
	def esc_accel_action(self, accelgroup, window, key, modifier):
		window.hide()
	#'''
		
	def return_accel_action(self, accelgroup, window, key, modifier):
		#self.on_findButton_clicked_action(None)
		self.on_findAllButton_clicked_action(None)
		
	def main(self):
		Gtk.main()

	def do_events(self):
		while Gtk.events_pending():
			Gtk.main_iteration()
			
	def add_combobox_list(self):
		find_text = self.findTextComboboxtext.get_active_text()
		replace_text = self.replaceTextComboboxtext.get_active_text()
		file_pattern = self.filterComboboxtext.get_active_text()
		path = self.pathComboboxtext.get_active_text()
		self._instance.current_search_pattern = find_text
		self._instance.current_replace_text = replace_text
		self._instance.current_file_pattern = file_pattern
		#self._instance.current_path = path
		
		if find_text != "" and find_text not in self._instance.find_history:
			#if len(self.findTextComboboxtext.get_model()) == 10:
			if len(self._instance.find_history) == 10:
				self._instance.find_history[0:1] = []
				self.findTextComboboxtext.remove(9)
			self._instance.find_history.append(find_text)
			self.findTextComboboxtext.prepend_text(find_text)
			
		if replace_text != "" and replace_text not in self._instance.replace_history:
			#if len(self.replaceTextComboboxtext.get_model()) == 10:
			if len(self._instance.replace_history) == 10:
				self._instance.replace_history[0:1] = []
				self.replaceTextComboboxtext.remove(9)
			self._instance.replace_history.append(replace_text)
			self.replaceTextComboboxtext.prepend_text(replace_text)
			
		if self._instance.scopeFlg == 2: #files in directory
			if file_pattern != "" and file_pattern not in self._instance.filter_history:
				#if len(self.filterComboboxtext.get_model()) == 10:
				if len(self._instance.filter_history) == 10:
					self._instance.filter_history[0:1] = []
					self.filterComboboxtext.remove(9)
				self._instance.filter_history.append(file_pattern)
				self.filterComboboxtext.prepend_text(file_pattern)
			
			if path != "" and path not in self._instance.path_history:
				#if len(self.pathComboboxtext.get_model()) == 10:
				if len(self._instance.path_history) == 10:
					self._instance.path_history[0:1] = []
					self.pathComboboxtext.remove(9)
				self._instance.path_history.append(path)
				self.pathComboboxtext.prepend_text(path)

	# button actions       
	def on_findButton_clicked_action(self, object):
		doc = self._instance._window.get_active_document()
		if not doc:
			return
		
		search_pattern = self.findTextComboboxtext.get_active_text()
		if search_pattern == "":
			return
		
		self.add_combobox_list()
		self._instance.advanced_find_in_doc(doc, search_pattern, self._instance.find_options, self._instance.forwardFlg)
		
	def on_replaceButton_clicked_action(self, object):
		doc = self._instance._window.get_active_document()
		if not doc:
			return
			
		search_pattern = self.findTextComboboxtext.get_active_text()
		if search_pattern == "":
			return
		
		self.add_combobox_list()
		self._instance.advanced_find_in_doc(doc, search_pattern, self._instance.find_options, self._instance.forwardFlg, True)

	def on_findAllButton_clicked_action(self, object):
		search_pattern = self.findTextComboboxtext.get_active_text()
		if search_pattern == "":
			return
		doc = self._instance._window.get_active_document()
		if not doc:
			return
			
		self._instance.set_bottom_panel_label(_('Finding...'), os.path.join(os.path.dirname(__file__), 'loading.gif'))
		#self._instance._results_view.set_sensitive(False)
		self._instance._results_view.is_busy(True)
		self._instance.show_bottom_panel()
		self.findDialog.hide()
		self.do_events()
			
		self.add_combobox_list()
		
		it = self._instance._results_view.append_find_pattern(search_pattern)
		
		if self._instance.scopeFlg == 0: #current document
			self._instance.advanced_find_all_in_doc(it, doc, search_pattern, self._instance.find_options)
			self._instance._results_view.show_find_result()
		elif self._instance.scopeFlg == 1: #all opened documents
			docs = self._instance._window.get_documents()			
			for doc in docs:
				self._instance.advanced_find_all_in_doc(it, doc, search_pattern, self._instance.find_options)
				self.do_events()
				if self._instance._results_view.stopButton.get_sensitive() == False:
					break
			self._instance._results_view.show_find_result()
		elif self._instance.scopeFlg == 2: #files in directory
			dir_path = self.pathComboboxtext.get_active_text()
			file_pattern = self.filterComboboxtext.get_active_text()
			self._instance.find_all_in_dir(it, dir_path, file_pattern, search_pattern, self._instance.find_options)
			self._instance._results_view.show_find_result()
		elif self._instance.scopeFlg == 3: #current selected text
			self._instance.advanced_find_all_in_doc(it, doc, search_pattern, self._instance.find_options, False, True)
			self._instance._results_view.show_find_result()

		self._instance.set_bottom_panel_label()
		#self._instance._results_view.set_sensitive(True)
		self._instance._results_view.is_busy(False)
		#self.do_events()
		#self.findDialog.destroy()

	def on_replaceAllButton_clicked_action(self, object):
		search_pattern = self.findTextComboboxtext.get_active_text()
		if search_pattern == "":
			return
		doc = self._instance._window.get_active_document()
		if not doc:
			return
			
		self._instance.set_bottom_panel_label(_('Replacing...'), os.path.join(os.path.dirname(__file__), 'loading.gif'))
		#self._instance._results_view.set_sensitive(False)
		self._instance._results_view.is_busy(True)
		self._instance.show_bottom_panel()
		self.findDialog.hide()
		self.do_events()
		
		self.add_combobox_list()

		it = self._instance._results_view.append_find_pattern(search_pattern, True, self.replaceTextComboboxtext.get_child().get_text())
		
		if self._instance.scopeFlg == 0: #current document
			self._instance.advanced_find_all_in_doc(it, doc, search_pattern, self._instance.find_options, True)
			self._instance._results_view.show_find_result()
		elif self._instance.scopeFlg == 1: #all opened documents
			docs = self._instance._window.get_documents()
			for doc in docs:
				self._instance.advanced_find_all_in_doc(it, doc, search_pattern, self._instance.find_options, True)
				self.do_events()
				if self._instance._results_view.stopButton.get_sensitive() == False:
					break
			self._instance._results_view.show_find_result()
		elif self._instance.scopeFlg == 2: #files in directory
			path = str(self._instance._results_view.findResultTreemodel.iter_n_children(None) - 1)
			it = self._instance._results_view.findResultTreemodel.get_iter(path)
			self._instance._results_view.show_find_result()
			self._instance._results_view.findResultTreemodel.set_value(it, 2, _("Replace in this scope is not supported."))
		elif self._instance.scopeFlg == 3: #current selected text
			self._instance.advanced_find_all_in_doc(it, doc, search_pattern, self._instance.find_options, True, True)
			self._instance._results_view.show_find_result()
		
		self._instance.set_bottom_panel_label()
		#self._instance._results_view.set_sensitive(True)
		self._instance._results_view.is_busy(False)
		#self.do_events()
		#self.findDialog.destroy()

	def on_closeButton_clicked_action(self, object):
		self.findDialog.destroy()
		
	def on_selectPathButton_clicked_action(self, object):
		self.selectPathFilechooserdialog.show()

	# select path file chooserr dialog actions
	def on_selectPathDialogOkButton_clicked_action(self, object):
		if self.followCurrentDocCheckbutton.get_active() == True:
			self.followCurrentDocCheckbutton.set_active(False)
		folder_path = self.selectPathFilechooserdialog.get_filename()
		self.selectPathFilechooserdialog.select_filename(folder_path)
		self.pathComboboxtext.get_child().set_text(folder_path)
		self.add_combobox_list()
		self.selectPathFilechooserdialog.hide()
		
	def on_selectPathDialogCancelButton_clicked_action(self, object):
		self.selectPathFilechooserdialog.hide()
		
	# find_options    
	def on_matchWholeWordCheckbutton_toggled_action(self, object):
		self._instance.find_options['MATCH_WHOLE_WORD'] = object.get_active()

	def on_matchCaseCheckbutton_toggled_action(self, object):
		self._instance.find_options['MATCH_CASE'] = object.get_active()

	def on_wrapAroundCheckbutton_toggled_action(self, object):
		self._instance.find_options['WRAP_AROUND'] = object.get_active()
		
	def on_followCurrentDocCheckbutton_toggled_action(self, object):
		self._instance.find_options['FOLLOW_CURRENT_DOC'] = object.get_active()
		if object.get_active() == True:
			self.pathComboboxtext.get_child().set_text(os.path.dirname(self._instance._window.get_active_document().get_uri_for_display()))
		else:
			filebrowser_root = self.get_filebrowser_root()
			if filebrowser_root != None and self._instance.find_options['ROOT_FOLLOW_FILEBROWSER'] == True:
				self.pathComboboxtext.get_child().set_text(filebrowser_root)
			else:
				self.pathComboboxtext.get_child().set_text(self.selectPathFilechooserdialog.get_filename())
			
	def on_includeSubfolderCheckbutton_toggled_action(self, object):
		self._instance.find_options['INCLUDE_SUBFOLDER'] = object.get_active()
		
	def on_regexSearchCheckbutton_toggled_action(self, object):
		self._instance.find_options['REGEX_SEARCH'] = object.get_active()
		
	def on_opacityScale_vlaue_changed_action(self, object):
		object.set_fill_level(object.get_value())

	# radiobutton
	def directionRadiobuttonGroup_action(self, object):
		self._instance.forwardFlg = self.forwardRadiobutton.get_active()

	def scopeRadiobuttonGroup_action(self, object):
		if self.currentFileRadiobutton.get_active() == True:
			self._instance.scopeFlg = 0
		elif self.allFilesRadiobutton.get_active() == True:
			self._instance.scopeFlg = 1
		elif self.allFilesInPathRadiobutton.get_active() == True:
			self._instance.scopeFlg = 2
		elif self.currentSelectionRadiobutton.get_active() == True:
			self._instance.scopeFlg = 3
		
		if self._instance.scopeFlg == 2:
			self.pathExpander.set_sensitive(True)
		else:
			self.pathExpander.set_sensitive(False)
			
	def set_bookmark_icon(self, entry, flg=False):
		image = Gtk.Image()
		if flg:
			image.set_from_file(os.path.join(os.path.dirname(__file__), 'star_y.png'))
		else:
			image.set_from_file(os.path.join(os.path.dirname(__file__), 'star_w.png'))	
		entry.set_icon_from_pixbuf(0, image.get_pixbuf())

	# filebrowser integration
	def get_filebrowser_root(self):
		base_key = 'org.gnome.gedit.plugins.filebrowser'
		setting = Gio.Settings.new(base_key)
		root_str = setting.get_string('virtual-root')
		#print(root_str)
		if not root_str:
			return None
		'''
		path = Gio.Vfs.get_default().get_file_for_uri(root_str).get_path()
		print(path + '#')
		return path
		#'''
		#'''
		if root_str.startswith('file://'):
			return root_str[7:]
		else:
			return None
		#'''
		
		
		'''
		base = u'/apps/gedit-2/plugins/filebrowser/on_load'
		client = gconf.client_get_default()
		client.add_dir(base, gconf.CLIENT_PRELOAD_NONE)
		path = os.path.join(base, u'virtual_root')
		val = client.get(path)
		if val != None:
			path_string = val.get_string()
			idx = path_string.find('://') + 3
			return val.get_string()[idx:]
		return None
		#'''
	


if __name__ == "__main__":
	app = AdvancedFindUI(None)
	app.main()


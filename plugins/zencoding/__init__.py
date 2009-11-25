# completion.py
#
# Copyright (C) 2009 - Stuart Langridge
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# http://code.google.com/p/zen-coding
#
# Heavily based on Guillaume Chazarain's completion.py


import gedit, gobject, gtk, re
import zen_core

class ZenCodingPlugin(gedit.Plugin):
	"A gedit plugin to implement Zen Coding"

	def __init__(self):
		gedit.Plugin.__init__(self)

	def activate(self, window):
		"gedit callback: install the completion entry point"
		ui_manager = window.get_ui_manager()
		action_group = gtk.ActionGroup("GeditZenCodingPluginActions")
		complete_action = gtk.Action(name="ZenCodingAction", 
		                             label="Expand Zen code...",
		                             tooltip="Expand Zen Code in document to HTML",
		                             stock_id=gtk.STOCK_GO_FORWARD)
		complete_action.connect("activate",
		                        lambda a: self.expand_zencode_cb(window))
		action_group.add_action_with_accel(complete_action,
		                                   "<Ctrl>E")
		ui_manager.insert_action_group(action_group, 0)
		ui_merge_id = ui_manager.new_merge_id()
		ui_manager.add_ui(ui_merge_id,
		                  "/MenuBar/EditMenu/EditOps_5",
		                  "ZenCoding",
		                  "ZenCodingAction",
		                  gtk.UI_MANAGER_MENUITEM, False)
		ui_manager.__ui_data__ = (action_group, ui_merge_id)

	def deactivate(self, window):
		"gedit callback: get rid of the completion feature"
		ui_manager = window.get_ui_manager()
		(action_group, ui_merge_id) = ui_manager.__ui_data__
		del ui_manager.__ui_data__
		ui_manager.remove_action_group(action_group)
		ui_manager.remove_ui(ui_merge_id)


	def expand_zencode_cb(self, window):
		"The entry point to the word completion"
		view = window.get_active_view()
		
		buffer = view.get_buffer()
		cursor_iter = buffer.get_iter_at_mark(buffer.get_insert())
		line_iter = cursor_iter.copy()
		line_iter.set_line_offset(0)
		# The text from the start of the line to the cursor
		line = buffer.get_text(line_iter, cursor_iter)
		# Find the last space in the line
		words = line.split(" ")
		before = words[-1]
		if not before: return
		
		tree = zen_core.parse_into_tree(before)
		if not tree: return
		after = tree.to_string(True)
		
		# We are currently lame and do not know how to do placeholders.
		# So remove all | characters from after.
		after = after.replace("|", "")
		
		# replace last_word with after
		buffer = view.get_buffer()
		cursor_iter = buffer.get_iter_at_mark(buffer.get_insert())
		word_iter = cursor_iter.copy()
		position_in_line = cursor_iter.get_line_index() - len(before)
		word_iter.set_line_index(position_in_line)
		buffer.delete(word_iter, cursor_iter)
		buffer.insert_at_cursor(after)
		

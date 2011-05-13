# -*- coding: utf-8 -*-
#  A Diolog that contains the last opened documents
# 
#  Copyright (C) 2008 Marco Laspe <macco@gmx.net>
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


# IMPROVE highlight first entry
import gedit, gtk
#from gettext import gettext as _

# Menu item example, insert a new item in the Tools menu
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menuitem name="Lastdocs" action="Lastdocs"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class LastdocsPluginInstance:
  def __init__(self, plugin, window):
    self._window = window
    self._plugin = plugin
    # Insert menu items
    self._insert_menu()
    # get recent_manager
    self.load_recent_manager()
    self.create_dialog()
    # Recent Limit
    self.__recent_limit = 9 #IMPROVE set __recent_limit via configuration dialog

  def stop(self):
    # Remove any installed menu items
    self._remove_menu()

    self._window = None
    self._plugin = None
    self._action_group = None

  def _insert_menu(self):
    # Get the GtkUIManager
    manager = self._window.get_ui_manager()

    # Create a new action group
    self._action_group = gtk.ActionGroup("LastdocsPluginActions")
    self._action_group.add_actions([("Lastdocs", None, _("Lastdocs"), "<Ctrl><Shift>o", _("Example menu item"), lambda a: self.on_example_menu_item_activate())])
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

  def update(self):
    pass
    # Called whenever the window has been updated (active tab
    # changed, etc.)


  # Menu activate handlers
  def on_example_menu_item_activate(self):
    self.dialog.show_all()
    self.dialog.grab_focus()
    
    #uris = dialog.get_uris()
    #dialog.select_uri(uris[0])
    #info2.grab_focus()
        
    if self.dialog.run() == gtk.RESPONSE_ACCEPT:
      info = self.dialog.get_current_item()      
      print info.get_uri()
      self._open_file(info.get_uri())
      #gedit.document.load(info.get_uri(), None, 1, False)
    self.dialog.hide()
    return
    
  def _sort_recent(self):
    pass
  
  def load_recent_manager(self):
    self.recent_manager = gtk.recent_manager_get_default()

  def create_dialog(self):
    self.dialog = gtk.RecentChooserDialog("Recent Documents", self._window, self.recent_manager,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
    #dialog.set_sort_func(_sort_recent(),None)
    self.dialog.set_sort_type(gtk.RECENT_SORT_MRU)
    self.dialog.set_filter(self.__create_filter())
    #dialog.set_limit(self.__recent_limit)
    self.dialog.set_local_only(False)    
    #dialog.set_select_multiple(False)
    self.dialog.set_show_not_found(False)
    self.dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    
  def __create_filter(self):
		"""
		Create a filter for the recent menu.

		@param self: Reference to the RecentMenu instance.
		@type self: A RecentMenu object.

		@return: A filter for the recent menu.
		@rtype: A gtk.RecentFilter object.
		"""
		recent_filter = gtk.RecentFilter()
		recent_filter.add_application("gedit")
		return recent_filter    
  #opens (or switches to) the given file
  
  def _open_file( self, filename ):
    #uri = self._rootdir + "/" + filename
    uri = filename
    tab = self._window.get_tab_from_uri(uri) 
    if tab == None:
      tab = self._window.create_tab_from_uri( uri,gedit.encoding_get_current(), 0, False, False )
    self._window.set_active_tab( tab )

class LastdocsPlugin(gedit.Plugin):
  DATA_TAG = "LastdocsPluginInstance"

  def __init__(self):
    gedit.Plugin.__init__(self)

  def _get_instance(self, window):
    return window.get_data(self.DATA_TAG)

  def _set_instance(self, window, instance):
    window.set_data(self.DATA_TAG, instance)

  def activate(self, window):
    self._set_instance(window, LastdocsPluginInstance(self, window))

  def deactivate(self, window):
    self._get_instance(window).stop()
    self._set_instance(window, None)

  def update_ui(self, window):
    self._get_instance(window).update()

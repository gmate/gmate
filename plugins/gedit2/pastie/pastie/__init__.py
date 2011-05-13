from gettext import gettext as _

import gtk, gtk.glade
import pygtk
pygtk.require('2.0')
import gedit
import os
import pastie
import windows

#pice of XML, it tells where to place our action
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
         <menuitem name="Pastie" action="Pastie"/>
         <menuitem name="PastieDefault" action="PastieDefault" />
      </placeholder>
    </menu>
  </menubar>
</ui>
"""


#WINDOW HEPER
class PastieWindowHelper:

    #ACTIONS

    def __init__(self, plugin, window):
        self._window = window
        self._plugin = plugin
        self.pastie_window = windows.PastieWindow()
        self.pastie_window.get_text = self.get_selected_text
        self._insert_menu() #insert menu item


    def deactivate(self):
        self._remove_menu() #remove installed menu items
        self._window = None
        self._plugin = None

    def update_ui(self):
        #called whenever this window has been updated (active, change, etc)
        self._action_group.set_sensitive(self._window.get_active_document() != None)

    #MENU INSERTION

    def _insert_menu(self):
        manager = self._window.get_ui_manager() #get the GtkUIManager
        self._action_group = gtk.ActionGroup("PastieActions") #new group
        #menu position (from ui_str) and ctrl + shift + d shourtcut fo pastie action
        self._action_group.add_actions([("Pastie", None, _("Pastie selection"),
                                         '<Control><Shift>v', _("Pastie selection"),
                                         self.pastie_window.show)])
        self._action_group.add_actions([("PastieDefault", None, _("Pastie with defaults"),
                                         '<Control><Shift>x', _("Pastie with defaults"),
                                         self.pastie_window.paste_defaults)])
        manager.insert_action_group(self._action_group, -1)
        self._ui_id = manager.add_ui_from_string(ui_str)

    def _remove_menu(self):
        "removes elements form menu which plugin adds"
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id) #_ui_id is stored id of added menu
        manager.remove_action_group(self._action_group) #removes action group
        manager.ensure_update()


    #METHODS

    def get_selected_text(self):
        "gets selected text form current document and returns it"
        doc = self._window.get_active_document()

        if not doc:
            return None
        if doc.get_has_selection():
            start, end = doc.get_selection_bounds()
        else:
            return None

        return doc.get_text(start,end)



#PLUGIN
class PastiePlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)

    def activate(self, window):
        self._instances = PastieWindowHelper(self, window)

    def deactivate(self, window):
        self._instances.deactivate()
        del self._instances

    def update_ui(self, window):
        self._instances.update_ui()

    def is_configurable(self):
        return True

    def create_configure_dialog(self):
        return self._instances.pastie_window.config.window.window


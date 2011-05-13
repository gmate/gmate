import gtk
from FindInProjectWindow import FindInProjectWindow

ui_str="""<ui>
<menubar name="MenuBar">
  <menu name="SearchMenu" action="Search">
    <placeholder name="SearchOps_0">
      <menuitem name="FindInProject" action="FindInProject"/>
    </placeholder>
  </menu>
</menubar>
</ui>
"""
class FindInProjectPluginInstance:
    def __init__(self, window):
        self._window = window
        self._search_window = FindInProjectWindow(self._window)
        self.add_menu()

    def deactivate(self):
        self.window = None
        self.plugin = None
        self.remove_menu()

    def add_menu(self):
        self._action_group = gtk.ActionGroup("FindInProjectActions")
        self._action_group.add_actions([('FindInProject', gtk.STOCK_EDIT, 'Find in project...', '<Ctrl><Shift>f', 'Search in the project', self.show_window)])
        self.manager = self._window.get_ui_manager()
        self.manager.insert_action_group(self._action_group, -1)
        self._ui_id = self.manager.add_ui_from_string(ui_str)

    def remove_menu(self):
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()

    def show_window(self, window):
        self._search_window.init()


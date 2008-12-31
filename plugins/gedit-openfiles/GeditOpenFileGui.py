import gtk
import os
from Logger import log
import gedit
import urllib

menu_str="""
<ui>
    <menubar name="MenuBar">
        <menu name="FileMenu" action="File">
            <placeholder name="FileOps_1">
                <menuitem name="Open File" action="GeditOpenFileMenuAction"/>
           </placeholder>
        </menu>
    </menubar>
</ui>
"""


class GeditOpenFileGui(object):

    def __init__(self, plugin, window, file_monitor, config):
        self._plugin = plugin
        self._window = window
        self._file_monitor = file_monitor
        self._config = config

        # Get Builder and get xml file
        self._builder = gtk.Builder()
        self._builder.add_from_file(os.path.join(os.path.dirname(__file__),
             "gui", "geditopenfiles_gtk.xml"))

        #setup window
        self._plugin_window = self._builder.get_object("gedit_openfiles_window")
        self._plugin_window.set_transient_for(self._window)
        self._notebook = self._builder.get_object('notebook')

        # Callbacks
        self._plugin_window.connect("key-release-event", self._on_window_release)
        self._plugin_window.connect("delete_event", self._plugin_window_delete_event)

        #setup buttons
        self._builder.get_object("open_button").connect("clicked",
            self._open_selected_item)
        self._builder.get_object("cancel_button").connect("clicked",
            lambda a: self._plugin_window.hide())

        # Setup entry field
        self._file_query = self._builder.get_object("file_query")
        self._file_query.connect("key-release-event", self._on_query_entry)

        # Get File TreeView
        self._file_list = self._builder.get_object("file_list")

        # Connect Action on TreeView
        self._file_list.connect("select-cursor-row", self._on_select_from_list)
        self._file_list.connect("button_press_event", self._on_list_mouse)

        # Setup File TreeView
        self._liststore = gtk.ListStore(str, str)
        self._file_list.set_model(self._liststore)

        # Path Column
        column1 = gtk.TreeViewColumn("Path", gtk.CellRendererText(), markup=0)
        column1.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)

        self._file_list.append_column(column1)
        self._file_list.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        # Add Animation icon for building data
        building_data_spinner = self._builder.get_object('spinner')
        building_data_spinner.set_from_animation(gtk.gdk.PixbufAnimation(
            os.path.join(os.path.dirname(__file__), "gui", "progress.gif")))
        self._building_data_spinner_box = self._builder.get_object('spinner_box')

        # Setup Configuration Tab
        self._notebook = self._builder.get_object("notebook")
        self._file_browser_checkbox = self._builder.get_object("file_browser_checkbox")
        self._file_browser_checkbox.connect("toggled", self._file_browser_checkbox_event)
        self._open_root_hbox = self._builder.get_object("open_root_hbox")

        # Setup Callback for root path
        self._open_root_path = self._builder.get_object("open_root_path")
        self._open_root_path.set_current_folder(self._config.get_value("ROOT_PATH"))

        self._config_ignore_input = self._builder.get_object("config_ignore_input")

        self._reset_config()

        # Connect the OK Button the config tab
        self._builder.get_object("config_save_button").connect("clicked", self._save_config_event)
        self._builder.get_object("config_cancel_button").connect("clicked", self._cancel_config_event)
        self._builder.get_object("config_refresh_button").connect("clicked", self._refresh_data)

        use_file_browser = self._config.get_value("USE_FILEBROWSER")
        if use_file_browser == True or use_file_browser == None: # Defualt
            self._open_root_hbox.set_sensitive(False)
        else:
            self._open_root_hbox.set_sensitive(True)

        # Set encoding
        self._encoding = gedit.encoding_get_current()
        self._insert_menu()

    def _refresh_data(self, event):
        self._file_monitor.refresh_database()
        self._plugin_window.hide()

    def _reset_config(self):
        if self._config.get_value("USE_FILEBROWSER"):
            self._file_browser_checkbox.set_active(True)
        else:
            self._file_browser_checkbox.set_active(False)
        log.debug("[GeditOpenFileGui] IGNORE_FILE_FILETYPES = " + str(self._config.get_value("IGNORE_FILE_FILETYPES")))
        self._config_ignore_input.set_text(", ".join(self._config.get_value("IGNORE_FILE_FILETYPES")))

    def _cancel_config_event(self, event):
        self._reset_config()
        self._plugin_window.hide()

    def _save_config_event(self, event):
        self._config.set_value("USE_FILEBROWSER", self._file_browser_checkbox.get_active())
        log.debug("[GeditOpenFileGui] : ROOT_PATH = %s" % self._open_root_path.get_current_folder())
        self._config.set_value("ROOT_PATH", self._open_root_path.get_current_folder())

        ignored_list = [s.strip() for s in self._config_ignore_input.get_text().split(",")]
        log.debug("[GeditOpenFileGui] ignored_list = " + str(ignored_list))
        self._config.set_value("IGNORE_FILE_FILETYPES", ignored_list)
        self._file_monitor.set_root_path(self._config.root_path())
        self._file_monitor.refresh_database()
        self._plugin_window.hide()

    def _file_browser_checkbox_event(self, widget):
        if widget.get_active():
            self._open_root_hbox.set_sensitive(False)
        else:
            self._open_root_hbox.set_sensitive(True)

    def _plugin_window_delete_event(self, window, event):
        """
        Method used to is trigger when the x is click on the window, it will not
        destroy the window only hide it.
        """
        self._plugin_window.hide()
        return True

    def update_ui(self):
        #log.error("[GeditOpenFileGui] update_ui METHOD NOT IMPLEMENTED")
        pass

    def _insert_menu(self):
        #TODO refactor and reivew code. To make sure its not doing more work then is needed.
        manager = self._window.get_ui_manager()
        self._action_group = gtk.ActionGroup("GeditOpenFileAction")
        plugin_menu_action = gtk.Action(name="GeditOpenFileAction",
            label="Open", tooltip="Gedit Open File(s) tools", stock_id=None)
        self._action_group.add_action(plugin_menu_action)

        geditopenfiles_action = gtk.Action(name="GeditOpenFileMenuAction",
            label="Open File(s)...\t", tooltip="Open a file(s)",
            stock_id=gtk.STOCK_OPEN)
        geditopenfiles_action.connect("activate",
            lambda a: self._on_geditopen_action())
        self._action_group.add_action_with_accel(geditopenfiles_action,
            "<Ctrl><Alt>o")
        manager.insert_action_group(self._action_group, 0)

        self._ui_id = manager.new_merge_id()

        manager.add_ui_from_string(menu_str)
        manager.ensure_update()

    def _on_window_release(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self._plugin_window.hide()

    def _on_query_entry(self, widget, event):
        # Check to see if key pressed is Return if so open first file
        if event.keyval == gtk.keysyms.Return:
            self._on_select_from_list(None, event)
            return

        self._clear_treeveiw() # Remove all

        input_query = widget.get_text()
        log.debug("[GeditOpenFileGui] input_query : %s" % input_query)

        if input_query:
            # Query database based on input
            results = self._file_monitor.search_for_files(input_query)
            self._insert_into_treeview(results)

            # Select the first one on the list
            iter = self._liststore.get_iter_first()
            if iter != None:
                self._file_list.get_selection().select_iter(iter)

    def _insert_into_treeview(self, file_list):
        for file in file_list:
            self._liststore.append([file.display_path, file.uri])

    def _clear_treeveiw(self):
        self._liststore.clear()

    def _open_file(self, uri):
        log.debug("[GeditOpenFileGui] uri to open : %s" % uri)
        # Check to make sure file is not allready opened
        tab = self._window.get_tab_from_uri(uri)
        if not tab:
            # if not createa tab.
            tab = self._window.create_tab_from_uri(uri, self._encoding, 0,
                False, False)
        self._window.set_active_tab(tab)

    def _foreach(self, model, path, iter, selected):
        """
        Populates selected list
        """
        selected.append(model.get_value(iter, 1))

    def _on_select_from_list(self, widget, event):
        # Populate the list of file paths
        selected = []
        self._file_list.get_selection().selected_foreach(self._foreach, selected)
        for selected_file in selected:
            # Open File
            self._open_file(selected_file)

        # Hide the window
        self._plugin_window.hide()

    def _on_list_mouse(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self._on_select_from_list(None, event)

    def _on_geditopen_action(self):
        self._plugin_window.show()
        self._notebook.set_current_page(0) # Set back to the search page
        self._file_query.grab_focus()
        self._file_monitor.change_root(self._config.root_path())
        self._reset_config()

    def _open_selected_item(self, event):
        self._on_select_from_list(None, event)

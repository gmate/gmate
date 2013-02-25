import os
import sys
import logging
import tempfile
import ctags
from gi.repository import GObject, GdkPixbuf, Gedit, Gtk, PeasGtk, Gio

logging.basicConfig()
LOG_LEVEL = logging.WARN
SETTINGS_SCHEMA = "org.gnome.gedit.plugins.sourcecodebrowser"
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
ICON_DIR = os.path.join(DATA_DIR, 'icons', '16x16')
 
class SourceTree(Gtk.VBox):
    """
    Source Tree Widget
    
    A treeview storing the heirarchy of source code symbols within a particular
    document. Requries exhuberant-ctags.
    """
    __gsignals__ = {
        "tag-activated": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
    }   
    
    def __init__(self):
        Gtk.VBox.__init__(self)
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.setLevel(LOG_LEVEL)
        self._pixbufs = {}
        self._current_uri = None
        self.expanded_rows = {}
        
        # preferences (should be set by plugin)
        self.show_line_numbers = True
        self.ctags_executable = 'ctags'
        self.expand_rows = True
        self.sort_list = True
        self.create_ui()
        self.show_all()
    
    def get_missing_pixbuf(self):
        """ Used for symbols that do not have a known image. """
        if not 'missing' in self._pixbufs:
            filename = os.path.join(ICON_DIR, "missing-image.png")
            self._pixbufs['missing'] = GdkPixbuf.Pixbuf.new_from_file(filename)
        
        return self._pixbufs['missing']
        
    def get_pixbuf(self, icon_name):
        """ 
        Get the pixbuf for a specific icon name fron an internal dictionary of
        pixbufs. If the icon is not already in the dictionary, it will be loaded
        from an external file.        
        """
        if icon_name not in self._pixbufs: 
            filename = os.path.join(ICON_DIR, icon_name + ".png")
            if os.path.exists(filename):
                try:
                    self._pixbufs[icon_name] = GdkPixbuf.Pixbuf.new_from_file(filename)
                except Exception as e:
                    self._log.warn("Could not load pixbuf for icon '%s': %s", 
                                   icon_name, 
                                   str(e))
                    self._pixbufs[icon_name] = self.get_missing_pixbuf()
            else:
                self._pixbufs[icon_name] = self.get_missing_pixbuf()
                                       
        return self._pixbufs[icon_name]

    def clear(self):
        """ Clear the tree view so that new data can be loaded. """
        if self.expand_rows: 
            self._save_expanded_rows()
        self._store.clear()
        
    def create_ui(self):
        """ Craete the main user interface and pack into box. """
        self._store = Gtk.TreeStore(GdkPixbuf.Pixbuf,       # icon
                                    GObject.TYPE_STRING,    # name
                                    GObject.TYPE_STRING,    # kind
                                    GObject.TYPE_STRING,    # uri 
                                    GObject.TYPE_STRING,    # line               
                                    GObject.TYPE_STRING)    # markup                           
        self._treeview = Gtk.TreeView.new_with_model(self._store)
        self._treeview.set_headers_visible(False)          
        column = Gtk.TreeViewColumn("Symbol")
        cell = Gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, 'pixbuf', 0)
        cell = Gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'markup', 5)
        self._treeview.append_column(column)
        
        self._treeview.connect("row-activated", self.on_row_activated)
        
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self._treeview)
        self.pack_start(sw, True, True, 0)
    
    def _get_tag_iter(self, tag, parent_iter=None):
        """
        Get the tree iter for the specified tag, or None if the tag cannot
        be found.
        """
        tag_iter = self._store.iter_children(parent_iter)
        while tag_iter:
            if self._store.get_value(tag_iter, 1) == tag.name:
                return tag_iter
            tag_iter = self._store.iter_next(tag_iter)
        
        return None
            
    def _get_kind_iter(self, kind, uri, parent_iter=None):
        """
        Get the iter for the specified kind. Creates a new node if the iter
        is not found under the specirfied parent_iter.
        """
        kind_iter = self._store.iter_children(parent_iter)
        while kind_iter:
            if self._store.get_value(kind_iter, 2) == kind.name:
                return kind_iter
            kind_iter = self._store.iter_next(kind_iter)
        
        # Kind node not found, so we'll create it.
        pixbuf = self.get_pixbuf(kind.icon_name())
        markup = "<i>%s</i>" % kind.group_name()
        kind_iter = self._store.append(parent_iter, (pixbuf, 
                                       kind.group_name(), 
                                       kind.name, 
                                       uri, 
                                       None, 
                                       markup))
        return kind_iter
        
    def load(self, kinds, tags, uri):
        """
        Load the tags into the treeview and restore the expanded rows if 
        applicable.
        """
        self._current_uri = uri
        # load root-level tags first
        for i, tag in enumerate(tags):
            if "class" not in tag.fields: 
                parent_iter = None
                pixbuf = self.get_pixbuf(tag.kind.icon_name())
                if 'line' in tag.fields and self.show_line_numbers:
                    markup = "%s [%s]" % (tag.name, tag.fields['line'])
                else:
                    markup = tag.name
                kind_iter = self._get_kind_iter(tag.kind, uri, parent_iter)
                new_iter = self._store.append(kind_iter, (pixbuf, 
                                                          tag.name, 
                                                          tag.kind.name, 
                                                          uri, 
                                                          tag.fields['line'], 
                                                          markup))
        # second level tags 
        for tag in tags:
            if "class" in tag.fields and "." not in tag.fields['class']:
                pixbuf = self.get_pixbuf(tag.kind.icon_name())
                if 'line' in tag.fields and self.show_line_numbers:
                    markup = "%s [%s]" % (tag.name, tag.fields['line'])
                else:
                    markup = tag.name
                for parent_tag in tags:
                    if parent_tag.name == tag.fields['class']:
                        break
                kind_iter = self._get_kind_iter(parent_tag.kind, uri, None)
                parent_iter = self._get_tag_iter(parent_tag, kind_iter)
                kind_iter = self._get_kind_iter(tag.kind, uri, parent_iter) # for sub-kind nodes
                new_iter = self._store.append(kind_iter, (pixbuf, 
                                                          tag.name, 
                                                          tag.kind.name, 
                                                          uri, 
                                                          tag.fields['line'], 
                                                          markup))
        # TODO: We need to go at least one more level to deal with the inline 
        # classes used in many python projects (eg. Models in Django)
        # Recursion would be even better.
        
        # sort         
        if self.sort_list:                               
            self._store.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        
        # expand
        if uri in self.expanded_rows:
            for strpath in self.expanded_rows[uri]:
                path = Gtk.TreePath.new_from_string(strpath)
                if path:
                    self._treeview.expand_row(path, False)
        elif uri not in self.expanded_rows and self.expand_rows:
            self._treeview.expand_all()
            """
            curiter = self._store.get_iter_first()
            while curiter:
                path = self._store.get_path(curiter)
                self._treeview.expand_row(path, False)
                curiter = self._store.iter_next(iter)
            """

    def on_row_activated(self, treeview, path, column, data=None):
        """
        If the row has uri and line number information, emits the tag-activated
        signal so that the editor can jump to the tag's location.
        """
        model = treeview.get_model()
        iter = model.get_iter(path)
        uri = model.get_value(iter, 3)
        line = model.get_value(iter, 4)
        if uri and line:
            self.emit("tag-activated", (uri, line))

    def parse_file(self, path, uri):
        """
        Parse symbols out of a file using exhuberant ctags. The path is the local
        filename to pass to ctags, and the uri is the actual URI as known by
        Gedit. They would be different for remote files.
        """
        command = "ctags -nu --fields=fiKlmnsSzt -f - '%s'" % path
        #self._log.debug(command)
        try:
            parser = ctags.Parser()
            parser.parse(command, self.ctags_executable)
        except Exception as e:
            self._log.warn("Could not execute ctags: %s (executable=%s)",
                           str(e), 
                           self.ctags_executable)
        self.load(parser.kinds, parser.tags, uri)
    
    
    def _save_expanded_rows(self):
        self.expanded_rows[self._current_uri] = []
        self._treeview.map_expanded_rows(self._save_expanded_rows_mapping_func, 
                                         self._current_uri)
    
    def _save_expanded_rows_mapping_func(self, treeview, path, uri):
        self.expanded_rows[uri].append(str(path))
        
        
class Config(object):
    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.setLevel(LOG_LEVEL)
        
    def get_widget(self, has_schema):
        filename = os.path.join(DATA_DIR, 'configure_dialog.ui')
        builder = Gtk.Builder()
        try:
            count = builder.add_objects_from_file(filename, ["configure_widget"])
            assert(count > 0)
        except Exception as e:
            self._log.error("Failed to load %s: %s." % (filename, str(e)))
            return None
        widget = builder.get_object("configure_widget")
        widget.set_border_width(12)
        
        if not has_schema:
            widget.set_sensitive(False)
        else:
            self._settings = Gio.Settings.new(SETTINGS_SCHEMA)
            builder.get_object("show_line_numbers").set_active(
                self._settings.get_boolean('show-line-numbers')
            )
            builder.get_object("expand_rows").set_active(
                self._settings.get_boolean('expand-rows')
            )
            builder.get_object("load_remote_files").set_active(
                self._settings.get_boolean('load-remote-files')
            )
            builder.get_object("sort_list").set_active(
                self._settings.get_boolean('sort-list')
            )
            builder.get_object("ctags_executable").set_text(
                self._settings.get_string('ctags-executable')
            )
            builder.connect_signals(self)
        return widget
    
    def on_show_line_numbers_toggled(self, button, data=None):
        self._settings.set_boolean('show-line-numbers', button.get_active())
    
    def on_expand_rows_toggled(self, button, data=None):
        self._settings.set_boolean('expand-rows', button.get_active())
    
    def on_load_remote_files_toggled(self, button, data=None):
        self._settings.set_boolean('load-remote-files', button.get_active())
    
    def on_sort_list_toggled(self, button, data=None):
        self._settings.set_boolean('sort-list', button.get_active())
        
    def on_ctags_executable_changed(self, editable, data=None):
        self._settings.set_string('ctags-executable', editable.get_text())
    
    
class SourceCodeBrowserPlugin(GObject.Object, Gedit.WindowActivatable, PeasGtk.Configurable):
    """
    Source Code Browser Plugin for Gedit 3.x
    
    Adds a tree view to the side panel of a Gedit window which provides a list
    of programming symbols (functions, classes, variables, etc.).
    
    https://live.gnome.org/Gedit/PythonPluginHowTo
    """
    __gtype_name__ = "SourceCodeBrowserPlugin"
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.setLevel(LOG_LEVEL)
        self._is_loaded = False
        self._ctags_version = None

        filename = os.path.join(ICON_DIR, "source-code-browser.png")
        self.icon = Gtk.Image.new_from_file(filename)
    
    def do_create_configure_widget(self):
        return Config().get_widget(self._has_settings_schema())
        
    def do_activate(self):
        """ Activate plugin """
        self._log.debug("Activating plugin")
        self._init_settings()
        self._version_check()
        self._sourcetree = SourceTree()
        self._sourcetree.ctags_executable = self.ctags_executable
        self._sourcetree.show_line_numbers = self.show_line_numbers
        self._sourcetree.expand_rows = self.expand_rows
        self._sourcetree.sort_list = self.sort_list
        panel = self.window.get_side_panel()
        panel.add_item(self._sourcetree, "SymbolBrowserPlugin", "Source Code", self.icon)
        self._handlers = []
        hid = self._sourcetree.connect("focus", self.on_sourcetree_focus)
        self._handlers.append((self._sourcetree, hid))
        if self.ctags_version is not None:
            hid = self._sourcetree.connect('tag-activated', self.on_tag_activated)
            self._handlers.append((self._sourcetree, hid))
            hid = self.window.connect("active-tab-state-changed", self.on_tab_state_changed)
            self._handlers.append((self.window, hid))
            hid = self.window.connect("active-tab-changed", self.on_active_tab_changed)
            self._handlers.append((self.window, hid))
            hid = self.window.connect("tab-removed", self.on_tab_removed)
            self._handlers.append((self.window, hid))
        else:
            self._sourcetree.set_sensitive(False)
    
    def do_deactivate(self):
        """ Deactivate the plugin """
        self._log.debug("Deactivating plugin")
        for obj, hid in self._handlers:
            obj.disconnect(hid)
        self._handlers = None
        pane = self.window.get_side_panel()
        pane.remove_item(self._sourcetree)
        self._sourcetree = None
    
    def _has_settings_schema(self):
        schemas = Gio.Settings.list_schemas()
        if not SETTINGS_SCHEMA in schemas:
            return False
        else:
            return True
            
    def _init_settings(self):
        """ Initialize GSettings if available. """
        if self._has_settings_schema():
            settings = Gio.Settings.new(SETTINGS_SCHEMA)
            self.load_remote_files = settings.get_boolean("load-remote-files")
            self.show_line_numbers = settings.get_boolean("show-line-numbers")
            self.expand_rows = settings.get_boolean("expand-rows")
            self.sort_list = settings.get_boolean("sort-list")
            self.ctags_executable = settings.get_string("ctags-executable")
            settings.connect("changed::load-remote-files", self.on_setting_changed)
            settings.connect("changed::show-line-numbers", self.on_setting_changed)
            settings.connect("changed::expand-rows", self.on_setting_changed)
            settings.connect("changed::sort-list", self.on_setting_changed)
            settings.connect("changed::ctags-executable", self.on_setting_changed)
            self._settings = settings
        else:
            self._log.warn("Settings schema not installed. Plugin will not be configurable.")
            self._settings = None
            self.load_remote_files = True
            self.show_line_numbers = False
            self.expand_rows = True
            self.sort_list = True
            self.ctags_executable = 'ctags'
   
    def _load_active_document_symbols(self):
        """ Load the symbols for the given URI. """
        self._sourcetree.clear()
        self._is_loaded = False
        # do not load if not the active tab in the panel
        panel = self.window.get_side_panel()
        if not panel.item_is_active(self._sourcetree):
            return

        document = self.window.get_active_document()
        if document:
            location = document.get_location()
            if location:
                uri = location.get_uri()
                self._log.debug("Loading %s...", uri)
                if uri is not None:
                    if uri[:7] == "file://":
                        # use get_parse_name() to get path in UTF-8
                        filename = location.get_parse_name() 
                        self._sourcetree.parse_file(filename, uri)
                    elif self.load_remote_files:
                        basename = location.get_basename()
                        fd, filename = tempfile.mkstemp('.'+basename)
                        contents = document.get_text(document.get_start_iter(),
                                                     document.get_end_iter(),
                                                     True)
                        os.write(fd, contents)
                        os.close(fd)
                        while Gtk.events_pending():
                            Gtk.main_iteration()
                        self._sourcetree.parse_file(filename, uri)
                        os.unlink(filename)
                    self._loaded_document = document
        self._is_loaded = True
            
    def on_active_tab_changed(self, window, tab, data=None):
        self._load_active_document_symbols()
    
    def on_setting_changed(self, settings, key, data=None):
        """
        self.load_remote_files = True
        self.show_line_numbers = False
        self.expand_rows = True
        self.ctags_executable = 'ctags'
        """
        if key == 'load-remote-files':
            self.load_remote_files = self._settings.get_boolean(key)
        elif key == 'show-line-numbers':
            self.show_line_numbers = self._settings.get_boolean(key)
        elif key == 'expand-rows':
            self.expand_rows = self._settings.get_boolean(key)
        elif key == 'sort-list':
            self.sort_list = self._settings.get_boolean(key)
        elif key == 'ctags-executable':
            self.ctags_executable = self._settings.get_string(key)
        
        if self._sourcetree is not None:
            self._sourcetree.ctags_executable = self.ctags_executable
            self._sourcetree.show_line_numbers = self.show_line_numbers
            self._sourcetree.expand_rows = self.expand_rows
            self._sourcetree.sort_list = self.sort_list
            self._sourcetree.expanded_rows = {}
            self._load_active_document_symbols()
    
    def on_sourcetree_focus(self, direction, data=None):
        if not self._is_loaded:
            self._load_active_document_symbols()
        return False
        
    def on_tab_state_changed(self, window, data=None):
        self._load_active_document_symbols()
    
    def on_tab_removed(self, window, tab, data=None):
        if not self.window.get_active_document():
            self._sourcetree.clear()
        
    def on_tag_activated(self, sourcetree, location, data=None):
        """ Go to the line where the double-clicked symbol is defined. """
        uri, line = location
        self._log.debug("%s, line %s." % (uri, line))
        document = self.window.get_active_document()
        view = self.window.get_active_view()
        line = int(line) - 1 # lines start from 0
        document.goto_line(line)
        view.scroll_to_cursor()
        
    def _version_check(self):
        """ Make sure the exhuberant ctags is installed. """
        self.ctags_version = ctags.get_ctags_version(self.ctags_executable) 
        if not self.ctags_version:
            self._log.warn("Could not find ctags executable: %s" % 
                           (self.ctags_executable))
            
        
        

from gi.repository import GObject, Gedit, Gtk, Gio, Gdk
import os, os.path
from urllib.request import pathname2url
import tempfile

max_result = 50
app_string = "Snap open"

ui_str="""<ui>
<menubar name="MenuBar">
    <menu name="FileMenu" action="File">
        <placeholder name="FileOps_2">
            <menuitem name="SnapOpen" action="SnapOpenAction"/>
        </placeholder>
    </menu>
</menubar>
</ui>
"""

# essential interface
class SnapOpenPluginInstance:
    def __init__( self, plugin, window ):
        self._window = window
        self._plugin = plugin
        self._rootdir = "file://" + os.getcwd()
        self._tmpfile = os.path.join(tempfile.gettempdir(), 'snapopen.%s.%s' % (os.getuid(),os.getpid()))
        self._show_hidden = False
        self._liststore = None;
        self._init_ui()
        self._insert_menu()

    def deactivate( self ):
        self._remove_menu()
        self._action_group = None
        self._window = None
        self._plugin = None
        self._liststore = None;
        os.popen('rm %s &> /dev/null' % (self._tmpfile))

    def update_ui( self ):
        return

    # MENU STUFF
    def _insert_menu( self ):
        manager = self._window.get_ui_manager()
        self._action_group = Gtk.ActionGroup( "SnapOpenPluginActions" )
        self._action_group.add_actions([
            ("SnapOpenAction", Gtk.STOCK_OPEN, "Snap open...",
             '<Ctrl><Alt>O', "Open file by autocomplete",
             lambda a: self.on_snapopen_action())
        ])

        manager.insert_action_group(self._action_group)
        self._ui_id = manager.add_ui_from_string(ui_str)

    def _remove_menu( self ):
        manager = self._window.get_ui_manager()
        manager.remove_ui( self._ui_id )
        manager.remove_action_group( self._action_group )
        manager.ensure_update()

    # UI DIALOGUES
    def _init_ui( self ):
        filename = os.path.dirname( __file__ ) + "/snapopen.ui"
        self._builder = Gtk.Builder()
        self._builder.add_from_file(filename)

        #setup window
        self._snapopen_window = self._builder.get_object('SnapOpenWindow')
        self._snapopen_window.connect("key-release-event", self.on_window_key)
        self._snapopen_window.set_transient_for(self._window)

        #setup buttons
        self._builder.get_object( "ok_button" ).connect( "clicked", self.open_selected_item )
        self._builder.get_object( "cancel_button" ).connect( "clicked", lambda a: self._snapopen_window.hide())

        #setup entry field
        self._glade_entry_name = self._builder.get_object( "entry_name" )
        self._glade_entry_name.connect("key-release-event", self.on_pattern_entry)

        #setup list field
        self._hit_list = self._builder.get_object( "hit_list" )
        self._hit_list.connect("select-cursor-row", self.on_select_from_list)
        self._hit_list.connect("button_press_event", self.on_list_mouse)
        self._liststore = Gtk.ListStore(str, str)
        self._liststore.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self._hit_list.set_model(self._liststore)
        column = Gtk.TreeViewColumn("Name" , Gtk.CellRendererText(), text=0)
        column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        column2 = Gtk.TreeViewColumn("File", Gtk.CellRendererText(), text=1)
        column2.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self._hit_list.append_column(column)
        self._hit_list.append_column(column2)
        self._hit_list.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

    #mouse event on list
    def on_list_mouse( self, widget, event ):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.open_selected_item( event )

    #key selects from list (passthrough 3 args)
    def on_select_from_list(self, widget, event):
        self.open_selected_item(event)

    #keyboard event on entry field
    def on_pattern_entry( self, widget, event ):
        oldtitle = self._snapopen_window.get_title().replace(" * too many hits", "")

        if event.keyval == Gdk.KEY_Return:
            self.open_selected_item( event )
            return
        pattern = self._glade_entry_name.get_text()
        pattern = pattern.replace(" ",".*")
        cmd = ""
        if self._show_hidden:
            filefilter = ""
        if len(pattern) > 0:
            # To search by name
            cmd = "grep -i -m %d -e '%s' %s 2> /dev/null" % (max_result, pattern, self._tmpfile)
            self._snapopen_window.set_title("Searching ... ")
        else:
            self._snapopen_window.set_title("Enter pattern ... ")
        #print cmd

        self._liststore.clear()
        maxcount = 0
        hits = os.popen(cmd).readlines()
        for file in hits:
            file = file.rstrip().replace("./", "") #remove cwd prefix
            name = os.path.basename(file)
            self._liststore.append([name, file])
            if maxcount > max_result:
                break
            maxcount = maxcount + 1
        if maxcount > max_result:
            oldtitle = oldtitle + " * too many hits"
        self._snapopen_window.set_title(oldtitle)

        selected = []
        self._hit_list.get_selection().selected_foreach(self.foreach, selected)

        if len(selected) == 0:
            iter = self._liststore.get_iter_first()
            if iter != None:
                self._hit_list.get_selection().select_iter(iter)

    #on menuitem activation (incl. shortcut)
    def on_snapopen_action( self ):
        self._init_ui()

        fbroot = self.get_filebrowser_root()

        if fbroot != "" and fbroot is not None:
            self._rootdir = fbroot
            self._snapopen_window.set_title(app_string + " (File Browser root)")
        else:
            self._snapopen_window.set_title(app_string + " (Working dir): " + self._rootdir)

        # cache the file list in the background
        #modify lines below as needed, these defaults work pretty well
        imagefilter = " ! -iname '*.jpg' ! -iname '*.jpeg' ! -iname '*.gif' ! -iname '*.png' ! -iname '*.psd' ! -iname '*.tif' "
        dirfilter = " ! -path '*.svn*' ! -path '*.git*' "
        binfilter = " ! -iname '*.o' ! -iname '*.so' ! -iname '*.lo' ! -iname '*.Plo' ! -iname '*.a' ! -iname '*.pyc' ! -iname '*.class' "
        os.popen("cd %s; find . -type f %s > %s 2> /dev/null &" % (self._rootdir.replace("file://", ""), imagefilter + dirfilter + binfilter, self._tmpfile))

        self._snapopen_window.show()
        self._glade_entry_name.select_region(0,-1)
        self._glade_entry_name.grab_focus()

    #on any keyboard event in main window
    def on_window_key( self, widget, event ):
        if event.keyval == Gdk.KEY_Escape:
            self._snapopen_window.hide()

    def foreach(self, model, path, iter, selected):
        selected.append(model.get_value(iter, 1))

    #open file in selection and hide window
    def open_selected_item( self, event ):
        selected = []
        self._hit_list.get_selection().selected_foreach(self.foreach, selected)
        for selected_file in    selected:
            self._open_file ( selected_file )
        self._snapopen_window.hide()

    #gedit < 2.16 version (get_tab_from_uri)
    def old_get_tab_from_uri(self, window, uri):
        docs = window.get_documents()
        for doc in docs:
            if doc.get_uri() == uri:
                return gedit.tab_get_from_document(doc)
        return None

    #opens (or switches to) the given file
    def _open_file( self, filename ):
        uri      = self._rootdir + "/" + pathname2url(filename)
        gio_file = Gio.file_new_for_uri(uri)
        tab = self._window.get_tab_from_location(gio_file)
        if tab == None:
            tab = self._window.create_tab_from_location( gio_file, None, 0, 0, False, False )
        self._window.set_active_tab( tab )

# FILEBROWSER integration
    def get_filebrowser_root(self):
        base = u'org.gnome.gedit.plugins.filebrowser'

        settings = Gio.Settings.new(base)
        root = settings.get_string('virtual-root')

        if root is not None:
            filter_mode = settings.get_strv('filter-mode')

            if 'hide-hidden' in filter_mode:
                self._show_hidden = False
            else:
                self._show_hidden = True

            return root

# STANDARD PLUMMING
class SnapOpenPlugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "SnapOpenPlugin"
    DATA_TAG = "SnapOpenPluginInstance"

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def _get_instance( self ):
        return self.window.get_data( self.DATA_TAG )

    def _set_instance( self, instance ):
        self.window.set_data( self.DATA_TAG, instance )

    def do_activate( self ):
        self._set_instance( SnapOpenPluginInstance( self, self.window ) )

    def do_deactivate( self ):
        self._get_instance().deactivate()
        self._set_instance( None )

    def do_update_ui( self ):
        self._get_instance().update_ui()

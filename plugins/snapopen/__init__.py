#VERSION 1.1.4

import gedit, gtk, gtk.glade
import gconf
import gnomevfs
import pygtk
pygtk.require('2.0')
import os, os.path, gobject

# set this to true for gedit versions before 2.16
pre216_version = False

max_result = 50

ui_str="""<ui>
<menubar name="MenuBar">
	<menu name="SnapOpenMenu" action="SnapOpenMenuAction">
		<placeholder name="SnapOpen Options">
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
		if pre216_version:
			self._encoding = gedit.gedit_encoding_get_current() 
		else:
			self._encoding = gedit.encoding_get_current()  
		self._rootdir = "file://" + os.getcwd()
		self._show_hidden = False
		self._liststore = None;
		self._init_glade()
		self._insert_menu()

	def deactivate( self ):
		self._remove_menu()
		self._action_group = None
		self._window = None
		self._plugin = None
		self._liststore = None;

	def update_ui( self ):
		return

	# MENU STUFF
	def _insert_menu( self ):
		manager = self._window.get_ui_manager()
		self._action_group = gtk.ActionGroup( "SnapOpenPluginActions" )
		snapopen_menu_action = gtk.Action( name="SnapOpenMenuAction", label="Snap", tooltip="Snap tools", stock_id=None )
		self._action_group.add_action( snapopen_menu_action )
		snapopen_action = gtk.Action( name="SnapOpenAction", label="Open...\t", tooltip="Open a file", stock_id=gtk.STOCK_OPEN )
		snapopen_action.connect( "activate", lambda a: self.on_snapopen_action() )
		self._action_group.add_action_with_accel( snapopen_action, "<Ctrl><Alt>o" )
		manager.insert_action_group( self._action_group, 0 )
		self._ui_id = manager.new_merge_id()
		manager.add_ui_from_string( ui_str )
		manager.ensure_update()

	def _remove_menu( self ):
		manager = self._window.get_ui_manager()
		manager.remove_ui( self._ui_id )
		manager.remove_action_group( self._action_group )
		manager.ensure_update()

  # UI DIALOGUES
	def _init_glade( self ):
		self._snapopen_glade = gtk.glade.XML( os.path.dirname( __file__ ) + "/snapopen.glade" )
		#setup window
		self._snapopen_window = self._snapopen_glade.get_widget( "SnapOpenWindow" )		
		self._snapopen_window.connect("key-release-event", self.on_window_key)		
		self._snapopen_window.set_transient_for(self._window)
		#setup buttons
		self._snapopen_glade.get_widget( "ok_button" ).connect( "clicked", self.open_selected_item )
		self._snapopen_glade.get_widget( "cancel_button" ).connect( "clicked", lambda a: self._snapopen_window.hide())
		#setup entry field
		self._glade_entry_name = self._snapopen_glade.get_widget( "entry_name" )
		self._glade_entry_name.connect("key-release-event", self.on_pattern_entry)		
		#setup list field
		self._hit_list = self._snapopen_glade.get_widget( "hit_list" )
		self._hit_list.connect("select-cursor-row", self.on_select_from_list)
		self._hit_list.connect("button_press_event", self.on_list_mouse)
		self._liststore = gtk.ListStore(str, str)
		self._hit_list.set_model(self._liststore)
		column = gtk.TreeViewColumn("Name" , gtk.CellRendererText(), text=0)
		column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		column2 = gtk.TreeViewColumn("File", gtk.CellRendererText(), text=1)
		column2.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
		self._hit_list.append_column(column)
		self._hit_list.append_column(column2)
		self._hit_list.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

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
		if event.keyval == gtk.keysyms.Return:
			self.open_selected_item( event )
			return
		pattern = self._glade_entry_name.get_text()
		pattern = pattern.replace(" ","*")
		#modify lines below as needed, these defaults work pretty well
		rawpath = self._rootdir.replace("file://", "")
		filefilter = " | grep -s -v \"/\.\""
		cmd = ""
		if self._show_hidden:
			filefilter = ""
		if len(pattern) > 0:
			cmd = "cd " + rawpath + "; find . -maxdepth 10 -depth -type f -iwholename \"*" + pattern + "*\" " + filefilter + " | grep -v \"~$\" | head -n " + repr(max_result + 1) + " | sort"
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
		fbroot = self.get_filebrowser_root()
		if fbroot != "" and fbroot is not None:
			self._rootdir = fbroot
			self._snapopen_window.set_title("Snap open (Filebrowser integration)")
		else:
			eddtroot = self.get_eddt_root()
			if eddtroot != "" and eddtroot is not None:
				self._rootdir = eddtroot
				self._snapopen_window.set_title("Snap open (EDDT integration)")
			else:
				self._snapopen_window.set_title("Snap open (cwd): " + self._rootdir)		
		self._snapopen_window.show()
		self._glade_entry_name.select_region(0,-1)
		self._glade_entry_name.grab_focus()

	#on any keyboard event in main window
	def on_window_key( self, widget, event ):
		if event.keyval == gtk.keysyms.Escape:
			self._snapopen_window.hide()

	def foreach(self, model, path, iter, selected):
		selected.append(model.get_value(iter, 1))

	#open file in selection and hide window
	def open_selected_item( self, event ):
		selected = []
		self._hit_list.get_selection().selected_foreach(self.foreach, selected)
		for selected_file in	selected:
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
 		uri = self._rootdir + "/" + filename
		if pre216_version:
			tab = self.old_get_tab_from_uri(self._window, uri)
		else:
			tab = self._window.get_tab_from_uri(uri) 
		if tab == None:
			tab = self._window.create_tab_from_uri( uri, self._encoding, 0, False, False )
		self._window.set_active_tab( tab )

# EDDT integration
	def get_eddt_root(self):
	  base = u'/apps/gedit-2/plugins/eddt'
	  client = gconf.client_get_default()
	  client.add_dir(base, gconf.CLIENT_PRELOAD_NONE)
	  path = os.path.join(base, u'repository')
	  val = client.get(path)
	  if val is not None:
	  	return val.get_string()

# FILEBROWSER integration
	def get_filebrowser_root(self):
	  base = u'/apps/gedit-2/plugins/filebrowser/on_load'
	  client = gconf.client_get_default()
	  client.add_dir(base, gconf.CLIENT_PRELOAD_NONE)
	  path = os.path.join(base, u'virtual_root')
	  val = client.get(path)
	  if val is not None:
	  	#also read hidden files setting
		  base = u'/apps/gedit-2/plugins/filebrowser'
		  client = gconf.client_get_default()
		  client.add_dir(base, gconf.CLIENT_PRELOAD_NONE)
		  path = os.path.join(base, u'filter_mode')
		  try:
			  fbfilter = client.get(path).get_string()
		  except AttributeError:
			  fbfilter = "hidden"
		  if fbfilter.find("hidden") == -1:
		  	self._show_hidden = True
		  else:
		  	self._show_hidden = False		  	
		  return val.get_string()

# STANDARD PLUMMING
class SnapOpenPlugin( gedit.Plugin ):
	DATA_TAG = "SnapOpenPluginInstance"

	def __init__( self ):
		gedit.Plugin.__init__( self )

	def _get_instance( self, window ):
		return window.get_data( self.DATA_TAG )

	def _set_instance( self, window, instance ):
		window.set_data( self.DATA_TAG, instance )

	def activate( self, window ):
		self._set_instance( window, SnapOpenPluginInstance( self, window ) )

	def deactivate( self, window ):
		self._get_instance( window ).deactivate()
		self._set_instance( window, None )

	def update_ui( self, window ):
		self._get_instance( window ).update_ui()

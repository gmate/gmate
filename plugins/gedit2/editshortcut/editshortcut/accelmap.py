import gedit
import gtk
import gtk.glade
import os.path
import re

from gettext import gettext as _

# Menu-definition
ui_str = """<ui>
    <menubar name="MenuBar">
        <menu name="ToolsMenu" action="Tools">  
            <placeholder name="ToolsOps_2">
                <menuitem name="EditShortcuts" action="EditShortcuts"/>
            </placeholder>
        </menu>
    </menubar>
</ui>"""



# Plugin-class
class AccelPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self._instances = dict()
    

    def activate(self, window):
        self._instances[window] = AccelPluginWindowHelper(window)
        
        
    def deactivate(self, window):
        self._instances[window].deactivate()
        del self._instances[window]
        
        
    def update_ui(self, window):
        self._instances[window].update_ui()
        
        
        
        
# Plugin-class per window-instance:        
class AccelPluginWindowHelper:
    """ This class registers a menu-item and action to show the accelerator
        -dialog """
    def __init__(self, window):
        self._window = window
        manager = self._window.get_ui_manager()

        self._action_group = gtk.ActionGroup("EditShortcutsPluginActions")
        self._action_group.add_actions([("EditShortcuts", None, 
                                         _("Edit Shortcuts"), None, 
                                         _("Edit keyboard-shortcuts"),
                                         self._on_assign_accelerators)])
        
        manager.insert_action_group(self._action_group, -1)
        self._ui_id = manager.add_ui_from_string(ui_str)


    def deactivate(self):
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()


    def update_ui(self):
        pass

    def _on_assign_accelerators(self, action):
        dlg = AccelDialog()
        dlg.run()




# Dialog-Class (impl. controller)
class AccelDialog:
    """ This class implements the accelerator-dialog """
    def __init__(self):
        # load glade-file
        glade_file = os.path.join(os.path.dirname(__file__),"accelmap.glade")
        self.__xml = gtk.glade.XML(glade_file, "AccelDialog")
        
        # and get some widgets
        self.__dialog = self.__xml.get_widget("AccelDialog")
        self.__tree = self.__xml.get_widget("ActionTree")

        # add colums to treeview
        self.__tree.append_column(gtk.TreeViewColumn(_("Action"), gtk.CellRendererText(), markup=0))
        self.__tree.append_column(gtk.TreeViewColumn(_("Shortcut"), gtk.CellRendererText(), text=1))

        # create and fill treemodel
        self.__model_iters = dict()
        self.__model = gtk.TreeStore(str, str, str)
        self.__my_accel_map = dict()
        gtk.accel_map_foreach(self.populate_tree)
        self.__model.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.__tree.set_model(self.__model)

        # connect event-handler
        self.__tree.connect("row-activated", self.on_double_click)
        self.__xml.get_widget("cancel").connect('clicked', self.on_cancel_clicked)
        self.__xml.get_widget("apply").connect('clicked', self.on_apply_clicked)



    def populate_tree(self, path, key, mode, changed):
        """ Internal used method to fill tree. """
        m = re.match("^<Actions>/(.+)/(.+)$", path)
        if not m: 
            print "Warning: action \"%s\" doesn't match re!"%path
            return
      
        grp, act = m.group(1), m.group(2)
        
        # if new group -> create one
        if not grp in self.__model_iters:
            self.__model_iters[grp] = self.__model.append(None, ["<b>%s</b>"%grp, "", ""])
        
        # assign action to group 
        self.__model.append(self.__model_iters[grp], [act, gtk.accelerator_get_label(key,mode), path])
        self.__my_accel_map[path] = (key, mode)        


    def on_double_click(self, view, path, column):
        """ If a action was double-clicked. """
        iter = self.__model.get_iter(path)
        if not self.__model[iter][2]: return True

        # show key-chooser-dialog
        dlg = KeyChooser()
        if dlg.run() == gtk.RESPONSE_DELETE_EVENT: return True 
        
        # get keys: 
        (key, modi) = dlg.keys

        # if backspace with no modifier -> delete accelerator:
        if key == 65288 and modi==0:
            self.__model[iter][1] = ""
            self.__my_accel_map[self.__model[iter][2]] = (0,0)
            return True

        # set keys to table (tree)
        self.__model[iter][1] = gtk.accelerator_get_label(key, modi)
        self.__my_accel_map[self.__model[iter][2]] = (key, modi) 


    def on_cancel_clicked(self, button):
        self.__dialog.response(gtk.RESPONSE_CANCEL)

    
    def on_apply_clicked(self, button):
        self.__dialog.response(gtk.RESPONSE_APPLY)
        self.apply_changes_to_accel(self.__model.get_iter_root())


    def run(self):
        ret = self.__dialog.run()
        self.__dialog.destroy()
    
        
    def apply_changes_to_accel(self, iter):
        """ Recursively saves accelerators from tree to gtk.AccelMap. """
        if not iter: return

        if self.__model[iter][2]:
            path        = self.__model[iter][2]
            (key, mods) = self.__my_accel_map[path]
            gtk.accel_map_change_entry(path, key, mods, False)                    

        if self.__model.iter_has_child(iter):
            self.apply_changes_to_accel(self.__model.iter_children(iter))

        self.apply_changes_to_accel(self.__model.iter_next(iter))




class KeyChooser:
    """ A small dialog to catch keyboard. """
    def __init__(self):
        glade_file = os.path.join(os.path.dirname(__file__),"accelmap.glade")
        self.__xml = gtk.glade.XML(glade_file, "KeyDialog")
    
        self.__dialog = self.__xml.get_widget("KeyDialog")
        self.__dialog.connect("key-release-event", self.on_key)
        self.__label  = self.__xml.get_widget("message")

        self.keys = None


    def on_key(self, widget, event):
        self.keys = event.keyval, event.state

        if not gtk.accelerator_valid(event.keyval, event.state):
            self.__label.set_markup("<b>%s</b> - invalid accelerator!"%gtk.accelerator_get_label(event.keyval, event.state))
            return

        action = self.accel_is_used(event.keyval, event.state)
        if action:
            self.__label.set_markup("<b>%s</b> - accelerator used by action:\n \"%s\"!"%(gtk.accelerator_get_label(event.keyval, event.state), action))
            return

        self.__dialog.response(gtk.RESPONSE_APPLY)   
   
 
    def run(self):
        ret = self.__dialog.run()
        self.__dialog.destroy()
        return ret


    def accel_is_used(self, key, modi):
        def _accel_cb(path, mkey, mmodi, changed, udata):
            if key==mkey and modi==mmodi: 
                 udata[0] = str(path)
        
        udata = ['']
        gtk.accel_map_foreach(_accel_cb, udata)
           
        m = re.match("^<Actions>(.+)$", udata[0])
        if not m: return udata[0]
        return m.group(1)

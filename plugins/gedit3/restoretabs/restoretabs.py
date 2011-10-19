import os
from gi.repository import GObject, GLib, Gtk, Gio, Gedit

SETTINGS_SCHEMA = "org.gnome.gedit.plugins.restoretabs"

class RestoreTabsWindowActivatable(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "RestoreTabsWindowActivatable"
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self._handlers = []
    
    def do_activate(self):
        handlers = []
        handler_id = self.window.connect("delete-event", 
                                         self.on_window_delete_event)                             
        self._handlers.append(handler_id)
        self._temp_handler = self.window.connect("show", self.on_window_show)  

    def do_deactivate(self):
        [self.window.disconnect(handler_id) for handler_id in self._handlers]
    
    def do_update_state(self):
        pass
        
    def is_first_window(self):
        app = Gedit.App.get_default()
        if len(app.get_windows()) <= 1:
            return True
        else:
            return False

    def on_window_delete_event(self, window, event, data=None):
        uris = []
        for document in window.get_documents():
            gfile = document.get_location()
            if gfile:
                uris.append(gfile.get_uri())
        settings = Gio.Settings.new(SETTINGS_SCHEMA)
        settings.set_value('uris', GLib.Variant("as", uris))
        return False
    
    def on_window_show(self, window, data=None):
        if self.is_first_window():
            tab = self.window.get_active_tab()
            if tab.get_state() == 0 and not tab.get_document().get_location():
                self.window.close_tab(tab)
            settings = Gio.Settings.new(SETTINGS_SCHEMA)
            uris = settings.get_value('uris')
            if uris:
                for uri in uris:
                    location = Gio.file_new_for_uri(uri)
                    tab = self.window.get_tab_from_location(location)
                    if not tab:
                        self.window.create_tab_from_location(location, None, 0, 
                                                             0, False, True)
            self.window.disconnect(self._temp_handler)


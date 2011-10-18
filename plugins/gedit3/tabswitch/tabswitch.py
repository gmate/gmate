# -*- coding: utf-8 -*-

VERSION = "0.1"

from gi.repository import GObject, Gtk, Gedit, Gdk, Gio
from gettext import gettext as _
import cPickle, os

class TabSwitchPlugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "ExamplePyWindowActivatable"
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self.id_name = 'TabSwitchPluginID'
    
    def do_activate(self):
        l_ids = []
        for signal in ('key-press-event',):
            method = getattr(self, 'on_window_' + signal.replace('-', '_'))
            l_ids.append(self.window.connect(signal, method))
        self.window.set_data(self.id_name, l_ids)
    
    def do_deactivate(self):
        l_ids = self.window.get_data(self.id_name)
        
        for l_id in l_ids:
            self.window.disconnect(l_id)
    
    def on_window_key_press_event(self, window, event):
        key = Gdk.keyval_name(event.keyval)

        if event.state & Gdk.ModifierType.CONTROL_MASK and key in ('Tab', 'ISO_Left_Tab'):
            atab = self.window.get_active_tab()
            docs = self.window.get_documents()
            tabs = []
            for doc in docs:
              tabs.append(Gedit.Tab.get_from_document(doc))
            
            tlen = len(tabs)
            i = 0
            tab = atab
            
            for tab in tabs:
                i += 1
                if tab == atab:
                    break
            
            if key == 'ISO_Left_Tab':
                i -= 2
            
            if i < 0:
                tab = tabs[tlen-1]
            elif i >= tlen:
                tab = tabs[0]
            else:
                tab = tabs[i]
            
            self.window.set_active_tab(tab)
            
            return True


# -*- coding: utf-8 -*-

VERSION = "0.1"

import gedit, gtk
from gettext import gettext as _
import cPickle, os

class TabSwitchPlugin(gedit.Plugin):
    
    def __init__(self):
        gedit.Plugin.__init__(self)
        
        self.id_name = 'TabSwitchPluginID'
    
    def activate(self, window):
        self.window = window
        
        l_ids = []
        for signal in ('key-press-event',):
            method = getattr(self, 'on_window_' + signal.replace('-', '_'))
            l_ids.append(window.connect(signal, method))
        window.set_data(self.id_name, l_ids)
    
    def deactivate(self, window):
        l_ids = window.get_data(self.id_name)
        
        for l_id in l_ids:
            window.disconnect(l_id)
    
    def on_window_key_press_event(self, window, event):
        key = gtk.gdk.keyval_name(event.keyval)
       
        if event.state & gtk.gdk.CONTROL_MASK and key in ('Tab', 'ISO_Left_Tab'):
            atab = window.get_active_tab()
            tabs = atab.parent.get_children()
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
            
            window.set_active_tab(tab)
            
            return True


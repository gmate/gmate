#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
  macropy.py 1.0.0
  
  Inspired on first implementation in C for gedit 2 by Sam K. Raju.
  This version for Gedit 3, by Eduardo Romero <eguaio@gmail.com>, Feb 13, 2012.
 
  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2, or (at your option)
  any later version.
 
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
 
  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 '''

from gi.repository import GObject, Gtk, Gedit

UI_XML = """<ui>
  <menubar name='MenuBar'>
    <menu name='ToolsMenu' action='Tools'>
      <placeholder name='ToolsOps_3'>
        <menu name='Macro' action='MacroPluginOptions'>
          <menuitem action='StartMacroRecording' 
                    name='Start Macro Recording'/>
          <menuitem action='StopMacroRecording' 
                    name= 'Stop Macro Recording'/>
          <menuitem action='PlaybackMacro' 
                    name= 'Playback Macro'/>
        </menu>
      </placeholder>
    </menu>
  </menubar>
  <toolbar name='ToolBar'>
    <separator/>
    <toolitem action='StartMacroRecording'/>
    <toolitem action='StopMacroRecording'/>
    <toolitem action='PlaybackMacro'/>
    <separator/>
  </toolbar>
</ui>"""

class macropy(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = 'Macro'
    window = GObject.property(type=Gedit.Window)
   
    def __init__(self):
        GObject.Object.__init__(self)
        self.macro = []
    
    def _add_ui(self):
        manager = self.window.get_ui_manager()
        self._actions = Gtk.ActionGroup('macro_actions')        
        self._actions.add_actions([ 
            ('MacroPluginOptions', Gtk.STOCK_INFO, 'Macro',None, 
            'Record and playback any key secquence', None),
            ('StartMacroRecording', Gtk.STOCK_MEDIA_RECORD, 
                'Start Recording Macro', 
                None, 'Start macro recording', 
                self.on_start_macro_recording),
            ('StopMacroRecording', Gtk.STOCK_MEDIA_STOP, 
                'Stop Recording Macro', 
                None, 'Stop macro recording', 
                self.on_stop_macro_recording),
            ('PlaybackMacro', Gtk.STOCK_MEDIA_PLAY, 'Playback Macro', 
                '<Ctrl><Alt>m', 'Playback recorded macro', 
                self.on_playback_macro)
        ])
        manager.insert_action_group(self._actions)
        self._ui_merge_id = manager.add_ui_from_string(UI_XML)
        manager.ensure_update()
        
    def do_activate(self):
        self._add_ui()   
        self._actions.get_action('StartMacroRecording').set_sensitive(True)         
        self._actions.get_action('StopMacroRecording').set_sensitive(False)            
        self._actions.get_action('PlaybackMacro').set_sensitive(False)  

    def do_deactivate(self):
        self._remove_ui()
  
    def on_start_macro_recording(self, action, data=None):
        handlers = []
        handler_id = self.window.connect('key-press-event', 
                                          self.on_key_press_event)
        handlers.append(handler_id)
        self.window.set_data('Macro1PluginHandlers', handlers) 
        self.macro = []
        self._actions.get_action('StartMacroRecording').set_sensitive(False)
        self._actions.get_action('StopMacroRecording').set_sensitive(True) 
        self._actions.get_action('PlaybackMacro').set_sensitive(False)

    def on_stop_macro_recording(self, action, data=None):
        handlers = self.window.get_data('Macro1PluginHandlers')
        for handler_id in handlers:
            self.window.disconnect(handler_id)
        self._actions.get_action('StartMacroRecording').set_sensitive(True)
        self._actions.get_action('StopMacroRecording').set_sensitive(False) 
        self._actions.get_action('PlaybackMacro').set_sensitive(True) 

    def on_playback_macro(self, action, data=None):    
        for e in self.macro:
            e.put()     
    
    def on_key_press_event(self, window, event):
        self.macro.append(event.copy())
            
    def _remove_ui(self):
        manager = self.window.get_ui_manager()
        manager.remove_ui(self._ui_merge_id)
        manager.remove_action_group(self._actions)
        manager.ensure_update()

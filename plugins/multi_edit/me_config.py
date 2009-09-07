"""
    Multi-edit - Gedit plugin
    Copyright (C) 2009 Jonathan Walsh
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os

import gtk
import gtk.glade

class ConfigDialog:
    """ Plugin config window instance """
    
    def __init__(self, plugin):
        self._plugin = plugin
        glade_file = os.path.join(os.path.dirname(__file__), 'config.glade')
        self._ui = gtk.glade.XML(glade_file, 'settings_dialog')
        
        # Widgets
        self._dialog = self._ui.get_widget('settings_dialog')
        self._auto_incr_field = self._ui.get_widget('auto_incr').get_buffer()
        self._columns_checkbox = self._ui.get_widget('columns_always_avail')
        
        # auto_incr_field style
        self._auto_incr_field.create_tag('monospace', family='monospace')
        self._auto_incr_field.connect('changed', self._style_auto_incr)
        
        # Load settings
        self._auto_incr_field.set_text(self._plugin._sc_auto_incr_str)
        self._columns_checkbox.set_active(self._plugin._columns_always_avail)
        
        self._dialog.connect('response', self._button_event)
    
    def _button_event(self, dialog, resp_id):
        """ Button event handler. """
        resp = {'default':1, 'cancel':2, 'apply':3}
        
        if resp_id == resp['default']:
            self._auto_incr_field.set_text(self._plugin._sc_auto_incr_def)
        
        elif resp_id == resp['apply']:
            # Save to vars
            start = self._auto_incr_field.get_start_iter()
            end = self._auto_incr_field.get_end_iter()
            self._plugin._sc_auto_incr_str = self._auto_incr_field.get_text(start, end)
            self._plugin._columns_always_avail = self._columns_checkbox.get_active()
            
            # Save to gconf
            self._plugin._save_settings()
            
            # Translate to keyvals
            self._plugin._set_shortcut_keyvals()
        
        if resp_id in (resp['cancel'], resp['apply']):
            self._destroy()
    
    def _style_auto_incr(self, *args):
        """ Ensure the auto-incr field stays monospace. """
        text = self._auto_incr_field
        text.apply_tag_by_name('monospace', text.get_start_iter(), text.get_end_iter())
    
    def _destroy(self):
        self._dialog.destroy()
        self._plugin._config_instance = None


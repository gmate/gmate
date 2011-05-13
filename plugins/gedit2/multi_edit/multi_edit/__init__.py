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

import csv

import gtk
import gedit
import gconf

import me_window
import me_config


class MultiEditPlugin(gedit.Plugin):
    """ Plugin instance (Multi-edit) """
    
    # ============================================================ Gedit expected functions
    
    def __init__(self):
        gedit.Plugin.__init__(self)
        self._windows = {}
        self._gconf_key_base = '/apps/gedit-2/plugins/multi_edit/'
        
        # Config defaults
        self._columns_always_avail_def = 'True'
        self._sc_auto_incr_def = '\n'.join((
            '- abc:a',
            '_ abc:A',
            '= abc:z',
            '+ abc:Z',
            '0 num:0,1',
            ') num:1,1',
            'x list:"This","is","an","example",";)",""',
        ))
        
        # Advanced config
        self._sc_add_mark_def = 'r'
        self._sc_level_marks_def = 'l'
        self._sc_temp_incr_def = 'i'
        self._sc_mark_vert_def = {
            'up': 'Page_Up',
            'down': 'Page_Down',
            'smart_up': 's+Page_Up',
            'smart_down': 's+Page_Down',
        }
        
        # Load settings
        self._columns_always_avail = self._get_config_str('columns_always_avail', self._columns_always_avail_def)
        self._columns_always_avail = self._columns_always_avail == 'True'
        
        self._sc_add_mark_str = self._sc_add_mark_def
        self._sc_level_marks_str = self._sc_level_marks_def
        self._sc_temp_incr_str = self._sc_temp_incr_def
        self._sc_mark_vert_str = self._sc_mark_vert_def
        self._sc_auto_incr_str = self._get_config_str('auto_incr', self._sc_auto_incr_def)
        
        # Shortcut strings to keyvals
        self._set_shortcut_keyvals()
    
    def activate(self, window):
        """ Create a Multi-edit instance for a window. """
        self._windows[window] = me_window.WindowInstance(self, window)
    
    def deactivate(self, window):
        """ Deactivate Multi-edit for a window. """
        self._windows[window].deactivate()
        del self._windows[window]
    
    def update_ui(self, window):
        pass

    def is_configurable(self):
        return True
    
    def create_configure_dialog(self):
        """ Show the plugin settings window. """
        self._config_instance = me_config.ConfigDialog(self)
        return self._config_instance._dialog
    
    # ============================================================ Shortcuts
    
    def _get_keyval(self, string):
        """ Get a GTK keyval from a single character or a keyval name.
        
        Result is a tuple with a "shift req" bool (for non-printables)
        """
        if len(string) == 1:
            return (gtk.gdk.unicode_to_keyval(ord(unicode(string))), None)
        if len(string) > 1:
            shift_req = string[:2] == 's+'
            if shift_req:
                string = string[2:]
            keyval = gtk.gdk.keyval_from_name(string)
            if gtk.gdk.keyval_to_unicode(keyval) != 0:
                shift_req = None
            return (keyval, shift_req)
        else:
            return (0, None)
    
    def _set_shortcut_keyvals(self):
        """ Convert the shortcut strings to GTK readable keyvals. """
        self._sc_add_mark = self._get_keyval(self._sc_add_mark_str)
        self._sc_level_marks = self._get_keyval(self._sc_level_marks_str)
        self._sc_temp_incr = self._get_keyval(self._sc_temp_incr_str)
        self._sc_auto_incr = self._parse_sc_auto_incr(self._sc_auto_incr_str)
        self._sc_mark_vert = {
            'up': self._get_keyval(self._sc_mark_vert_str['up']),
            'down': self._get_keyval(self._sc_mark_vert_str['down']),
            'smart_up': self._get_keyval(self._sc_mark_vert_str['smart_up']),
            'smart_down': self._get_keyval(self._sc_mark_vert_str['smart_down']),
        }
    
    def _parse_sc_auto_incr(self, string):
        """ Parse the multi-line string and return a dictionary of auto-incr shortcuts. """
        lines = string.splitlines()
        result = {}
        for line in lines:
            (line, sep, args) = line.partition(':')
            if sep != ':': continue
            (key, sep, incr_type) = line.partition(' ')
            if sep != ' ': continue
            keyval, shift_req = self._get_keyval(key)
            if keyval == 0: continue
            args = csv.reader([args]).next()
            if len(args) == 0: continue
            result[keyval] = {
                'shift_req': shift_req,
                'type': incr_type,
                'args': args,
            }
        return result
    
    # ============================================================ gconf
    
    def _get_config_str(self, key, default=''):
        """ Retrieve a gconf key, or its default if not set. """
        key = self._gconf_key_base + key
        value = gconf.client_get_default().get(key)
        if value is not None and value.type == gconf.VALUE_STRING:
            return value.get_string()
        else:
            return default
    
    def _set_config_str(self, key, string):
        """ Save a value to a gconf key. """
        key = self._gconf_key_base + key
        value = gconf.Value(gconf.VALUE_STRING)
        value.set_string(string)
        gconf.client_get_default().set(key, value)
    
    def _save_settings(self):
        """ Wrapper for saving the current settings to gconf. """
        self._set_config_str('auto_incr', self._sc_auto_incr_str)
        self._set_config_str('columns_always_avail', str(self._columns_always_avail))


# Copyright (C) 2007 - Nando Vieira
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import gedit
import gtk
import gtk.gdk
import os
import os.path
from gettext import gettext as _
import re
import webbrowser
from time import sleep

def debug(text, level=1):
    if os.environ.has_key('RH_DEBUG'):
        try:
            required_level = int(os.environ['RH_DEBUG'])
            
            if required_level >= level:
                print "[rails_mode] %s" % text
        except:
            print "[rails_mode] debug error"

class RailsHotkeysPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self.instances = {}

    def activate(self, window):
        debug('activating plugin')
        self.instances[window] = RailsHotkeysWindowHelper(self, window)

    def deactivate(self, window):
        debug('deactivating plugin')
        self.instances[window].deactivate()
        del self.instances[window]

    def update_ui(self, window):
        debug('updating ui')
        self.instances[window].update_ui()

class RailsHotkeysWindowHelper:
    handlers = {}
    
    def __init__(self, plugin, window):
        self.window = window
        self.plugin = plugin
        self.statusbar = window.get_statusbar()
        self.context_id = self.statusbar.get_context_id('RailsHotkeysStatusbar')
        self.status_label = gtk.Label('RH')
        self.frame = gtk.Frame()
        
        self.status_label.set_alignment(0, 0)
        self.status_label.show()
        self.frame.add(self.status_label)
        self.frame.show()
        self.statusbar.add(self.frame)
        
        self.set_status()
        
        for view in window.get_views():
            self.connect_handlers(view)
        
        window.connect('tab_added', self.on_tab_added)
    
    def deactivate(self):
        debug('deactivate function called')
        for view in self.handlers:
            view.disconnect(self.handlers[view])
        
        self.window = None
        self.plugin = None
    
    def connect_handlers(self, view):
        handler = view.connect('key-press-event', self.on_key_press)
        self.handlers[view] = handler
        
    def on_tab_added(self, window, tab):
        self.connect_handlers(tab.get_view())
    
    def update(self, text=None):
        pass
    
    def update_ui(self):
        self.set_status()
    
    def set_status(self, text=None):
        self.statusbar.pop(self.context_id)
        label = 'RH'
        
        if text is not None:
            label = "RH: %s " % _(text)
        
        self.status_label.set_text(label)
    
    def create_tab(self, uri):
        # have to find out the file's encoding
        # so calling gedit command is probably better
        # self.window.create_tab_from_uri(uri, None, 1, False, False)
        os.system('gedit %s' % uri)
    
    def get_rails_root(self, uri):
        rails_root = self.get_data('RailsModeRoot')
        
        if rails_root:
            debug('returning previously defined rails_root')
            return rails_root
        
        base_dir = os.path.dirname(uri)
        depth = 10

        while depth > 0:
            depth -= 1
            app_dir = os.path.join(base_dir, 'app')
            config_dir = os.path.join(base_dir, 'config')
            debug('base_dir: %s' % base_dir)
            if os.path.isdir(app_dir) and os.path.isdir(config_dir):
                rails_root = base_dir
                break
            else:
                base_dir = os.path.abspath(os.path.join(base_dir, '..'))

        if rails_root:
            self.set_data('RailsModeRoot', rails_root)
        
        debug('setting rails_root to %s' % rails_root)
        
        return rails_root
    
    def pluralize(self, text):
        plurals = [
            ('$', 's'),
            ('s$', 's'),
            ('(ax|test)is$', '\\1es'),
            ('(octop|vir)us$', '\\1i'),
            ('(alias|status)$', '\\1es'),
            ('(bu)s$', '\\1ses'),
            ('(buffal|tomat)o$', '\\1oes'),
            ('([ti])um$', '\\1a'),
            ('sis$', 'ses'),
            ('(?:([^f])fe|([lr])f)$', '\\1\\2ves'),
            ('(hive)$', '\\1s'),
            ('([^aeiouy]|qu)y$', '\\1ies'),
            ('([^aeiouy]|qu)ies$', '\\1y'),
            ('(x|ch|ss|sh)$', '\\1es'),
            ('(matr|vert|ind)ix|ex$', '\\1ices'),
            ('([m|l])ouse$', '\\1ice'),
            ('^(ox)$', '\\1en'),
            ('(quiz)$', '\\1zes'),
            ('^person$', 'people'),
            ('^man$', 'men'),
            ('^child$', 'children'),
            ('^sex$', 'sexes'),
            ('^move$', 'moves'),
            ('^(deer|fish|sheep|species)$', '\\1')
        ]
        plurals.reverse()
        
        for re_from, re_to in plurals:
            if re.search(re_from, text):
                text = re.sub(re_from, re_to, text)
                break
        return text

    def singularize(self, text):
        singulars = [
            ('s$', ''),
            ('(n)ews$', '\\1ews'),
            ('([ti])a$', '\\1um'),
            ('((a)naly|(b)a|(d)iagno|(p)arenthe|(p)rogno|(s)ynop|(t)he)ses$', '\\1\\2sis'),
            ('(^analy)ses$', '\\1sis'),
            ('([^f])ves$', '\\1fe'),
            ('(hive)s$', '\\1'),
            ('(tive)s$', '\\1'),
            ('([lr])ves$', '\\1f'),
            ('([^aeiouy]|qu)ies$', '\\1y'),
            ('(s)eries$', '\\1eries'),
            ('(m)ovies$', '\\1ovie'),
            ('(x|ch|ss|sh)es$', '\\1'),
            ('([m|l])ice$', '\\1ouse'),
            ('(bus)es$', '\\1'),
            ('(o)es$', '\\1'),
            ('(shoe)s$', '\\1'),
            ('(cris|ax|test)es$', '\\1is'),
            ('([octop|vir])i$', '\\1us'),
            ('(alias|status)es$', '\\1'),
            ('^(ox)en', '\\1'),
            ('(vert|ind)ices$', '\\1ex'),
            ('(matr)ices$', '\\1ix'),
            ('(quiz)zes$', '\\1'),
            ('^people$', 'person'),
            ('^men$', 'man'),
            ('^children$', 'child'),
            ('^sexes$', 'sex'),
            ('^moves$', 'move'),
            ('^(deer|fish|sheep|species)$', '\\1')
        ]
        singulars.reverse()
        
        for re_from, re_to in singulars:
            if re.search(re_from, text):
                text = re.sub(re_from, re_to, text)
                break
        return text

    def on_key_press(self, view, event):
        ctrl = False
        shift = False
        alt = False
        
        keys = {
            'A': (gtk.keysyms.a, gtk.keysyms.A),
            'B': (gtk.keysyms.b, gtk.keysyms.B),
            'C': (gtk.keysyms.c, gtk.keysyms.C),
            'D': (gtk.keysyms.d, gtk.keysyms.D),
            'E': (gtk.keysyms.e, gtk.keysyms.E),
            'F': (gtk.keysyms.f, gtk.keysyms.F),
            'H': (gtk.keysyms.h, gtk.keysyms.H),
            'I': (gtk.keysyms.i, gtk.keysyms.I),
            'J': (gtk.keysyms.j, gtk.keysyms.J),
            'L': (gtk.keysyms.l, gtk.keysyms.L),
            'M': (gtk.keysyms.m, gtk.keysyms.M),
            'N': (gtk.keysyms.n, gtk.keysyms.N),
            'P': (gtk.keysyms.p, gtk.keysyms.P),
            'Q': (gtk.keysyms.q, gtk.keysyms.Q),
            'R': (gtk.keysyms.r, gtk.keysyms.R),
            'T': (gtk.keysyms.t, gtk.keysyms.T),
            'U': (gtk.keysyms.u, gtk.keysyms.U),
            'V': (gtk.keysyms.v, gtk.keysyms.V),
        }
        
        if event.state & gtk.gdk.CONTROL_MASK:
            ctrl = True
        
        if event.state & gtk.gdk.SHIFT_MASK:
            shift = True
        
        if event.state & gtk.gdk.MOD1_MASK:
            alt = True
        
        debug('key: %s, ctrl: %s, shift: %s, alt: %s' % (event.keyval, ctrl, shift, alt), 2)
        
        # canceling Rails Mode
        if self.get_rails_mode() and event.keyval == gtk.keysyms.Escape:
            debug('Rails mode enabled, so disable it')
            self.set_status()
            view.set_data('RailsMode', False)
            return True
        
        r_pressed = event.keyval in keys['R']
        
        debug('R key pressed? %s' % r_pressed, 2)
        
        # starting Rails Mode
        if r_pressed and ctrl and shift:
            if not self.get_rails_mode():
                debug('enabling Rails Mode')
                self.set_status('Press F1 for help')
                self.set_rails_mode(True)
                return True
        
        if self.get_rails_mode():
            uri = view.get_buffer().get_uri_for_display()
            debug('current file uri: %s' % uri)
            
            if not uri:
                return True
            
            uri = os.path.abspath(uri)
            name = re.sub('(_controller|_test|_controller_test)?\.(rb|yml)$', '', os.path.basename(uri))
            type = None
            
            if event.keyval in keys['A']:
                type = 'application'
            elif event.keyval in keys['B']:
                type = 'rails'
            elif event.keyval in keys['C']:
                type = 'controller'
            elif event.keyval in keys['D']:
                type = 'database'
            elif event.keyval in keys['E']:
                type = 'environment'
            elif event.keyval in keys['F']:
                type = 'functional'
            elif event.keyval in keys['H']:
                type = 'helper'
            elif event.keyval in keys['I']:
                type = 'integration'
            elif event.keyval in keys['J']:
                type = 'fixtures'
            elif event.keyval in keys['L']:
                type = 'layout'
            elif event.keyval in keys['M']:
                type = 'model'
            elif event.keyval in keys['N']:
                type = 'navigate'
            elif event.keyval in keys['P']:
                type = 'public'
            #elif event.keyval in keys['Q']:
            elif event.keyval == gtk.keysyms.F1:
                type = 'help'
            elif event.keyval in keys['R']:
                type = 'routes'
            elif event.keyval in keys['T']:
                type = 'tests'
            elif event.keyval in keys['U']:
                type = 'unit'
            elif event.keyval in keys['V']:
                type = 'views'
            
            debug('type: %s' % type)
            
            if type:
                debug('Rails mode enabled, so disable it')
                self.open(type, uri, name)
                self.set_rails_mode(False)
                return True
            else:
                self.set_status('Key not recognized')
                return True
        else:
            return False
    
    def set_data(self, name, value):
        self.window.get_active_tab().get_view().set_data(name, value)
    
    def get_data(self, name):
        return self.window.get_active_tab().get_view().get_data(name)
    
    def set_rails_mode(self, value):
        self.set_data('RailsMode', value)
    
    def get_rails_mode(self):
        return self.get_data('RailsMode')
    
    def open(self, type, uri, name=None):
        rails_root = rails_root = self.get_rails_root(uri)
        status = None
        
        if not rails_root:
            return self.set_status(_('Root not found'))
        
        if re.search('\/app\/views\/', uri):
            name = os.path.basename(os.path.dirname(uri))
        
        if type == 'unit':
            name = self.singularize(name)
            path = os.path.join(rails_root, 'test', 'unit', '%s_test.rb' % name)
        elif type == 'functional':
            name = self.pluralize(name)
            path = os.path.join(rails_root, 'test', 'functional', '%s_controller_test.rb' % name)
        elif type == 'integration':
            name = self.pluralize(name)
            path = os.path.join(rails_root, 'test', 'integration', '%s_test.rb' % name)
        elif type == 'model':
            name = self.singularize(name)
            path = os.path.join(rails_root, 'app', 'models', '%s.rb' % name)
        elif type == 'controller':
            name = self.pluralize(name)
            path = os.path.join(rails_root, 'app', 'controllers', '%s_controller.rb' % name)
        elif type == 'database':
            path = os.path.join(rails_root, 'config', 'database.yml')
        elif type == 'routes':
            path = os.path.join(rails_root, 'config', 'routes.rb')
        elif type == 'environment':
            path = os.path.join(rails_root, 'config', 'environment.rb')
        elif type == 'fixtures':
            name = self.pluralize(name)
            path = os.path.join(rails_root, 'test', 'fixtures', '%s.yml' % name)
        elif type == 'tests':
            self.open('unit', uri, name)
            self.open('functional', uri, name)
            self.open('integration', uri, name)
            self.open('fixtures', uri, name)
            return
        elif type == 'application':
            path = os.path.join(rails_root, 'app', 'controllers', 'application.rb')
        elif type == 'layout':
            path = os.path.join(rails_root, 'app', 'views', 'layouts', 'application.rhtml')
        elif type == 'helper':
            name = self.pluralize(name)
            path = os.path.join(rails_root, 'app', 'helpers', '%s_helper.rb' % name)
        elif type == 'rails':
            path = rails_root
        elif type == 'help':
            path = os.path.join(os.path.dirname(__file__), "rails_hotkeys.html")
            debug('opening %s' % path)
            webbrowser.open(path, 2, 1)
            return
        elif type == 'navigate':
            webbrowser.open('http://localhost:3000/', 2, 1)
            return
        elif type == 'views':
            path = os.path.join(rails_root, 'app', 'views')
        elif type == 'public':
            path = os.path.join(rails_root, 'public')
        
        debug('type: %s, path: %s' % (type, path))
        
        status_message = type
        
        if os.path.isdir(path):
            os.system('nautilus %s' % path)
        elif os.path.isfile(path):
            self.create_tab(path)
        else:
            status_message = 'File not found'
        
        self.set_status(status_message)

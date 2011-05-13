# -*- coding: utf-8 -*-

# Rails Hot Commands Gedit Plugin
#
# Copyright (C) 2007 - Tiago Bastos
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
#
# Thanks for: Nando Vieira - http://simplesideias.com.br/ (get_rails_root method)

import gtk
import gedit
import os
import os.path
from vte import Terminal
import gconf
import gnomevfs

class TerminaldWidget():
    def __init__(self, window):
        self.window = window

        self.bottom = window.get_bottom_panel()

        self.uri = window.get_active_document().get_uri_for_display()
        self.term = Terminal()
        self.term.set_emulation("xterm")
        self.term.set_audible_bell(False)
        self.term.set_scrollback_lines(150)
        self.term.set_size_request(10,100)
        self.term.fork_command('bash')

        self.term_scrollbar = gtk.VScrollbar()
        self.term_scrollbar.set_adjustment(self.term.get_adjustment())

        self.term_box = gtk.HBox()
        self.term_box.pack_start(self.term, True, True, 0)
        self.term_box.pack_end(self.term_scrollbar, False, False, 0)

        self.close_bt = gtk.Button("Close")
        self.close_bt.connect("clicked", self.close_bt_action, "Exit!")

        self.container = gtk.VBox(False)

       # self.term.connect("child-exited", lambda term: term.fork_command('irb'))
        self.term.connect("child-exited", self.close_term_action_child_exited)

        self.table = gtk.Table(2,1,False)
        self.table.attach(self.term_box,0,1,0,1)
        self.table.attach(self.close_bt,0,1,1,2,gtk.FILL|gtk.SHRINK,gtk.FILL|gtk.SHRINK, 0, 0)
        self.container.pack_start(self.table)
        self.close_bt.show()
        self.table.show()
        self.term_box.show_all()

    def close_bt_action(self, widget, data=None):
      self.close()

    def close_term_action_child_exited(self, term):
      self.close()

    def close(self):
        self.bottom.remove_item(self.container)
        self.bottom.hide()
        self.container.destroy()

    def run(self,command=''):
        self.rails_root = self.get_rails_root(self.uri)

        if self.rails_root=='':
             self.rails_root = self.get_filebrowser_root()

        if self.rails_root=='':
            os.popen("notify-send -t 1600 -i gtk-dialog-info 'Alert!' 'This is not a rails project file!'")
        elif command.strip()=='':
            os.popen("notify-send -t 1600 -i gtk-dialog-info 'Alert!' 'Hey, type something!'")
        else:
            self.term.feed_child("cd "+self.rails_root+" \n")
            self.term.feed_child(command+"\n")

            self.bottom.show()

            self.image = gtk.Image()
            self.image.set_from_icon_name('gnome-mime-application-x-shellscript', gtk.ICON_SIZE_MENU)

            self.bottom.add_item(self.container, _('Run Rails Command: '+command), self.image)
            self.window.set_data('RubyTerminalPluginInfo', self.container)
            self.bottom.activate_item(self.container)
            self.term.grab_focus()
        self.close_bt_action()

    def get_rails_root(self, uri):
        base_dir = os.path.dirname(uri)
        depth = 10
        rails_root = ''

        while depth > 0:
            depth -= 1
            app_dir = os.path.join(base_dir, 'app')
            config_dir = os.path.join(base_dir, 'config')
            if os.path.isdir(app_dir) and os.path.isdir(config_dir):
                rails_root = base_dir
                break
            else:
                base_dir = os.path.abspath(os.path.join(base_dir, '..'))
        return rails_root


    # FileBrowser Integration
    def get_filebrowser_root(self):
       base = u'/apps/gedit-2/plugins/filebrowser/on_load'
       client = gconf.client_get_default()
       client.add_dir(base, gconf.CLIENT_PRELOAD_NONE)
       path = os.path.join(base, u'virtual_root')
       val = client.get(path)
       if val is not None:
          return gnomevfs.get_local_path_from_uri(val.get_string())
       else:
          return ''

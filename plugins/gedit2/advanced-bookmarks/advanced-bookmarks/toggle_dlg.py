# -*- coding: utf-8 -*-

#  Copyright (C) 2008 - Eugene Khorev
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330,
#  Boston, MA 02111-1307, USA.

import pygtk
pygtk.require("2.0")
import gtk
import gedit
import os

class toggle_dlg(gtk.Dialog):

    def __init__(self, parent, config):
        # Create config diaog window
        title = _("Bookmark properties")
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK)

        super(toggle_dlg, self).__init__(title, parent, 0, buttons)
        
        self.vbox.set_homogeneous(False)
        
        # Create diaog items
        self._msg = gtk.Label(_("Comment"))
        self._msg.set_property("xalign", 0.0)
        self.vbox.pack_start(self._msg, True, True, 5)
        
        self._input = gtk.Entry()
        self._input.connect("key-press-event", self._on_input_key)
        self.vbox.pack_start(self._input, True, True, 0)
        
        self._note = gtk.Label(_("(leave blank to use source line)"))
        self.vbox.pack_start(self._note, True, True, 5)
        
        self.vbox.show_all()
        
        # Setup configuration dictionary
        self._config = config
    
    def reset(self, comment = ""):#, prompt = True):
        self._input.set_text(comment)
        self._input.grab_focus()
    
    def get_comment(self):
        return self._input.get_text().strip()
    
    def _on_input_key(self, widget, event):
        if event.keyval == gtk.keysyms.Return:
            self.response(gtk.RESPONSE_OK)
    
# ex:ts=4:et:

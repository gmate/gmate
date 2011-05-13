# Copyright (C) 2006 Frederic Back (fredericback@gmail.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, 
# Boston, MA 02111-1307, USA.

# The class browser pixmaps are stolen from Jesse Van Den Kieboom's
# ctags plugin (http://live.gnome.org/Gedit/PluginCodeListing)

import gtk
import sys, os

pixbufs = {
    "class" : None,
    "default" : None,
    "enum" : None,
    "enum_priv" : None,
    "enum_prot" : None,
    "field" : None,
    "field_priv" : None,
    "field_prot" : None,
    "method" : None,
    "method_priv" : None,
    "method_prot" : None,
    "namespace" : None,
    "patch" : None,
    "struct" : None,
    "struct_priv" : None,
    "struct_prot" : None,
    "variable" : None,
}

def initialise():
    for key in pixbufs:
        try:
            name = "%s.png" % key
            filename = os.path.join(sys.path[0],"classbrowser","pixmaps",name)
            if not os.path.exists(filename):
                filename = os.path.join(os.path.dirname(__file__),"pixmaps",name)
            pixbufs[key] = gtk.gdk.pixbuf_new_from_file(filename)
        except:
            print "Class browser plugin couldn't locate",filename





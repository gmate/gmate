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

import gobject
import gtk
import gconf

def singleton():
    if Options.singleton is None:
        Options.singleton = Options()
    return Options.singleton

class Options(gobject.GObject):

    __gsignals__ = {
        'options-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    singleton = None

    def __init__(self):

        gobject.GObject.__init__(self)
        self.__gconfDir = "/apps/gedit-2/plugins/classbrowser"

        # default values
        self.verbose = False
        self.autocollapse = True
        self.jumpToTagOnMiddleClick = False
        self.colours = {
            "class" : gtk.gdk.Color(50000,20000,20000),
            "define": gtk.gdk.Color(60000,0,0),
            "enumerator": gtk.gdk.Color(0,0,0),
            "member" : gtk.gdk.Color(0,0,60000),
            "function" : gtk.gdk.Color(50000,0,60000),
            "namespace" : gtk.gdk.Color(0,20000,0),
        }
    
        # create gconf directory if not set yet
        client = gconf.client_get_default()        
        if not client.dir_exists(self.__gconfDir):
            client.add_dir(self.__gconfDir,gconf.CLIENT_PRELOAD_NONE)

        # get the gconf keys, or stay with default if key not set
        try:
            self.verbose = client.get_bool(self.__gconfDir+"/verbose") \
                or self.verbose 

            self.autocollapse = client.get_bool(self.__gconfDir+"/autocollapse") \
                or self.autocollapse 

            self.jumpToTagOnMiddleClick = client.get_bool(self.__gconfDir+"/jumpToTagOnMiddleClick") \
                or self.jumpToTagOnMiddleClick 

            for i in self.colours:
                col = client.get_string(self.__gconfDir+"/colour_"+i)
                if col: self.colours[i] = gtk.gdk.color_parse(col)

        except Exception, e: # catch, just in case
            print e
            
    def __del__(self):
        # write changes to gconf
        client = gconf.client_get_default()
        client.set_bool(self.__gconfDir+"/verbose", self.verbose)
        client.set_bool(self.__gconfDir+"/autocollapse", self.autocollapse)
        client.set_bool(self.__gconfDir+"/jumpToTagOnMiddleClick", self.jumpToTagOnMiddleClick)
        for i in self.colours:
            client.set_string(self.__gconfDir+"/colour_"+i, self.color_to_hex(self.colours[i]))

    def create_configure_dialog(self):
        win = gtk.Window()
        win.connect("delete-event",lambda w,e: w.destroy())
        win.set_title("Preferences")
        vbox = gtk.VBox() 

        #--------------------------------  

        notebook = gtk.Notebook()
        notebook.set_border_width(6)
        vbox.pack_start(notebook)

        vbox2 = gtk.VBox()
        vbox2.set_border_width(6) 

        box = gtk.HBox()
        verbose = gtk.CheckButton("show debug information")
        verbose.set_active(self.verbose)
        box.pack_start(verbose,False,False,6)
        vbox2.pack_start(box,False)

        box = gtk.HBox()
        autocollapse = gtk.CheckButton("autocollapse symbol tree")
        autocollapse.set_active(self.autocollapse)
        box.pack_start(autocollapse,False,False,6)
        vbox2.pack_start(box,False)

        box = gtk.HBox()
        jumpToTagOnMiddleClick = gtk.CheckButton("jump to tag on middle click")
        jumpToTagOnMiddleClick.set_active(self.jumpToTagOnMiddleClick)
        box.pack_start(jumpToTagOnMiddleClick,False,False,6)
        vbox2.pack_start(box,False)

        notebook.append_page(vbox2,gtk.Label("General"))

        #--------------------------------       
        vbox2 = gtk.VBox()
        vbox2.set_border_width(6)

        button = {}
        for i in self.colours:
            box = gtk.HBox()
            button[i] = gtk.ColorButton()
            button[i].set_color(self.colours[i])
            box.pack_start(button[i],False)
            box.pack_start(gtk.Label(i),False,False,6)
            vbox2.pack_start(box)

        notebook.append_page(vbox2,gtk.Label("Colours"))

        def setValues(w):

            # set class attributes
            self.verbose = verbose.get_active()
            self.autocollapse = autocollapse.get_active()
            self.jumpToTagOnMiddleClick = jumpToTagOnMiddleClick.get_active()
            for i in self.colours:
                self.colours[i] = button[i].get_color()
                
            # write changes to gconf
            client = gconf.client_get_default()

            client.set_bool(self.__gconfDir+"/verbose", self.verbose)
            client.set_bool(self.__gconfDir+"/autocollapse", self.autocollapse)
            client.set_bool(self.__gconfDir+"/jumpToTagOnMiddleClick", self.jumpToTagOnMiddleClick)
            for i in self.colours:
                client.set_string(self.__gconfDir+"/colour_"+i, self.color_to_hex(self.colours[i]))

            # commit changes and quit dialog
            self.emit("options-changed")
            win.destroy()

        box = gtk.HBox()
        b = gtk.Button(None,gtk.STOCK_OK)
        b.connect("clicked",setValues)
        box.pack_end(b,False)
        b = gtk.Button(None,gtk.STOCK_CANCEL)
        b.connect("clicked",lambda w,win: win.destroy(),win)
        box.pack_end(b,False)
        vbox.pack_start(box,False)

        win.add(vbox)
        win.show_all()        
        return win

    def color_to_hex(self, color ):
        r = str(hex( color.red / 256 ))[2:]
        g = str(hex( color.green / 256 ))[2:]
        b = str(hex( color.blue / 256 ))[2:]
        return "#%s%s%s"%(r.zfill(2),g.zfill(2),b.zfill(2))

gobject.type_register(Options)

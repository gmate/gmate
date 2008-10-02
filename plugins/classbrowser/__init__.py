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

import gedit
import gtk
from browserwidget import ClassBrowser
from tabwatch import TabWatch
import options
from parser_ctags import CTagsParser
from parser_python import PythonParser
from parser_ruby import RubyParser
from parser_html import geditHTMLParser
from parser_diff import DiffParser

icon = [
"16 16 2 1",
" 	c None",
".	c #000000",
"                ",
" .............. ",
"                ",
"      ......... ",
"                ",
"      ......... ",
"                ",
"      ......... ",
"                ",
"                ",
" .............. ",
"                ",
"      ......... ",
"                ",
"      ......... ",
"                "]
       
#-------------------------------------------------------------------------------
class ClassBrowserPlugin(gedit.Plugin):

    def __init__(self):
        gedit.Plugin.__init__(self)
        

    def create_configure_dialog(self):
        return options.singleton().create_configure_dialog()


    def is_configurable(self):
        return True
        

    def register_parsers(self, window):
        """ Add new parsers here. """
        self.tabwatch.defaultparser = CTagsParser()
        self.tabwatch.register_parser("Python",PythonParser(window))
        self.tabwatch.register_parser("Ruby",RubyParser())
        self.tabwatch.register_parser("Diff",DiffParser())

        htmlParser = geditHTMLParser()
        self.tabwatch.register_parser("HTML",htmlParser)
        self.tabwatch.register_parser("XML",htmlParser)

    def activate(self, window):

        # create the browser pane
        panel = window.get_side_panel()
        image = gtk.Image()
        drawable = gtk.gdk.get_default_root_window()
        colormap = drawable.get_colormap()
        pixmap, mask = gtk.gdk.pixmap_colormap_create_from_xpm_d(drawable, colormap, None, icon)
        image.set_from_pixmap(pixmap, mask)
        self.classbrowser = ClassBrowser(window)
        panel.add_item(self.classbrowser, "Class Browser", image)

        # create the tabwatch to monitor open files in gedit
        self.tabwatch = TabWatch(window, self.classbrowser)

        # store per window data in the window object
        windowdata = { "ClassBrowser" : self.classbrowser,
                       "TabWatch" : self.tabwatch }

        submenu = """
            <ui>
              <menubar name="MenuBar">
                <menu name="SearchMenu" action="Search">
                  <placeholder name="SearchOps_7">
                        <menuitem action="JumpPreviousTag"/>
                        <menuitem action="JumpNextTag"/>
                  </placeholder>
                </menu>
              </menubar>
            </ui>
            """
            
        manager = window.get_ui_manager()
        windowdata["action_group"] = gtk.ActionGroup("GeditClassBrowserPluginActions")
        windowdata["action_group"].add_actions(
         [
            # name, stock id, label, accelerator, tooltip
          ('JumpNextTag', gtk.STOCK_GO_DOWN,_('Jump to next tag'),"<control>e", _("Jump to next tag"), self.next_tag),
             
          ('JumpPreviousTag', gtk.STOCK_GO_UP, _('Jump to previous tag'), "<control><shift>e",_("Jump to previous tag"), self.previous_tag)
         ], 
          
          window)
          
        manager.insert_action_group(windowdata["action_group"], 0)
        windowdata["ui_id"] = manager.new_merge_id ()
        manager.add_ui_from_string(submenu)
        window.set_data("ClassBrowserPluginWindowDataKey", windowdata)
        self.register_parsers(window)
        

    def next_tag(self, action, window):
        windowdata = window.get_data("ClassBrowserPluginWindowDataKey")
        windowdata["ClassBrowser"].jump_to_tag(direction=1)
        
    
    def previous_tag(self, action, window):
        windowdata = window.get_data("ClassBrowserPluginWindowDataKey")
        windowdata["ClassBrowser"].jump_to_tag(direction=0)
        

    def deactivate(self, window):
        pane = window.get_side_panel()
        pane.remove_item(self.classbrowser)
        windowdata = window.get_data("ClassBrowserPluginWindowDataKey")
        manager = window.get_ui_manager()
        #manager.remove_ui(windowdata["ui_id"])
        manager.remove_action_group(windowdata["action_group"])
        

    def update_ui(self, window):
        view = window.get_active_view()
        windowdata = window.get_data("ClassBrowserPluginWindowDataKey")

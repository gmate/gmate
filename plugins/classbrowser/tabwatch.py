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

import gtk
import options

#-------------------------------------------------------------------------------        
class TabWatch:
    """ Monitor the tabs in gedit to find out when documents get opened or
        changed. """

    def __init__(self, window, classbrowser):
        self.browser = classbrowser   
        self.geditwindow = window
        self.geditwindow.connect("tab_added",self.__tab_added_or_activated)
        self.geditwindow.connect("tab_removed",self.__tab_removed)
        self.geditwindow.connect("active_tab_changed",self.__tab_added_or_activated)
        
        self.openfiles = []
        self.currentDoc = None
        self.languageParsers = {}
        self.defaultparser = None
    
    def register_parser(self, mimetype, parser):
        """ register a new class parser to use with a certain mime type.
            language -- a string (see gtksourceview languages for reference)
            parser -- an instance of ClassParserInterface """
        self.languageParsers[mimetype] = parser  
    
    def __tab_added_or_activated(self, window, tab):
        self.__register(tab.get_document(),tab)
        doc = self.geditwindow.get_active_document()
        if doc != self.currentDoc: self.__update()

    def __tab_removed(self, window, tab):
        self.__unregister(tab.get_document())

        doc = self.geditwindow.get_active_document()
        if doc != self.currentDoc: self.__update()

    def __register(self, doc, tab):
        if doc is None: return
        uri = doc.get_uri()
        if uri in self.openfiles: return
        self.openfiles.append(uri)
        tab.get_view().connect_after("notify",self.browser.on_cursor_changed)
        tab.get_view().connect_after("move-cursor",self.browser.update_cursor)

        #doc.set_modified(True)
        doc.connect("modified-changed",self.__update)
        if options.singleton().verbose: print "added:",uri

    def __unregister(self, doc):
        if doc is None: return
        uri = doc.get_uri()
        if uri not in self.openfiles: return
        self.openfiles.remove(uri)  
        #if options.singleton().verbose: print "removed:",uri

    def __update(self, *args):
        doc = self.geditwindow.get_active_document()
        if doc:
                
            lang = doc.get_language()
            parser = self.defaultparser
            if lang:
                m = lang.get_name()
                if m in self.languageParsers: parser = self.languageParsers[m]

            if options.singleton().verbose:
                print "parse %s (%s)"%(doc.get_uri(),parser.__class__.__name__)
            model = parser.parse(doc)
            self.browser.set_model(model, parser)
            self.currentDoc = doc

        else:
            self.browser.set_model(None)

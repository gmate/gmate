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

class bookmark_list(object):
    
    def __init__(self, config):
        self._list = {}
        
        self._config = config

        # Load bookmarks from configuration
        sections = config.sections()

        if config.has_section("common"):
            index = sections.index("common")
            del sections[index]
        
        # Create an empty store for the documents that have no bookmarks yet
        self._empty_store = gtk.ListStore(int, str)
        
        for sec in sections:
            store = gtk.ListStore(int, str)
            
            self._list[sec] = {"store": store, "iters": {}}
            
            for line in config.options(sec):
                comment = config.get(sec, line)
                self._list[sec]["iters"][int(line)] = store.append([int(line), comment])
            
            # Setup sorting
            store.set_sort_func(0, self._line_sort)
            store.set_sort_column_id(0, gtk.SORT_ASCENDING)
            
    def get_store(self, uri): # Gets tree store for an uri
        try:
            return self._list[uri]["store"]
        except:
            return self._empty_store
        
    def get_iters(self, uri):
        try:
            return self._list[uri]["iters"]
        except:
            return {}
        
    def add(self, uri, line, source, comment = ""): # Adds a line for an uri (returns True on success)
        exists = self.exists(uri, line)
        
        if comment == "":
            content = source
        else:
            content = comment
        
        if not exists:
            if self._list.has_key(uri):
                self._list[uri]["iters"][line] = self._list[uri]["store"].append([line, content])
            else:
                store = gtk.ListStore(int, str)
                self._list[uri] = {"store": store, "iters": {line: store.append([line, content])}}    
                
                # Setup sorting
                store.set_sort_func(0, self._line_sort)
                store.set_sort_column_id(0, gtk.SORT_ASCENDING)

                # Create uri section in configuration
                self._config.add_section(uri)
            
            # Upadate configuration
            self._config.set(uri, str(line), comment)
        
        return not exists
        
    def delete(self, uri, line = None): # Deletes a line or an entire uri (returns True on success)
        if line:
            exists = self.exists(uri, line)
            
            if exists:
                self._list[uri]["store"].remove(self._list[uri]["iters"][line])
                del self._list[uri]["iters"][line]
                
                # Upadate configuration
                self._config.remove_option(uri, str(line))
                
            return exists
        else:
            try:
                del self._list[uri]
                
                # Upadate configuration
                self._config.remove_section(uri)
                
                return True
            except:
                return False
        
    def exists(self, uri, line): # Returns True if there is a line exists in an uri
        try:
            return self._list[uri]["iters"][line]
        except:
            return False
        
    def toggle(self, uri, line, source, comment = ""): # Adds or removes a line for an uri
        if self.exists(uri, line):
            self.delete(uri, line)
            return False
        else:
            self.add(uri, line, source, comment)
            return True

    def update(self, uri, offset, cur_line, end_line):
        if self._list.has_key(uri):
            iters = {}
            
            keys = self._list[uri]["iters"].keys()
            
            for line in keys:
                row = self._list[uri]["iters"][line]
                
                comment = self._config.get(uri, str(line))
                self._config.remove_option(uri, str(line))

                if line < cur_line:
                    self._list[uri]["store"].set_value(row, 0, line)
                    iters[line] = row
                    
                    # Upadate configuration
                    self._config.set(uri, str(line), comment)
                    
                elif (end_line < 0 and line >= cur_line) or (end_line >= 0 and line > end_line):
                    line = line-offset
                    self._list[uri]["store"].set_value(row, 0, line)
                    iters[line] = row
                    
                    # Upadate configuration
                    self._config.set(uri, str(line), comment)
                    
                else:
                    self._list[uri]["store"].remove(row)
                    
            self._list[uri]["iters"] = iters
            
            return True 
        else:
            return False

    def _line_sort(self, model, line1, line2):
        val1 = model.get_value(line1, 0)
        val2 = model.get_value(line2, 0)

        if val1 < val2:
	        return -1
        if val1 == val2:
	        return 0
        return 1
        
# ex:ts=4:et:

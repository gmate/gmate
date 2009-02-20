#/usr/bin/env python
#
# Copyright (C) 2008  Christian Hergert <chris@dronelabs.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License or the
# GNU Lesser General Public License as published by the 
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gio
import gobject
import glib
import os
import time

_NAME_ATTRIBUTE="standard::display-name"
_TYPE_ATTRIBUTE="standard::type"

class WalkerTexasRanger(object):
    def __init__(self, onResult, onClear=None, onFinish=None):
        self._onResult  = onResult
        self._onClear   = onClear
        self._onFinish  = onFinish
        self._enumerate = gio.Cancellable()
        self._userData  = None
    
    def _result(self, *args, **kwargs):
        if callable(self._onResult):
            userData = self._userData and [self._userData] or [None]
            apply(self._onResult, [self] + list(args) + userData, kwargs)
    
    def _clear(self, *args, **kwargs):
        if callable(self._onClear):
            userData = self._userData and [self._userData] or [None]
            apply(self._onClear, [self] + list(args) + userData, kwargs)
    
    def _finish(self, *args, **kwargs):
        if callable(self._onFinish):
            userData = self._userData and [self._userData] or [None]
            apply(self._onFinish, [self] + list(args) + userData, kwargs)
    
    def cancel(self):
        """
        Cancels a running query.
        """
        self._stamp = None
        self._enumerate.cancel()
        
    def walk(self, query, ignoredot = False, maxdepth = -1, user_data = None):
        # cancel any existing request
        self._enumerate.cancel()
        self._enumerate.reset()
        self._userData = user_data
        
        # call the clear callback
        self._clear()
        
        # consider doing query_info_async to determine if this is
        # a directory without potential blocking for slow disks.
        if not query or not os.path.isdir(query):
            False
        
        # build a unique stamp for this query
        stamp = self._stamp = str(time.time()) + query
        
        # build our state and file objects
        # state => (
        #   unique query stamp,
        #   dirs to traverse,
        #   ignore dot files/dirs
        #   max depth to traverse
        #   current traversal depth
        # )
        state = [stamp, [], ignoredot, maxdepth, 0]
        vfs = gio.vfs_get_default()
        gfile = vfs.get_file_for_path(query)
        
        # asynchronously get the list of children
        attrs = ','.join([_NAME_ATTRIBUTE, _TYPE_ATTRIBUTE])
        gfile.enumerate_children_async(attrs, self._walk, 0, 0,
                                       self._enumerate, state)
        
        return True
        
    def _walk(self, gfile, result, state):
        stamp, todo, ignoredot, maxdepth, curdepth = state
        
        # return immediately if we have been End-Of-Lifed
        if stamp != self._stamp:
            return
        
        try:
            children = gfile.enumerate_children_finish(result)
            dirname = gfile.get_path()
            dirs = []
            files = []
            
            # iterate the children found
            for child in children:
                childname = child.get_attribute_string(_NAME_ATTRIBUTE)
                childtype = child.get_attribute_uint32(_TYPE_ATTRIBUTE)
                
                # keep track of dirs and files for callback.
                # add directories to traverse if needed.
                if childtype == gio.FILE_TYPE_DIRECTORY:
                    if childname.startswith('.') and ignoredot:
                        continue
                    
                    # only add this to the todo list if its within
                    # our depth limit.
                    if maxdepth < 0 or curdepth + 1 <= maxdepth:
                        fullpath = os.path.join(gfile.get_path(), childname)
                        todo.insert(0, (fullpath, curdepth + 1))
                    
                    dirs.insert(0, childname)
                elif childtype == gio.FILE_TYPE_REGULAR:
                    if childname.startswith('.') and ignoredot:
                        continue
                    files.insert(0, childname)
            
            self._result(dirname, dirs, files)
            children.close()

            del children
        except gio.Error, ex:
            pass
        
        del gfile
        
        # we are done if no more dirs are left to traverse.
        # call finish and return.
        if not len(todo):
            self._finish()
            return
        
        # perform our next enumerate which calls this same method
        nextpath, nextdepth = todo.pop()
        state[-1] = nextdepth
        next = gio.file_parse_name(nextpath)
        attrs = ','.join([_NAME_ATTRIBUTE, _TYPE_ATTRIBUTE])
        next.enumerate_children_async(attrs, self._walk, 0, 0,
                                      self._enumerate, state)
        
if __name__ == '__main__':
    import gtk
    import pprint
    
    def p(walker, dirname, dirs, files, user):
        assert(user != None)
        print '=' * 76
        print dirname
        if dirs:
            print '  dirs:'
            print '    ' + '\n    '.join(dirs)
            print
        if files:
            print '  files:'
            print '    ' + '\n    '.join(files)
            print
    
    walker = WalkerTexasRanger(p, None, lambda *a: gtk.main_quit())
    #walker.walk('/home/chergert')
    
    def newwalk():
        walker.walk('/home/chergert', True, 2, "user data")
        return False
    
    # start a new search 50 mili later
    glib.timeout_add(50, newwalk)
    
    gtk.main()

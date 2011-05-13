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


class ClassParserInterface:
    """ An abstract interface for class parsers.
    
    A class parser monitors gedit documents and provides a gtk.TreeModel
    that contains the browser tree. Elements in the browser tree are reffered
    to as 'tags'.
    
    There is always only *one* active instance of each parser. They are created
    at startup (in __init__.py).
    
    The best way to implement a new parser is probably to store custom python
    objects in a gtk.treestore or gtk.liststore, and to provide a cellrenderer
    to render them.
    """
    
    #------------------------------------- methods that *have* to be implemented
    
    def parse(self, geditdoc): 
        """ Parse a gedit.Document and return a gtk.TreeModel. 
        
        geditdoc -- a gedit.Document
        """
        pass        
        
        
    def cellrenderer(self, treeviewcolumn, cellrenderertext, treemodel, it):
        """ A cell renderer callback function that controls what the text label
        in the browser tree looks like.
        See gtk.TreeViewColumn.set_cell_data_func for more information. """
        pass
        
    #------------------------------------------- methods that can be implemented
   
    def pixbufrenderer(self, treeviewcolumn, cellrendererpixbuf, treemodel, it):
        """ A cell renderer callback function that controls what the pixmap next
        to the label in the browser tree looks like.
        See gtk.TreeViewColumn.set_cell_data_func for more information. """
        cellrendererpixbuf.set_property("pixbuf",None)
        
        
    def get_tag_position(self, model, doc, path):
        """ Return the position of a tag in a file. This is used by the browser
        to jump to a symbol's position.
        
        Returns a tuple with the full file uri of the source file and the line
        number of the tag or None if the tag has no correspondance in a file.
        
        model -- a gtk.TreeModel (previously provided by parse())
        path -- a tuple containing the treepath
        """
        pass
    
        
    def get_menu(self, model, path):
        """ Return a list of gtk.Menu items for the specified tag. 
        Defaults to an empty list
        
        model -- a gtk.TreeModel (previously provided by parse())
        path -- a tuple containing the treepath
        """
        return []

    
    def current_line_changed(self, model, doc, line):
        """ Called when the cursor points to a different line in the document.
        Can be used to monitor changes in the document.
        
        model -- a gtk.TreeModel (previously provided by parse())
        doc -- a gedit document
        line -- int
        """
        pass
  
        
    def get_tag_at_line(self, model, doc, linenumber):
        """ Return a treepath to the tag at the given line number, or None if a
        tag can't be found.
        
        model -- a gtk.TreeModel (previously provided by parse())
        doc -- a gedit document
        linenumber -- int
        """
        pass
        

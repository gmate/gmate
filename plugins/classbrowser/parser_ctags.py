# Copyright (C) 200-2008 Frederic Back (fredericback@gmail.com)
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
import tempfile
import os
from subprocess import *
import gnomevfs

from parserinterface import *
import imagelibrary
import options
import re



class CTagsParser( ClassParserInterface ):
    """ A class parser that uses ctags.
    
    Note that this is a very rough and hackish implementation.
    Feel free to improve it.
    
    See http://ctags.sourceforge.net for more information about exuberant ctags,
    and http://ctags.sourceforge.net/FORMAT for a description of the file format.
    """
    
    def __init__(self):
        self.model = None
        self.document = None
        self.parse_all_files = False
        self.debug = False


    def parse(self, doc):
        """ Create a gtk.TreeModel with the tags of the document.
         
        The TreeModel contains:
           token name, source file path, line in the source file, type code

        If the second str contains an empty string, it means that
        the element has no 'physical' position in a file (see get_tag_position)   """

        self.model = gtk.TreeStore(str,str,int,str) # see __parse_to_model
        self.model.set_sort_column_id(2,gtk.SORT_ASCENDING)
        self.document = doc
        
        if os.system("ctags --version >/dev/null") != 0:
            self.model.append( None, ["Please install ctags!","",0,""] )
            return self.model
        else:
            self._parse_doc_to_model()
            return self.model
        
        
    def _generate_tagfile_from_document(self, doc, options = "-n"):
        
        try:
            # make sure this is a local file (ie. not via ftp or something)
            if doc.get_uri()[:4] != "file": return None
        except: return None
    
        docpath = doc.get_uri_for_display()
	if not os.path.isfile(docpath):
	    # don't parse the file if it doesn't exist
	    return None
        path, filename = os.path.split(docpath)
        if not self.parse_all_files:
            if filename.find(".") != -1:
                arg = self.shell_escape(path + os.sep + filename[:filename.rfind(".")]) + ".*"
            else:
                arg = self.shell_escape(docpath)
        else:
            arg = self.shell_escape(path) + os.sep + "*.*"       
            
        if filename.find(".vala") != -1:
             return self._generate_tagfile(docpath, "-n --language-force=C#")                
        else:         
             return self._generate_tagfile(arg,options)
    
    
    def _generate_tagfile(self, filestr, options = "-n"):
        """ filestr is a string, could be *.* or explicit paths """

        # create tempfile
        h, tmpfile = tempfile.mkstemp()
        os.close(h)
        
        # launch ctags
        command = "ctags %s -f \"%s\" %s"%(options,tmpfile,filestr)
        os.system(command)
        
        return tmpfile

        
    def _parse_doc_to_model(self):
        """ Parse the given document and write the tags to a gtk.TreeModel.
        
        The parser uses the ctags command from the shell to create a ctags file,
        then parses the file, and finally populates a treemodel. """
        # refactoring noise    
        doc = self.document
        ls = self.model        
        ls.clear()
        tmpfile = self._generate_tagfile_from_document(doc)
        if tmpfile is None: return ls
        
        # A list of lists. Matches the order found in tag files.
        # identifier, path to file, line number, type, and then more magical things
        tokenlist = [] 
        h = open(tmpfile)
        for r in h.readlines():
            tokens = r.strip().split("\t")
            if tokens[0][:2] == "!_": continue

            # convert line numbers to an int
            tokens[2] =  int(filter( lambda x: x in '1234567890', tokens[2] ))
            
            # prepend container elements, append member elements. Do this to
            # make sure that container elements are created first.
            if self._is_container(tokens): tokenlist = [tokens] + tokenlist
            else: tokenlist.append(tokens)
        h.close()

        # add tokens to the treestore---------------------------------------
        containers = { None: None } # keep dict: token's name -> treeiter
        
        # iterate through the list of tags, 
        # Note: Originally sorted by line number, bit it did break some
        # formatting in c
        for tokens in tokenlist:
        
            # skip enums
            #if self.__get_type(tokens) in 'de': continue
        
            # append current token to parent iter, or to trunk when there is none
            parent = self._get_parent(tokens)
            
            if parent in containers: node = containers[parent]
            else:
                # create a dummy element in case the parent doesn't exist
                node = ls.append( None, [parent,"",0,""] )
                containers[parent] = node
            
            # escape blanks in file path
            tokens[1] = str( gnomevfs.get_uri_from_local_path(tokens[1]) )
            
            # make sure tokens[4] contains type code
            if len(tokens) == 3: tokens.append("")
            else: tokens[3] = self.__get_type(tokens)
            
            # append to treestore
            it = ls.append( node, tokens[:4] )
            
            # if this element was a container, remember its treeiter
            if self._is_container(tokens):
                containername = self._get_container_name(tokens)
                containers[ containername ] = it
            
        # remove temp file
        os.remove(tmpfile)
        
        
    def shell_escape(self, filename):
        return re.sub(r"([ \"'\\\$])", '\\\\\\1', filename)
    
    
    def get_tag_position(self, model, path):
        filepath = model.get_value( model.get_iter(path), 1 )
        linenumber = model.get_value( model.get_iter(path), 2 )
        if filepath == "": return None
        return filepath, linenumber


    def get_tag_at_line(self, model, doc, linenumber):
        """ Return a treepath to the tag at the given line number, or None if a
        tag can't be found.
        """

        if doc is None: return
        
        self.minline = -1
        self.tagpath = None
            
        def loopfunc(model, path, it):
            if model.get_value(it,1) != doc.get_uri(): return
            l = model.get_value(it,2)
            if l >= self.minline and l <= linenumber+1:
                self.tagpath = path
                self.minline = l
        
        # recursively loop through the treestore
        model.foreach(loopfunc)
        
        if self.tagpath is None:
            it = model.get_iter_root()
            return model.get_path(it)
        
        return self.tagpath
        
        
    def get_menu(self, model, path):
        m1 = gtk.CheckMenuItem("Parse _All Files")
        m1.set_active(self.parse_all_files)
        m1.connect("toggled", lambda w: self.__set_parse_all_files_option(w.get_active()) )
        m2 = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        m2.connect("activate", lambda w: self._parse_doc_to_model() )
        return [m1,m2]
        
        
    def __set_parse_all_files_option(self, onoff):
        self.parse_all_files = onoff
        self.__parse_doc_to_model()
        
        
    def __get_type(self, tokrow):
        """ Returns a char representing the token type or False if none were found.

        According to the ctags docs, possible types are:
            c    class name
            d    define (from #define XXX)
            e    enumerator
            f    function or method name
            F    file name
            g    enumeration name
            m    member (of structure or class data)
            p    function prototype
            s    structure name
            t    typedef
            u    union name
            v    variable        
        """
        if len(tokrow) == 3: return
        for i in tokrow[3:]:
            if len(i) == 1: return i # most common case: just one char
            elif i[:4] == "kind": return i[5:]
        return ' '  
        
        
        
    #----------------------------------------------- related to container tags
        
    def _get_container_name(self, tokrow):
        """ Usually, we can assume that the parent's name is the same
            as the name of the token. In some cases (typedefs), this
            doesn't work (see Issue 13) """
        
        if self.__get_type(tokrow) == "t":
            try:
                t = tokrow[4]
                a = t.split(":")
                return a[ len(a)-1 ]
            except:
                pass
        return tokrow[0]
    
        
    def _is_container(self, tokrow):
        """ class, enumerations, structs and unions are considerer containers.
            See Issue 13 for some issues we had with this.
        """
        if self.__get_type(tokrow) in 'cgsut': return True
        return False
        
        
    def _get_parent(self, tokrow):
        if len(tokrow) == 3: return
        # Iterate through all items in the tag.
        # TODO: Not sure if needed
        for i in tokrow[3:]: 
            a = i.split(":")
            if a[0] in ("class","struct","union","enum"): 
                return a[1]
        return None
        
        
    #----------------------------------------------- cell renderers

    def cellrenderer(self, column, ctr, model, it):
        i = model.get_value(it,0)
        ctr.set_property("text", i)
        elements = {
            "c":"class",
            "f":"function",
            "m":"member",
            "e":"enumerator",
            "d":"define",
        }
        i = model.get_value(it,3)
        try: colour = options.singleton().colours[ elements[i] ]
        except: colour = gtk.gdk.Color(0,0,0)
        ctr.set_property("foreground-gdk", colour)
        
        
    def pixbufrenderer(self, column, crp, model, it):
        elements = {
            "c":"class", #class name
            "d":"default", #define (from #define XXX)
            "e":"enum", #enumerator
            "f":"method", #function or method name
            "F":"default", #file name
            "g":"enum", #enumeration name
            "m":"default", #(of structure or class data)
            "p":"default", #function prototype
            "s":"struct", #structure name
            "t":"default", #typedef
            "u":"struct", #union name
            "v":"variable", #variable
            "n":"namespace", #namespace
        }
        try:
            i = model.get_value(it,3)
            icon = elements[i]
        except:
            icon = "default"
        crp.set_property("pixbuf",imagelibrary.pixbufs[icon])
        

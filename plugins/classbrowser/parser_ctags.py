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
import tempfile
import os
import gnomevfs

from parserinterface import *
import imagelibrary
import options

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


    def parse(self, doc):
        """ Create a gtk.TreeModel with the tags of the document.

        The TreeModel contains:
           token name, source file path, line in the source file, type code

        If the second str contains an empty string, it means that
        the element has no 'physical' position in a file (see get_tag_position)
        """

        self.model = gtk.TreeStore(str,str,int,str) # see __parse_to_model
        self.document = doc
        self.__parse_doc_to_model()
        return self.model


    def __parse_doc_to_model(self):
        """ Parse the given document and write the tags to a gtk.TreeModel.

        The parser uses the ctags command from the shell to create a ctags file,
        then parses the file, and finally populates a treemodel.
        """

        # refactoring noise
        doc = self.document
        ls = self.model
        ls.clear()

        # make sure this is a local file (ie. not via ftp or something)
        try:
            if doc.get_uri()[:4] != "file": return ls
        except:
            return

        docpath = doc.get_uri_for_display()
        path, filename = os.path.split(docpath)
        if filename.find(".") != -1:
            arg = path + os.sep + filename[:filename.rfind(".")] + ".*"
        else:
            arg = docpath

        # simply replacing blanks is the best variant because both gnomevfs
        # and the fs understand it.
        arg = arg.replace(" ","\ ")

        # create tempfile
        h, tmpfile = tempfile.mkstemp()

        # launch ctags
        command = "ctags -n -f %s %s"%(tmpfile,arg)
        os.system(command)

        # print "command:",command

        # create list of tokens from the ctags file-------------------------

        # A list of lists. Matches the order found in tag files.
        # identifier, path to file, line number, type, and then more magical things
        tokenlist = []

        h = open(tmpfile)
        enumcounter = 0
        for r in h.readlines():
            tokens = r.strip().split("\t")
            if tokens[0][:2] == "!_": continue

            # convert line numbers to an int
            tokens[2] =  int(filter( lambda x: x in '1234567890', tokens[2] ))

            # prepend container elements, append member elements. Do this to
            # make sure that container elements are created first.
            if self.__is_container(tokens): tokenlist = [tokens] + tokenlist
            else: tokenlist.append(tokens)

            # hack: remember the number of enums without parents for later grouping
            if self.__get_type(tokens) == 'e' and self.__get_parent(tokens) == None:
                enumcounter += 1

        # add tokens to the treestore---------------------------------------
        containers = { None: None } # keep dict: token's name -> treeiter

        #if enumcounter > 0:
        #    node = ls.append( None, ["Enumerators","",0,""] )
        #    containers["Enumerators"] = node

        # used to sort the list of tokens by file, then by line number
        def cmpfunc(a,b):
            # by filename
            #if a[1] < b[1]: return -1
            #if a[1] > a[1]: return 1

            # by line number
            if a[2] < b[2]: return -1
            if a[2] > b[2]: return 1
            return 0


        # iterate through the list of tags, sorted by their line number
        # a token is a list. Order matches tag file order (name,path,line,type,...)
        for tokens in sorted(tokenlist,cmpfunc):

            # skip enums
            if self.__get_type(tokens) in 'de': continue

            #print self.__get_type(tokens),tokens[0],self.__get_parent(tokens)

            # append current token to parent iter, or to trunk when there is none
            parent = self.__get_parent(tokens)

            # hack: group enums without parents:
            if parent is None and self.__get_type(tokens) == 'e': parent = "Enumerators"

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

            # if this element was a container, remember it's treeiter
            if self.__is_container(tokens): containers[tokens[0]] = it

        # remove temp file
        os.remove(tmpfile)

        #print "------------------"



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
            if model.get_value(it,1) != doc.get_uri_for_display(): return
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
        m = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        m.connect("activate", lambda w: self.__parse_doc_to_model() )
        return [m]


    def __get_type(self, tokrow):
        """ Returns a char representing the token type or False if none were found.

        According to the ctags docs, possible types are:
		c	class name
		d	define (from #define XXX)
		e	enumerator
		f	function or method name
		F	file name
		g	enumeration name
		m	member (of structure or class data)
		p	function prototype
		s	structure name
		t	typedef
		u	union name
		v	variable
        """
        if len(tokrow) == 3: return
        for i in tokrow[3:]:
            if len(i) == 1: return i # most common case: just one char
            elif i[:4] == "kind": return i[5:]
        return ' '

    def __is_container(self, tokrow):
        """ class, enumerations, structs and unions are considerer containers """
        if self.__get_type(tokrow) in 'cgsu': return True
        return False

    def __get_parent(self, tokrow):
        if len(tokrow) == 3: return
        for i in tokrow[3:]:
            if i[:5] == "class": return i[6:]
            if i[:6] == "struct": return i[7:]
            if i[:5] == "union": return i[6:]
        return None

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
            "d":"define", #define (from #define XXX)
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
        }

        try:
            i = model.get_value(it,3)
            icon = elements[i]
        except:
            icon = "default"

        crp.set_property("pixbuf",imagelibrary.pixbufs[icon])

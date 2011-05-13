# Copyright (C) 2007 Frederic Back (fredericback@gmail.com)
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

"""

TODO

[1]-----------------------------------------------------------------------------

    The getTokenBackwards method is crap: It will stop as soon as it finds
    certain caracters (";"), but those may be enclosed in "", in ''
    or in comments, and therefore be legitimate.

    It would be better to keep a string in __get_brackets...

[2]-----------------------------------------------------------------------------

    __get_brackets() should skip everything enclosed in "" or ''.

[3]-----------------------------------------------------------------------------

    __get_brackets() should skip comments: c and c++ style
    
[4]-----------------------------------------------------------------------------

    what about php beginnings and endings? Should skip non-php parts
    

"""

import gtk
import pango
import options
import gobject
from parserinterface import ClassParserInterface
import imagelibrary

#---------------------------------------------------------------------------
class Token:

    def __init__(self,t):
        self.type = t
        self.name = None
        self.params = None
        self.visibility = None

        self.uri = None
        self.start = None
        self.end = None

        self.parent = None
        self.children = [] # a list of nested tokens

    def append(self, child):
        child.parent = self
        self.children.append(child)
        
    def __str__(self):
        return str(self.type) +" " +str(self.name)


#---------------------------------------------------------------------------
class _DummyToken:

    def __init__(self):
        self.parent = None
        self.children = [] # a list of nested tokens
        
    def append(self, child):
        child.parent = self
        self.children.append(child)
        
        
#---------------------------------------------------------------------------    
class CStyleCodeParser( ClassParserInterface ):
    """ This clases provides the basic functionality for the new PHP parser """

    def __init__(self):
        pass
   
   
    def getTokenFromChunk(self, chunk):
        """ Subclasses should implement this """
        pass
        
        
    def getTokenBackwards(self, string, position ):
        """ Iterate a string backwards from a given position to get token
            Example: calling ("one two three",8,2) would return ["two",one"] """ 
        
        # first step: get chunk where definition must be located
        # get substring up to a key character
        i = position
        while i > 0:
            i-=1
            if string[i] in ";}{/": # "/" is for comment endings
                break;
        
        # remove dirt
        chunk = string[i:position+1].strip()
        chunk = chunk.replace("\n"," ");
        chunk = chunk.replace("\r"," ");
        chunk = chunk.replace("\t"," ");
        
        return self.getTokenFromChunk(chunk)
        
        
    def parse(self, doc):
        text = doc.get_text(*doc.get_bounds())
        root = self.__get_brackets(text,doc.get_uri())
        self.__browsermodel = gtk.TreeStore(gobject.TYPE_PYOBJECT)
        for child in root.children: self.__appendTokenToBrowser(child,None)
        return self.__browsermodel
        
        
    def get_tag_position(self, model, path):
        tok = model.get_value( model.get_iter(path), 0 )
        try: return tok.uri, tok.start+1
        except: pass


    def cellrenderer(self, column, ctr, model, it):
        """ Render the browser cell according to the token it represents. """
        tok = model.get_value(it,0)
        name = tok.name
        colour = options.singleton().colours[ "function" ]
        if tok.type == "class":
            name = "class "+tok.name
            colour = options.singleton().colours[ "class" ]
        ctr.set_property("text", name)
        ctr.set_property("foreground-gdk", colour)


    def pixbufrenderer(self, column, crp, model, it):
        tok = model.get_value(it,0)
        if tok.type == "class":
            icon = "class"
        else:
            if tok.visibility == "private": icon = "method_priv"
            elif tok.visibility == "protected": icon = "method_prot"
            else: icon = "method"
        crp.set_property("pixbuf",imagelibrary.pixbufs[icon])


    def __appendTokenToBrowser(self, token, parentit ):
        if token.__class__ == _DummyToken: return
        it = self.__browsermodel.append(parentit,(token,))
        token.path = self.__browsermodel.get_path(it)
        for child in token.children:
            self.__appendTokenToBrowser(child, it)

    def __get_brackets(self,string,uri):
        verbose = False
        root = Token("root")
        parent = root
        ident = 0
        
        if verbose: print "-"*80
        
        line = 0 # count lines
        for i in range(len(string)-1):
        
            c = string[i]
            
            if c == "{": #------------------------------------------------------
            
                # get a token from the chunk of code preceding the bracket
                token = self.getTokenBackwards( string, i )
                
                if token:
                    # assign line number and uri to the token
                    token.uri = uri
                    token.start = line
                else:
                    # dummy token for empty brackets. Will not get added to tree.
                    token = _DummyToken()
                    
                # append the token to the tree
                parent.append(token)
                parent = token

                if verbose: print ident*"  "+"{",token
                ident += 1
                
                
            elif c == "}": #----------------------------------------------------
                ident -= 1
                if parent != root:
                    parent.end = line
                    parent = parent.parent
                    
                if verbose: print ident*"  "+"}",parent
                
            elif c == "\n":
                line += 1
                
        return root



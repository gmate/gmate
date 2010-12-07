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
import gobject
import pango
import os
import re
import options
from parserinterface import ClassParserInterface
import imagelibrary

#===============================================================================

def functionTokenFromString(string):
    """ Parse a string containing a function or class definition and return
        a tuple containing information about the function, or None if the
        parsing failed.

        Example: 
            "#def foo(bar):" would return :
            {'comment':True,'type':"def",'name':"foo",'params':"bar" } """

    try:
        e = r"([# ]*?)([a-zA-Z0-9_]+)( +)([a-zA-Z0-9_]+)(.*)"
        r = re.match(e,string).groups()
        token = Token()
        token.comment = '#' in r[0]
        token.type = r[1]
        token.name = r[3]
        token.params = r[4]
        token.original = string
        return token
    except: return None # return None to skip if unable to parse


#===============================================================================

class Token:
    """ Rules: 
            type "attribute" may only be nested to "class"
    """

    def __init__(self):
        self.type = None # "attribute", "class" or "function"
        self.original = None # the line in the file, unparsed

        self.indent = 0
        self.name = None
        self.comment = False # if true, the token is commented, ie. inactive
        self.params = None   # string containing additional info
        self.expanded = False

        # start and end points (line number)
        self.start = 0
        self.end = 0

        self.pythonfile = None
        self.path = None # save the position in the browser

        self.parent = None
        self.children = [] # a list of nested tokens
        self.attributes = [] # a list of class attributes
        

    def get_endline(self):
        """ Get the line number where this token's declaration, including all
            its children, finishes. Use it for copy operations."""
        if len(self.children) > 0:
            return self.children[-1].get_endline()
        return self.end

        def test_nested():
            pass
            
    def get_toplevel_class(self):
        """ Try to get the class a token is in. """
            
        if self.type == "class":
            return self    

        if self.parent is not None:
            tc = self.parent.get_toplevel_class()
            if tc is None or tc.type == "file": return self #hack
            else: return tc
                
        return None

    def printout(self):
        for r in range(self.indent): print "",
        print self.name,
        if self.parent: print " (parent: ",self.parent.name       
        else: print
        for tok in self.children: tok.printout()

#===============================================================================

class PythonFile(Token):
    """ A class that represents a python file.
        Manages "tokens", ie. classes and functions."""

    def __init__(self, doc):
        Token.__init__(self)
        self.doc = doc
        self.uri = doc.get_uri()
        self.linestotal = 0 # total line count
        self.type = "file"
        if self.uri:
            self.name = os.path.basename(self.uri)
        self.tokens = []

    def getTokenAtLine(self, line):
        """ get the token at the specified line number """
        for token in self.tokens:
            if token.start <= line and token.end > line:
                return token
        return None          

    def parse(self, verbose=True):

        #if verbose: print "parse ----------------------------------------------"
        newtokenlist = []

        indent = 0
        lastElement = None

        self.children = []

        lastToken = None
        indentDictionary = { 0: self, } # indentation level: token

        self.linestotal = self.doc.get_line_count()

        text = self.doc.get_text(*self.doc.get_bounds())
        linecount = -1
        for line in text.splitlines():
            linecount += 1
            lstrip = line.lstrip()
            ln = lstrip.split()
            if len(ln) == 0: continue

            if ln[0] in ("class","def","#class","#def"):

                token = functionTokenFromString(lstrip)
                if token is None: continue
                token.indent = len(line)-len(lstrip) 
                token.pythonfile = self
                
                token.original = line

                # set start and end line of a token. The end line will get set
                # when the next token is parsed.
                token.start = linecount
                if lastToken: lastToken.end = linecount
                newtokenlist.append(token)

                #if verbose: print "appending",token.name,
                if token.indent == indent:
                    # as deep as the last row: append the last e's parent
                    #if verbose: print "(%i == %i)"%(token.indent,indent),
                    if lastToken: p = lastToken.parent
                    else: p = self
                    p.children.append(token)
                    token.parent = p
                    indentDictionary[ token.indent ] = token

                elif token.indent > indent:
                    # this row is deeper than the last, use last e as parent
                    #if verbose: print "(%i > %i)"%(token.indent,indent),
                    if lastToken: p = lastToken
                    else: p = self
                    p.children.append(token)
                    token.parent = p
                    indentDictionary[ token.indent ] = token

                elif token.indent < indent:
                    # this row is shallower than the last
                    #if verbose: print "(%i < %i)"%(token.indent,indent),
                    if token.indent in indentDictionary.keys():
                        p = indentDictionary[ token.indent ].parent
                    else: p = self
                    if p == None: p = self # might happen with try blocks
                    p.children.append(token)
                    token.parent = p

                #if verbose: print "to",token.parent.name
                idx = len(newtokenlist) - 1
                if idx < len(self.tokens):
                    if newtokenlist[idx].original == self.tokens[idx].original:
                        newtokenlist[idx].expanded = self.tokens[idx].expanded
                lastToken = token
                indent = token.indent

            # not a class or function definition
            else: 
                
                # check for class attributes, append to last class in last token
                try:
                    # must match "self.* ="
                    if ln[0][:5] == "self." and ln[1] == "=":
                    
                        # make sure there is only one dot in the declaration
                        # -> attribute is direct descendant of the class
                        if lastToken and ln[0].count(".") == 1:
                            attr = ln[0].split(".")[1]
                            self.__appendClassAttribute(lastToken,attr,linecount)
                        
                except IndexError: pass

        # set the ending line of the last token
        if len(newtokenlist) > 0:
            newtokenlist[ len(newtokenlist)-1 ].end = linecount + 2 # don't ask

        # set new token list
        self.tokens = newtokenlist
        return True

    def __appendClassAttribute(self, token, attrName, linenumber):
        """ Append a class attribute to the class a given token belongs to. """
        
        # get next parent class
        while token.type != "class":
            token = token.parent
            if not token: return   
            
        # make sure attribute is not set yet
        for i in token.attributes:
            if i.name == attrName: return
                     
        # append a new attribute
        attr = Token()
        attr.type = "attribute"
        attr.name = attrName
        attr.start = linenumber
        attr.end = linenumber
        attr.pythonfile = self
        token.attributes.append(attr)
        
#===============================================================================

class PythonParser( ClassParserInterface ):
    """ A class parser that uses ctags.
    
    Note that this is a very rough and hackish implementation.
    Feel free to improve it.
    
    See http://ctags.sourceforge.net for more information about exuberant ctags,
    and http://ctags.sourceforge.net/FORMAT for a description of the file format.
    """
    
    def __init__(self, geditwindow):
        self.geditwindow = geditwindow
        self.pythonfile = None


    def appendTokenToBrowser(self, token, parentit ):
        it = self.__browsermodel.append(parentit,(token,))
        token.path = self.__browsermodel.get_path(it)
        
        # add special subtree for attributes
        if len(token.attributes) > 0:
        
            holder = Token()
            holder.name = "Attributes"
            holder.type = "attribute"
            it2 = self.__browsermodel.append(it,(holder,))
            
            for child in token.attributes   :
                self.__browsermodel.append(it2,(child,))
        
        #if token.parent:
        #    if token.parent.expanded:
        #        self.browser.expand_row(token.parent.path,False)
        #        pass
        
        for child in token.children:
            self.appendTokenToBrowser(child, it)


    def get_menu(self, model, path):
        """ The context menu is expanded if the python tools plugin and
            bicyclerepairman are available. """
    
        menuitems = []
    
        try: tok = model.get_value( model.get_iter(path), 0 )
        except: tok = None
        pt = self.geditwindow.get_data("PythonToolsPlugin")
        tagposition = self.get_tag_position(model,path)
        
        if pt and tok and tagposition:
        
            filename, line = tagposition # unpack the location of the token
            if tok.type in ["def","class"] and filename[:7] == "file://":
            
                print tok.original
            
                # trunkate to local filename
                filename = filename[7:]
                column = tok.original.find(tok.name) # find beginning of function definition
                print filename, line, column
                
                item = gtk.MenuItem("Find References")
                menuitems.append(item)
                item.connect("activate",lambda w: pt.brm.findReferencesDialog(filename,line,column))
            
        return menuitems


    def parse(self, doc):
        """ 
        Create a gtk.TreeModel with the class elements of the document
        
        The parser uses the ctags command from the shell to create a ctags file,
        then parses the file, and finally populates a treemodel.
        """
    
        self.pythonfile = PythonFile(doc)
        self.pythonfile.parse(options.singleton().verbose)
        self.__browsermodel = gtk.TreeStore(gobject.TYPE_PYOBJECT)
        for child in self.pythonfile.children:
            self.appendTokenToBrowser(child,None)
        return self.__browsermodel
        

    def get_tag_position(self, model, path):
        tok = model.get_value( model.get_iter(path), 0 )
        try: return tok.pythonfile.uri, tok.start+1
        except: return None


    def current_line_changed(self, model, doc, line):

        # parse again if line count changed
        if abs(self.pythonfile.linestotal - doc.get_line_count()) > 0:
            if abs(self.pythonfile.linestotal - doc.get_line_count()) > 5:
                if options.singleton().verbose:
                    print "PythonParser: refresh because line dif > 5"
                self.pythonfile.parse()
            else:
                it = doc.get_iter_at_line(line)
                a = it.copy(); b = it.copy()
                a.backward_line(); a.backward_line()
                b.forward_line(); b.forward_line()

                t = doc.get_text(a,b)
                if t.find("class") >= 0 or t.find("def") >= 0:
                    if options.singleton().verbose:
                        print "PythonParser: refresh because line cound changed near keyword"
                    self.pythonfile.parse()
 

    def get_tag_at_line(self, model, doc, linenumber):
        t = self.pythonfile.getTokenAtLine(linenumber)
        #print linenumber,t
        if t: return t.path


    def cellrenderer(self, column, ctr, model, it):

        """ Render the browser cell according to the token it represents. """
        tok = model.get_value(it,0)

        weight = 400
        style = pango.STYLE_NORMAL
        name = tok.name#+tok.params
        colour = options.singleton().colours[ "function" ]

        # set label and colour
        if tok.type == "class":
            name = "class "+name+tok.params
            colour = options.singleton().colours[ "class" ]
            weight = 600
        if tok.comment: name = "#"+name
        if tok.parent:
            if tok.parent.type == "class":
                colour = options.singleton().colours[ "member" ]

        # assing properties
        ctr.set_property("text", name)
        ctr.set_property("style", style)
        ctr.set_property("foreground-gdk", colour)


    def pixbufrenderer(self, column, crp, model, it):
        tok = model.get_value(it,0)

        icon = "method" # for normal defs

        if tok.type == "class":
            icon = "class"
        elif tok.type == "attribute":
            if tok.name[:2] == "__": icon = "field_priv"
            else: icon = "field"
        elif tok.parent:

            if tok.parent.type == "class":
                icon = "method"
                if tok.name[:2] == "__":
                    icon = "method_priv"


        crp.set_property("pixbuf",imagelibrary.pixbufs[icon])

        

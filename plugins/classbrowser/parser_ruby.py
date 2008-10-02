# -*- coding: utf-8 -*-
# Copyright (C) 2006 Frederic Back (fredericback@gmail.com)
# Copyright (C) 2007 Kristoffer Lundén (kristoffer.lunden@gmail.com)
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

def tokenFromString(string):
    """ Parse a string containing a function or class definition and return
        a tuple containing information about the function, or None if the
        parsing failed.

        Example: 
            "#def foo(bar):" would return :
            {'comment':True,'type':"def",'name':"foo",'params':"bar" } """

    try:
        e = r"([# ]*?)([a-zA-Z0-9_]+)( +)([a-zA-Z0-9_\?\!<>\+=\.]+)(.*)"
        r = re.match(e,string).groups()
        token = Token()
        token.comment = '#' in r[0]
        token.type = r[1]
        token.name = r[3]
        token.params = r[4]
        token.original = string
        return token
    except: return None # return None to skip if unable to parse
    
    def test():
        pass

#===============================================================================

class Token:
    def __init__(self):
        self.type = None
        self.original = None # the line in the file, unparsed

        self.indent = 0
        self.name = None
        self.comment = False # if true, the token is commented, ie. inactive
        self.params = None   # string containing additional info
        self.expanded = False

        self.access = "public"

        # start and end points
        self.start = 0
        self.end = 0

        self.rubyfile = None
        self.path = None # save the position in the browser

        self.parent = None
        self.children = []

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

class RubyFile(Token):
    """ A class that represents a ruby file.
        Manages "tokens", ie. classes and functions."""

    def __init__(self, doc):
        Token.__init__(self)
        self.doc = doc
        self.uri = doc.get_uri()
        self.linestotal = 0 # total line count
        self.type = "file"
        self.name = os.path.basename(self.uri)
        self.tokens = []


    def getTokenAtLine(self, line):
        """ get the token at the specified line number """
        for token in self.tokens:
            if token.start <= line and token.end > line:
                return self.__findInnermostTokenAtLine(token, line)
        return None

    def __findInnermostTokenAtLine(self, token, line):
        """" ruby is parsed as nested, unlike python """
        for child in token.children:
            if child.start <= line and child.end > line:
                return self.__findInnermostTokenAtLine(child, line)
        return token


    def parse(self, verbose=True):

        #if verbose: print "parse ----------------------------------------------"
        newtokenlist = []

        self.children = []

        currentParent = self

        self.linestotal = self.doc.get_line_count()

        text = self.doc.get_text(*self.doc.get_bounds())
        linecount = -1
        ends_to_skip = 0
        
        access = "public"
        
        for line in text.splitlines():
            linecount += 1
            lstrip = line.lstrip()
            ln = lstrip.split()
            if len(ln) == 0: continue
            if ln[0] == '#': continue
            
            if ln[0] in ("class","module","def"):
                token = tokenFromString(lstrip)
                if token is None: continue
                token.rubyfile = self
                token.start = linecount
                if token.type == "def":
                    token.access = access
                    
                #print "line",linecount
                #print "name", token.name
                #print "type",token.type
                #print "access",token.access
                #print "to",currentParent.name
                
                currentParent.children.append(token)
                token.parent = currentParent
                currentParent = token
                newtokenlist.append(token)
                
                
                idx = len(newtokenlist) - 1
                if idx < len(self.tokens):
                    if newtokenlist[idx].original == self.tokens[idx].original:
                        newtokenlist[idx].expanded = self.tokens[idx].expanded
                
            elif ln[0] in("begin","while","until","case","if","unless","for"):
                    ends_to_skip += 1
                    
            elif ln[0] in ("attr_reader","attr_writer","attr_accessor"):
                for attr in ln:
                    m = re.match(r":(\w+)",attr)
                    if m:
                        token = Token()
                        token.rubyfile = self
                        token.type = 'def'
                        token.name = m.group(1)
                        token.start = linecount
                        token.end = linecount
                        token.original = lstrip
                        currentParent.children.append(token)
                        token.parent = currentParent
                        newtokenlist.append(token)
            
            elif re.search(r"\sdo(\s+\|.*?\|)?\s*(#|$)", line):
                #print "do",line

                # Support for new style RSpec
                if re.match(r"^(describe|it|before|after)\b", ln[0]):
                    token = Token()
                    token.rubyfile = self
                    token.start = linecount
                    
                    if currentParent.type == "describe":                    
                        if ln[0] == "it":
                            token.name = " ".join(ln[1:-1])
                        else:
                            token.name = ln[0]
                        token.type = "def"
                    elif ln[0] == "describe":
                        token.type = "describe"
                        token.name = " ".join(ln[1:-1])
                    else:
                        continue
                    currentParent.children.append(token)
                    token.parent = currentParent
                    currentParent = token
                    newtokenlist.append(token)

                # Deprectated support for old style RSpec, will be removed later
                elif ln[0] in ("context","specify","setup","teardown","context_setup","context_teardown"):
                    token = Token()
                    token.rubyfile = self
                    token.start = linecount
                    
                    if currentParent.type == "context":                    
                        if ln[0] == "specify":
                            token.name = " ".join(ln[1:-1])
                        else:
                            token.name = ln[0]
                        token.type = "def"
                    elif ln[0] == "context":
                        token.type = "context"
                        token.name = " ".join(ln[1:-1])
                    else:
                        continue
                    currentParent.children.append(token)
                    token.parent = currentParent
                    currentParent = token
                    newtokenlist.append(token)
                else:
                    ends_to_skip += 1
                
            elif ln[0] in ("public","private","protected"):
                if len(ln) == 1:
                    access = ln[0]
                    
            if re.search(r";?\s*end(?:\s*$|\s+(?:while|until))", line):
                if ends_to_skip > 0:
                    ends_to_skip -= 1
                else:
                  token = currentParent
                  #print "end",currentParent.name
                  token.end = linecount
                  currentParent = token.parent
                

        # set new token list
        self.tokens = newtokenlist
        return True


#===============================================================================

class RubyParser( ClassParserInterface ):
    
    def __init__(self):
        self.rubyfile = None


    def appendTokenToBrowser(self, token, parentit ):
        it = self.__browsermodel.append(parentit,(token,))
        token.path = self.__browsermodel.get_path(it)
        #print token.path
        #if token.parent:
        #    if token.parent.expanded:
        #        self.browser.expand_row(token.parent.path,False)
        #        pass
        for child in token.children:
            self.appendTokenToBrowser(child, it)


    def parse(self, doc):
        """ 
        Create a gtk.TreeModel with the class elements of the document
        
        The parser uses the ctags command from the shell to create a ctags file,
        then parses the file, and finally populates a treemodel.
        """
    
        self.rubyfile = RubyFile(doc)
        self.rubyfile.parse(options.singleton().verbose)
        self.__browsermodel = gtk.TreeStore(gobject.TYPE_PYOBJECT)
        for child in self.rubyfile.children:
            self.appendTokenToBrowser(child,None)
        return self.__browsermodel

        
    def __private_test_method(self):
        pass


    def get_tag_position(self, model, path):
        tok = model.get_value( model.get_iter(path), 0 )
        try: return tok.rubyfile.uri, tok.start+1
        except: return None


    def current_line_changed(self, model, doc, line):

        # parse again if line count changed
        if abs(self.rubyfile.linestotal - doc.get_line_count()) > 0:
            if abs(self.rubyfile.linestotal - doc.get_line_count()) > 5:
                if options.singleton().verbose:
                    print "RubyParser: refresh because line dif > 5"
                self.rubyfile.parse()
            else:
                it = doc.get_iter_at_line(line)
                a = it.copy(); b = it.copy()
                a.backward_line(); a.backward_line()
                b.forward_line(); b.forward_line()

                t = doc.get_text(a,b)
                if t.find("class") >= 0 or t.find("def") >= 0:
                    if options.singleton().verbose:
                        print "RubyParser: refresh because line cound changed near keyword"
                    self.rubyfile.parse()
 

    def get_tag_at_line(self, model, doc, linenumber):
        t = self.rubyfile.getTokenAtLine(linenumber)
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
            name = "class "+name
            colour = options.singleton().colours[ "class" ]
            weight = 600
            
        elif tok.type == "module":
            name = "module "+name
            colour = options.singleton().colours[ "namespace" ]
            weight = 600
            
        # new style RSpec
        elif tok.type == "describe":
            name = "describe "+name
            colour = options.singleton().colours[ "namespace" ]
            weight = 600
        
        # Old style RSpec, deprecated    
        elif tok.type == "context":
            name = "context "+name
            colour = options.singleton().colours[ "namespace" ]
            weight = 600
            
        elif tok.type == "def":
            colour = options.singleton().colours[ "member" ]
            
        if tok.comment: name = "#"+name

        # assing properties
        ctr.set_property("text", name)
        ctr.set_property("style", style)
        ctr.set_property("foreground-gdk", colour)


    def pixbufrenderer(self, column, crp, model, it):
        tok = model.get_value(it,0)

        icon = "default"

        if tok.type == "class":
            icon = "class"
        elif tok.type == "module":
            icon = "namespace"
        elif tok.type == "describe":
            icon = "namespace"
        elif tok.type == "context":
            icon = "namespace"
        elif tok.type == "def":
            if tok.access == "public":
                icon = "method"
            elif tok.access == "protected":
                icon = "method_prot"
            elif tok.access == "private":
                icon = "method_priv"
                
        crp.set_property("pixbuf",imagelibrary.pixbufs[icon])

        

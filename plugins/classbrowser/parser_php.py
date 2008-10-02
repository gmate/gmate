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

import gtk
import gobject
from parser_cstyle import Token, CStyleCodeParser
import re


e = r".*?" # anything, but *not greedy*
e+= "(?:(private|protected) +)?" # visibility
e+= "function +(\w+)(\(.*\))" # function declaration
e+= " *\{$" # the tail
RE_FUNCTION = re.compile(e)
RE_CLASS = re.compile(r".*class +(\w+)(?: +extends +(\w+))? *\{$")
        
        
class PHPParser( CStyleCodeParser ):

    def __init__(self):
        pass


    def getTokenFromChunk(self, chunk):
        if chunk.find("function")>-1 or chunk.find("class")>-1:
            
            # third step: perform regular expression to get a token
            match = re.match(RE_FUNCTION,chunk)
            if match:
                t = Token("function")
                t.visibility, t.name, t.params = match.groups()
                #print match.groups()
                return t
                
            else:
                match = re.match(RE_CLASS,chunk)
                if match:
                    t = Token("class")
                    t.name, t.params = match.groups()
                    return t

                else:
                
                    # last step: alert user if a chunk could not be parsed
                    #print "Could not resolve PHP function or class in the following string:"
                    #print chunk
                    
                    pass

        return None
        



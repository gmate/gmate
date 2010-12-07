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


from parser_ctags import *
import re



class ETagsParser( CTagsParser ):
    """ A class parser that uses ctags in etags mode.
    
    See http://ctags.sourceforge.net for more information about exuberant ctags,
    and http://ctags.sourceforge.net/FORMAT for a description of the file format.
    """
    
    def __init__(self):
        CTagsParser.__init__(self)



    def _get_type(self, string):
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

        return "v"


    def _parse_doc_to_model(self):
        
        # refactoring noise    
        doc = self.document
        ls = self.model        
        ls.clear()
        
        #tmpfile = self._generate_tagfile("/var/planissimo.de/include/class.*","-n -e")
        tmpfile = self._generate_tagfile_from_document(doc,"-e")
        h = open(tmpfile)
        
        
        #h = open("/var/planissimo.de/include/tags_e")
        
        next_line_contains_filename = False
        filename = None
        parent_indentations = { 0: None }
        last_indent = 0
        for r in h.readlines():
        
            if next_line_contains_filename:
                filename,size = r.split(",")
                next_line_contains_filename = False
                continue
        
            if r[0] == u'\u000c':
                next_line_contains_filename = True
                continue
            
            indent = len(r) - len(r.lstrip())

            # Row contains: extracted source[007F]name of the tag[0001]linenumber,char_offset
            a = r[0:r.find(u'\u007f')].strip()
            b = r[r.find(u'\u007f')+1:r.find(u'\u0001')]
            c = r[r.find(u'\u0001')+1:-1]
            
            linenumber,char_offset = c.split(",")
            
            # Tokens of the ctags parser are constructed as follows:
            # name, file uri, line number, type code (as used in ctags, see _get_type)
            
            try: filename = str(gnomevfs.get_uri_from_local_path(filename))
            except: pass
            
            token = [b,str(filename),int(linenumber),self._get_type(a)]
            
            parent = None # Indentation is arbitrary
            i = indent-1
            while i > 0:
                try: parent = parent_indentations[i-1]
                except: pass
                if parent: i=0
                i -= 1
            
            #print parent_indentations
            #print indent,parent,token[0]
            #print
            
            newnode = ls.append( parent, token )
            parent_indentations[indent] = newnode
            
            last_indent = indent

        
        h.close()
        os.remove(tmpfile)
        
        
class ETagsParserPHP( ETagsParser ):
    """ This parser is able to recognise php symbols like class, static, etc """
    
    def _get_type(self, string):
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

        # squeeze
        s = re.sub(' +', ' ', string)
        
        
        if s.find("class") >= 0: return "c"
        if s.find("public function") >= 0: return "m"
        if re.search("private(.*)function",s): return "m_priv"
        if re.search("protected(.*)function",s): return "m_prot"
        if re.search("var(.*)\$",s): return "v_pubvar"
        if re.search("private(.*)\$",s): return "v_privvar"
        if re.search("protected(.*)\$",s): return "v_protvar"
        
        if s.find("function") >= 0: return "f"
        return "v"
        
        
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
        try: colour = options.singleton().colours[ elements[i[0]] ]
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
		    "v":"variable", #variable,
		    
		    "v_privvar":"field_priv",
		    "v_protvar":"field_prot",
		    "v_pubvar":"field",
		    "m_prot":"method_prot",
		    "m_priv":"method_priv",
        }

        try:
            i = model.get_value(it,3)
            icon = elements[i]
        except:
            icon = "default"

        crp.set_property("pixbuf",imagelibrary.pixbufs[icon])   
        

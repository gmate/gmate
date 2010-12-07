from parserinterface import ClassParserInterface
from HTMLParser import HTMLParser, HTMLParseError
import gtk

#=================================================================================================

class customParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        # id, description, line, offset, [pixbuf]
        self.ls = gtk.TreeStore( str, str, int, int )
        self.currenttag = None
        
    def handle_starttag(self, tag, attrs):
        
        # construct tagstring 
        tagstring = "<"+tag
        for name, value in attrs:
            if name in ["id","name"]: # append only certain attributes 
                tagstring += " %s=%s"%(name,value)
        tagstring += ">"
        #print tagstring
        
        lineno, offset = self.getpos()
        it = self.ls.append( self.currenttag,(tag,tagstring,lineno,0) )
        print (tag,tagstring,lineno,0)
        self.currenttag = it
        
                  
    def handle_endtag(self, tag):
        
        if self.currenttag:
            t = self.ls.get_value(self.currenttag,0)
            if tag == t:
                #print "</%s>"%tag
                self.currenttag = self.ls.iter_parent(self.currenttag)

#=================================================================================================

class geditHTMLParser( ClassParserInterface ):


    def parse(self, d): 
        parser = customParser()
        try: parser.feed(d.get_text(*d.get_bounds()))
        except HTMLParseError, e:
            print e.lineno, e.offset
            
        return parser.ls  
        
    def cellrenderer(self, treeviewcolumn, ctr, treemodel, it):
        name = treemodel.get_value(it,1)
        ctr.set_property("text", name)
        
    #------------------------------------------- methods that can be implemented
   
    def pixbufrenderer(self, treeviewcolumn, cellrendererpixbuf, treemodel, it):
        """ A cell renderer callback function that controls what the pixmap next
        to the label in the browser tree looks like.
        See gtk.TreeViewColumn.set_cell_data_func for more information. """
        cellrendererpixbuf.set_property("pixbuf",None)
        
        
    def get_tag_position(self, model, path):
        """ Return the position of a tag in a file. This is used by the browser
        to jump to a symbol's position.
        
        Returns a tuple with the full file uri of the source file and the line
        number of the tag or None if the tag has no correspondance in a file.
        
        model -- a gtk.TreeModel (previously provided by parse())
        path -- a tuple containing the treepath
        """
        
        return
    
        
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
        
        #print "="*80
        
        self.lastit = None
        def iterate(model, path, it):
            #print model.get_value(it,2)
            line = model.get_value(it,2)
            if line > linenumber: return True # exit, lastpath contains tag
            self.lastit = it
        
        model.foreach(iterate)
        #print self.lastit, "-----"*20
        return model.get_path(self.lastit)
        
        
        

import os
import pastie
import config
import gtk
import gtk.glade

class Window():

    def __init__(self, gladefile):
        self._glade = gtk.glade.XML( os.path.dirname( __file__ ) + "/" + gladefile )
        self._window = self._glade.get_widget("window")
        self._window.connect("delete_event", self._hide)
        
    def _hide(self, widget, event):
        widget.hide()
        return True
    
    def show(self, dummy=None):
        self._window.show()
        

class PastieWindow(Window):

    def __init__(self,):
        Window.__init__(self, "PasteWindow.glade")
       
        for lang in pastie.LANGS:
            self._glade.get_widget("syntax").append_text(lang)
        
        self._glade.get_widget("syntax").set_active(0) #sets active posision in syntax list
        self._glade.get_widget("ok_button").connect("clicked", self._ok_button)
        self._glade.get_widget("cancel_button").connect("clicked", lambda a: self._window.hide())
        
        self.inform = Inform()
        self.config = config.Configuration()
        
        self.set_from_defaults()
        self.config.call_when_configuration_changes = self.set_from_defaults
     
    def set_from_defaults(self):
        self._glade.get_widget("syntax").set_active(config.SYNTAXES.index(self.config.syntax))
        
        if self.config.private == "True":
            to_set = True
        else:
            to_set = False
        
        self._glade.get_widget("private").set_active(to_set)
        
        
    def _ok_button(self, event=None):
        text = self.get_text()
        combox = self._glade.get_widget("syntax")
        model = combox.get_model()
        active = combox.get_active()
        syntax = model[active][0]
        priv = self._glade.get_widget("private").get_active()
        self._window.hide()
        self._paste(syntax, priv, text, self.config.link)
        
    def paste_defaults(self, bla):
        if self.config.private == "True":
            private = True
        else:
            private = False
            
        self._paste(self.config.syntax, private, self.get_text(), self.config.link)
        
        
    def _paste(self, syntax, priv, text, link):
        "pastes selected text and displays window with link"
        p = pastie.Pastie(text, syntax, priv)
        paste = p.paste()
        if link == "Window":
            self.inform.entry.set_text("please wait")
            self.inform.show() #shows window
            self.inform.entry.set_text(paste)
        else:
            clipboard = gtk.clipboard_get('CLIPBOARD')
            clipboard.set_text(paste)
            clipboard.store()

class Inform(Window):

    def __init__(self):
        Window.__init__(self, "Inform.glade")
        self.entry = self._glade.get_widget("link")
        self._glade.get_widget("ok_button").connect("clicked", lambda a: self._window.hide())


import os
import pastie
import gtk
import gtk.glade

CONFIG_FILE = os.path.dirname( __file__ ) + '/config.pur'

LINKS = ['Clipboard', 'Window']
PRIVATES = ['True', 'False']
SYNTAXES = list(pastie.LANGS) 

class NoConfig(Exception): pass

class ConfigDialog():
    def __init__(self):
        self._glade = gtk.glade.XML( os.path.dirname( __file__ ) + "/Config.glade" )
        self.window = self._glade.get_widget("dialog")
        self._syntax = self._glade.get_widget("syntax")
        self._link = self._glade.get_widget("link")
        self._ok_button = self._glade.get_widget("ok_button")
        self._cancel_button = self._glade.get_widget("cancel_button")
        self._private = self._glade.get_widget("private")
        self.set_syntaxes()
        self.set_links()
        
        self._cancel_button.connect("clicked", self.hide)
    
    def set_syntaxes(self):
        for syntax in SYNTAXES:
            self._syntax.append_text(syntax)
    
    def set_links(self):
        for link in LINKS:
            self._link.append_text(link)
     
    def set_private(self, private):
        if private == "True":
            to_set = True
        else:
            to_set = False
        
        self._private.set_active(to_set)
        
    def set_syntax(self, syntax):
        self._syntax.set_active(SYNTAXES.index(syntax))
    
    def set_link(self, link):
        self._link.set_active(LINKS.index(link))
            
    def get_link(self):
        return self._link.get_model()[self._link.get_active()][0]
    
    def get_syntax(self):
        return self._syntax.get_model()[self._syntax.get_active()][0]

    def get_private(self):
        return self._private.get_active()
    
    def hide(self, widget=None, event=None):
        self.window.hide()
        self.reset()
        return True

    def connect_ok(self, func):
        self._ok_button.connect("clicked", lambda a: func())
    
        
class Configuration():

    def __init__(self):
        self._config_exists = os.access(CONFIG_FILE, os.R_OK)
        self.window = ConfigDialog()
        self.window.connect_ok(self.ok)
        try:
            self.read()
        except NoConfig:
            self.new()
        self.window_set()
        self.window.reset = self.window_set
        self.call_when_configuration_changes = None
        
    def error_dialog(self):
        dialog = gtk.MessageDialog(message_format="Error reading/writing configuration file!", 
                                   buttons = gtk.BUTTONS_OK,
                                   type = gtk.MESSAGE_ERROR )
        dialog.set_title("Error!")
        dialog.connect("response", lambda x, y: dialog.destroy())
        dialog.run()
    
    def read(self):
        if self._config_exists:
            try:
                f = open(CONFIG_FILE, 'rb')
            except:
                self.error_dialog()
            else:
                self.data = f.read()
                self.parse()
            finally:
                f.close()
        else:
            raise NoConfig
           
    def new(self):
        self.syntax = "Plain Text"
        self.link = "Window"
        self.private = "True"
        self.save()
        
    def parse(self):
        array = self.data.split("\n")
        if len(array) < 3:
            self.new()
        else:
          self.syntax = array[0]
          self.link = array[1]
          self.private = array[2]
        try:
            LINKS.index(self.link)
            PRIVATES.index(self.private)
            SYNTAXES.index(self.syntax) 
        except ValueError:
            self.new()
            
    def window_set(self):
        self.window.set_link(self.link)
        self.window.set_syntax(self.syntax)
        self.window.set_private(self.private)
        
    def ok(self):
        self.syntax = self.window.get_syntax()
        self.link = self.window.get_link()
        if self.window.get_private():
            self.private = "True"
        else:
            self.private = "False"
        self.save()
        self.window.hide()
        if self.call_when_configuration_changes:
            self.call_when_configuration_changes()
        
    def save(self):
        try:
            f = open(CONFIG_FILE, 'w')
        except:
            self.error_dialog()
        else:
            f.write("\n".join([self.syntax, self.link, self.private])+"\n")
        finally:
            f.close()
        

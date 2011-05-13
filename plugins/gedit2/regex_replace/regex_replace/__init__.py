import gedit
import gtk
from regexsearchinstance import RegexSearchInstance

class RegexSearch(gedit.Plugin):
    DATA_TAG = "RegexSearchInstance"

    def __init__(self):
        gedit.Plugin.__init__(self)

    def activate(self, window):
        regexsearch_instance = RegexSearchInstance(window)
        window.set_data(self.DATA_TAG, regexsearch_instance)
	
    def deactivate(self, window):
        regexsearch_instance = window.get_data(self.DATA_TAG)
        # regexsearch_instance destroy!?
        window.set_data(self.DATA_TAG, None)
		
    def update_ui(self, window):
        regexsearch_instance = window.get_data(self.DATA_TAG)
        regexsearch_instance.update_ui()

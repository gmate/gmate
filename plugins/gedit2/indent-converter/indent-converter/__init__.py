
import gedit
import gtk
import gconf
from gettext import gettext as _
import re




class IndentConverterWindow:

	def __init__(self, plugin, window):
		self.window = window
		self.plugin = plugin
	
	
	def activate(self):
		self.insert_menu()
		return self
	
	
	def deactivate(self):
		self.remove_menu()
		self.window = None
		self.plugin = None
		self.action_group = None
		return self
	
	
	def update_ui(self):
		view = self.window.get_active_view()
		self.action_group.set_sensitive(bool(view and view.get_editable()))
		return self
	
	
	def insert_menu(self):
		manager = self.window.get_ui_manager()
		self.action_group = gtk.ActionGroup('IndentConverterActions')
		self.action_group.add_actions([
			('TabConvert',   None,             _('Convert Tabs'),           None, None,                     None),
			('SpacesToTabs', gtk.STOCK_INDENT, _('Convert spaces to tabs'), None, _('Convert spaces to tabs'), self.do_spaces_to_tabs),
			('TabsToSpaces', gtk.STOCK_INDENT, _('Convert tabs to spaces'), None, _('Convert tabs to spaces'), self.do_tabs_to_spaces),
		])
		manager.insert_action_group(self.action_group, -1)
		self.ui_id = manager.add_ui_from_string(
		"<ui>\
			<menubar name='MenuBar'>\
				<menu name='EditMenu' action='Edit'>\
					<placeholder name='EditOps_6'>\
						<menu action='TabConvert'>\
							<menuitem action='SpacesToTabs'/>\
							<menuitem action='TabsToSpaces'/>\
						</menu>\
					</placeholder>\
				</menu>\
			</menubar>\
		</ui>")
		return self
	
	
	def remove_menu(self):
		manager = self.window.get_ui_manager()
		manager.remove_ui(self.ui_id)
		manager.remove_action_group(self.action_group)
		manager.ensure_update()
		return self
	
	
	def do_tabs_to_spaces(self, action):
		doc = self.window.get_active_document()
		start, end = doc.get_bounds()
		text = doc.get_text(start, end)
		text = text.expandtabs(self.plugin.tab_size())

		doc.begin_user_action()
		doc.set_text(text)
		doc.end_user_action()
	
	
	def guess_tab_size(self, text):
		def gcd(a, b):
			return a if b == 0 else gcd(b, a % b);
		
		r = re.compile('^ +', re.MULTILINE)
		matches = r.findall(text)
		freq = {} # `key` - length of leading spaces, `value` - it's frequency
		for spaces in matches:
			spaces = len(spaces)
			if spaces in freq:
				freq[spaces] += 1
			else:
				freq[spaces] = 1
		# sort frequencies by value:
		items = [ [i[1], i[0]] for i in freq.items() ]
		items.sort()
		items.reverse()
		items = [i[1] for i in items]
		if len(items) == 0:
			return 0
		elif len(items) == 1:
			return items[0]
		else:
			return gcd(items[0], items[1])
		
		
	def do_spaces_to_tabs(self, action):
		doc = self.window.get_active_document()
		start, end = doc.get_bounds()
		text = doc.get_text(start, end)
		
		tab_size = self.guess_tab_size(text)
		if (tab_size < 2):
			tab_size = self.plugin.tab_size()
		r = re.compile('^(?:' +  (' ' * tab_size) + ')+', re.MULTILINE)
		def replacer(match):
			return '\t' * (len(match.group(0)) / tab_size)
		text = r.sub(replacer, text)
		
		doc.begin_user_action()
		doc.set_text(text)
		doc.end_user_action()




class IndentConverterPlugin(gedit.Plugin):
	
	def __init__(self):
		gedit.Plugin.__init__(self)
		self.instances = {}
		self.client = gconf.client_get_default()


	def activate(self, window):
		self.instances[window] = IndentConverterWindow(self, window).activate()


	def deactivate(self, window):
		self.instances[window].deactivate()
		del self.instances[window]


	def update_ui(self, window):
		self.instances[window].update_ui()
	
	
	def tab_size(self):
		return self.client.get_int('/apps/gedit-2/preferences/editor/tabs/tabs_size')



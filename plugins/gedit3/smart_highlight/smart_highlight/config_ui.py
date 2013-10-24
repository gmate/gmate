# -*- encoding:utf-8 -*-


# config_ui.py is part of smart-highlighting-gedit
#
#
# Copyright 2010-2012 swatch
#
# smart-highlighting-gedit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#



#import sys
from gi.repository import Gtk, Gedit, Gdk
import os.path

#Gtk.glade.bindtextdomain('smart-highlight', os.path.join(os.path.dirname(__file__), 'locale'))
#Gtk.glade.textdomain('smart-highlight')


class ConfigUI(object):
	def __init__(self, plugin):
		#self._plugin = plugin
		self._instance, self._window = plugin.get_instance()
	
		#Set the Glade file
		gladefile = os.path.join(os.path.dirname(__file__),"config.glade")
		UI = Gtk.Builder()
		UI.set_translation_domain('smart_highlight')
		UI.add_from_file(gladefile)
		self.configWindow = UI.get_object("configWindow")
		self.matchWholeWordCheckbutton = UI.get_object("matchWholeWordCheckbutton")
		self.matchCaseCheckbutton = UI.get_object("matchCaseCheckbutton")
		self.regexSearchCheckbutton = UI.get_object("regexSearchCheckbutton")
		self.fgColorbutton = UI.get_object("fgColorbutton")
		self.bgColorbutton = UI.get_object("bgColorbutton")
		
		self.matchWholeWordCheckbutton.set_active(self._instance.options['MATCH_WHOLE_WORD'])
		self.matchCaseCheckbutton.set_active(self._instance.options['MATCH_CASE'])
		self.regexSearchCheckbutton.set_active(self._instance.options['REGEX_SEARCH'])
		self.fgColorbutton.set_color(Gdk.color_parse(self._instance.smart_highlight['FOREGROUND_COLOR']))
		self.bgColorbutton.set_color(Gdk.color_parse(self._instance.smart_highlight['BACKGROUND_COLOR']))
			
		self.configWindow.show_all()

		signals = { "on_configWindow_destroy" : self.on_configWindow_destroy,
					"on_matchWholeWordCheckbutton_toggled" : self.on_matchWholeWordCheckbutton_toggled,
					"on_matchCaseCheckbutton_toggled" : self.on_matchCaseCheckbutton_toggled,
					"on_regexSearchCheckbutton_toggled": self.on_regexSearchCheckbutton_toggled,
					"on_fgColorbutton_color_set" : self.on_fgColorbutton_color_set,
					"on_bgColorbutton_color_set" : self.on_bgColorbutton_color_set }
		
		UI.connect_signals(signals)
		
		
	def on_configWindow_destroy(self, widget):
		pass
		
	def on_matchWholeWordCheckbutton_toggled(self, widget):
		self._instance.options['MATCH_WHOLE_WORD'] = widget.get_active()
		
	def on_matchCaseCheckbutton_toggled(self, widget):
		self._instance.options['MATCH_CASE'] = widget.get_active()
	
	def on_regexSearchCheckbutton_toggled(self, widget):
		self._instance.options['REGEX_SEARCH'] = widget.get_active()
		
	def on_fgColorbutton_color_set(self, widget):
		self._instance.smart_highlight['FOREGROUND_COLOR'] = widget.get_color().to_string()
		
	def on_bgColorbutton_color_set(self, widget):
		self._instance.smart_highlight['BACKGROUND_COLOR'] = widget.get_color().to_string()	


if __name__ == '__main__':
	dlg = ConfigUI(None)
	Gtk.main()


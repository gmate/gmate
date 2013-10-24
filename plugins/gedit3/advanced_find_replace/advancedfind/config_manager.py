# -*- encoding:utf-8 -*-


# config_manager.py is part of advancedfind-gedit
#
#
# Copyright 2010-2012 swatch
#
# advancedfind-gedit is free software; you can redistribute it and/or modify
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



import os
from xml.dom.minidom import parse

class ConfigManager:
	def __init__(self, filename):
		if os.path.exists(filename) == True:
			self.config_file = filename
			self.dom = parse(filename) # parse an XML file by name
			#self.root = self.dom.documentElement
	
	def get_configure(self, branch, attr):
		root = self.dom.documentElement
		nodes = root.getElementsByTagName(branch)
		for node in nodes:
			if node.getAttribute('name') == attr:
				#return node.firstChild.nodeValue
				return node.getAttribute('value')
	
	def load_configure(self, branch):
		root = self.dom.documentElement
		nodes = root.getElementsByTagName(branch)
		dic = {}
		for node in nodes:
			#dic[node.getAttribute('name')] = node.firstChild.nodeValue
			dic[node.getAttribute('name')] = node.getAttribute('value')
		return dic
	
	def load_list(self, branch):
		root = self.dom.documentElement
		nodes = root.getElementsByTagName(branch)
		patterns = []
		for node in nodes:
			patterns.append(node.getAttribute('name'))
		return patterns
	
	def update_list(self, branch, patterns):
		root = self.dom.documentElement
		nodes = root.getElementsByTagName(branch)
		for node in nodes:
			root.removeChild(node).unlink()
		for pattern in patterns:
			node = root.appendChild(self.dom.createElement(branch))
			node.setAttribute('name', pattern)
					
	def update_configure(self, branch, dic):
		root = self.dom.documentElement
		nodes = root.getElementsByTagName(branch)
		for node in nodes:
			#node.firstChild.nodeValue = dic[node.getAttribute('name')]
			node.setAttribute('value', str(dic[node.getAttribute('name')]))
		
	def update_config_file(self, filename):
		xml_text = self.dom.toprettyxml('\t', '\n', 'utf-8')
		
		lines = xml_text.splitlines(True)
		newlines = []
		for line in lines:
			if line not in ['\n', '\t\n']:
				newlines.append(line.decode('utf-8'))
		
		#print("".join(newlines))
		f = open(filename, 'w+')
		f.write("".join(newlines))
		f.close
		
	def boolean(self, string):
		if string.lower() in ['true', 'yes', 'y', 'ok']:
			return True
		elif string.lower() in ['false', 'no', 'n', 'cancel']:
			return False
		else:
			return string
		
	def to_bool(self, dic):
		for key in list(dic.keys()):
			dic[key] = self.boolean(dic[key])

	
if __name__ == '__main__':
	config_manager = ConfigManager('config.xml')
	#print config_manager.get_configure('shortcut', 'ADVANCED_FIND_ACTIVE')
	#print config_manager.convert_to_shortcut_string(config_manager.get_configure('shortcut', 'ADVANCED_FIND_ACTIVE'))


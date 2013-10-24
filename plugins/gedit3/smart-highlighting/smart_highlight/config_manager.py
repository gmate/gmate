# -*- encoding:utf-8 -*-


# config_manager.py is part of smart-highlighting-gedit.
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
		for i in range(0, len(nodes)):
			if nodes[i].getAttribute('name') == attr:
				return nodes[i].firstChild.nodeValue
	
	def load_configure(self, branch):
		root = self.dom.documentElement
		nodes = root.getElementsByTagName(branch)
		dic = {}
		for i in range(0, len(nodes)):
			dic[nodes[i].getAttribute('name')] = nodes[i].firstChild.nodeValue
		return dic
	
	def update_config_file(self, filename, branch, dic):
		root = self.dom.documentElement
		nodes = root.getElementsByTagName(branch)
		for i in range(0, len(nodes)):
			nodes[i].firstChild.nodeValue = dic[nodes[i].getAttribute('name')]

		f = open(filename, 'w+')
		#print(bytes.decode(self.dom.toprettyxml('', '', 'utf-8'), 'utf-8'))
		f.write(bytes.decode(self.dom.toprettyxml('', '', 'utf-8'), 'utf-8'))
		f.close
		
	def boolean(self, string):
		return string.lower() in ['true', 'yes', 't', 'y', 'ok', '1']
		
	def to_bool(self, dic):
		for key in list(dic.keys()):
			dic[key] = self.boolean(dic[key])

	
if __name__ == '__main__':
	pass

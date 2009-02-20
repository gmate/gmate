# Copyright (C) 2008  Christian Hergert <chris@dronelabs.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

class MoonWalker(object):
	def __init__(self, onResult, onClear=None, onFinish=None):
		self._onResult  = onResult
		self._onClear   = onClear
		self._onFinish  = onFinish
		self._userData  = None

	def walk(self, query, ignoredot = False, maxdepth = -1, user_data = None):
		self._cancel = False
		self._onClear(self, user_data)
		for root, dirs, files in self._innerWalk(query, ignoredot=ignoredot, maxdepth=maxdepth, user_data=user_data):
			self._onResult(self, root, dirs, files, user_data)
			if self._cancel: break
		self._onFinish(self, user_data)

	def cancel(self):
		self._cancel = True
			
	def _innerWalk(self, path, **kwargs):
		"""
	Generator for recursively walking a directory tree with additional
	options compared to os.walk.
	 
	@path: a str containing the root directoyr or file
	@kwargs: The following args are supported:
	ignoredot=False -- ignores dot folders during recursion
	maxdepth=-1 -- sets the maximum recursions to be performed
	 
	Returns: yields tuple of (str,[str],[str]) containing the root dir
	as the first item, list of files as the second, and list of
	dirs as the third.
	"""
		if not os.path.isdir(path):
		    raise StopIteration
	 
		ignoredot = kwargs.get('ignoredot', False)
		maxdepth = kwargs.get('maxdepth', -1)
		curdepth = kwargs.get('curdepth', -1)
		kwargs['curdepth'] = curdepth + 1
	 
		if maxdepth > -1 and curdepth > maxdepth:
		    raise StopIteration
	 
		matches = lambda p: not ignoredot or not p.startswith('.')
		dirs = []
		files = []
	 
		for child in os.listdir(path):
			if matches(child):
				fullpath = os.path.join(path, child)
				if os.path.isdir(fullpath):
					dirs.append(child)
				else:
					files.append(child)
	 
		yield (path, dirs, files)
	 
		for child in dirs:
			fullpath = os.path.join(path, child)
			for item in self._innerWalk(fullpath, **kwargs):
				yield item

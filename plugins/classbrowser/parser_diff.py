# -*- coding: utf-8 -*-
# Copyright (C) 2007 Kristoffer Lundén (kristoffer.lunden@gmail.com)
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

import gtk
import gobject
import pango
import os
import options
import imagelibrary
from parserinterface import ClassParserInterface

class Token:
  def __init__(self):
    self.start = 0
    self.end = 0
    self.name = None
    self.parent = None
    self.children = []
    self.type = 'changeset'

class DiffParser(ClassParserInterface):

  def parse(self, geditdoc):
    text = geditdoc.get_text(*geditdoc.get_bounds())
    linecount = -1
    current_file = None
    changeset = None
    files = []
    uri = geditdoc.get_uri()
    
    for line in text.splitlines():
      linecount += 1
      lstrip = line.lstrip()
      ln = lstrip.split()
      if len(ln) == 0: continue

      if ln[0] == '---':
        if current_file is not None:
          current_file.end = linecount - 1
        current_file = Token()
        current_file.name = ln[1]
        current_file.start = linecount
        current_file.type = 'file'
        current_file.uri = uri
        files.append(current_file)

      elif current_file == None: continue

      elif ln[0] == '@@' and ln[-1] == '@@':
        if changeset is not None:
          changeset.end = linecount
        changeset = Token()
        changeset.name = ' '.join(ln[1:-1])
        changeset.start = linecount
        changeset.uri = uri
        current_file.children.append(changeset)
        changeset.parent = current_file
                  
      # Ending line of last tokens
      if len(files) > 0:
        f =  files[-1]
        f.end = linecount + 2
        if len(f.children) > 0:
          f.children[-1].end = linecount + 2

    model = gtk.TreeStore(gobject.TYPE_PYOBJECT)
    
    pp = None

    # "Fake" common top folder, if any
    # TODO: Create hierarchy if patch applies in multiple directories
    if len(files) > 0:
      paths = map(lambda f:f.name, files)
      prefix = os.path.dirname(os.path.commonprefix(paths)) + '/'
      if len(prefix) > 1:
        parent_path = Token()
        parent_path.type = 'path'
        parent_path.name = prefix
        for f in files: f.name = f.name.replace(prefix,'',1)
        pp = model.append(None,(parent_path,))

    # Build tree
    for f in files:
      tree_iter = model.append(pp,(f,))
      for c in f.children:
         model.append(tree_iter,(c,))
    
    return model

  def cellrenderer(self, treeviewcolumn, cellrenderertext, treemodel, it):  
    token = treemodel.get_value(it,0)

    colour = options.singleton().colours["member"]

    if token.type == 'path':
      colour = options.singleton().colours["namespace"]
    elif token.type == 'file':
      colour = options.singleton().colours["class"]

    cellrenderertext.set_property("text", token.name)
    cellrenderertext.set_property("style", pango.STYLE_NORMAL)
    cellrenderertext.set_property("foreground-gdk", colour)

  def get_tag_position(self, model, path):
    tok = model.get_value(model.get_iter(path),0)
    try: return tok.uri, tok.start + 1
    except: return None

  def get_tag_at_line(self, model, doc, linenumber):

    def find_path(model, path, iter, data):
      line = data[0]
      token = model.get_value(iter, 0)
      if token.start <= line and token.end > line:
        print path
        data[1].append(path)
        #return True
      return False

    path_found = []
    model.foreach(find_path, (linenumber, path_found))

    if len(path_found) > 0:
      return path_found[-1]
    return None

  def pixbufrenderer(self, treeviewcolumn, cellrendererpixbuf, treemodel, it):
    token = treemodel.get_value(it,0)
    if token.type == 'path':
      cellrendererpixbuf.set_property("stock-id", gtk.STOCK_DIRECTORY)
    elif token.type == 'file':
      cellrendererpixbuf.set_property("stock-id", gtk.STOCK_FILE)
    else:
      cellrendererpixbuf.set_property("pixbuf",imagelibrary.pixbufs['patch'])

# -*- coding: utf-8 -*-
# Copyright (C) 2007 Kristoffer Lundén (kristoffer.lunden@gmail.com)
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

import gtk
import gobject
import pango
import os
import options
import imagelibrary
from parserinterface import ClassParserInterface

class Token:
  def __init__(self):
    self.start = 0
    self.end = 0
    self.name = None
    self.parent = None
    self.children = []
    self.type = 'changeset'

class DiffParser(ClassParserInterface):

  def parse(self, geditdoc):
    text = geditdoc.get_text(*geditdoc.get_bounds())
    linecount = -1
    current_file = None
    changeset = None
    files = []
    uri = geditdoc.get_uri()
    
    for line in text.splitlines():
      linecount += 1
      lstrip = line.lstrip()
      ln = lstrip.split()
      if len(ln) == 0: continue

      if ln[0] == '---':
        if current_file is not None:
          current_file.end = linecount - 1
        current_file = Token()
        current_file.name = ln[1]
        current_file.start = linecount
        current_file.type = 'file'
        current_file.uri = uri
        files.append(current_file)

      elif current_file == None: continue

      elif ln[0] == '@@' and ln[-1] == '@@':
        if changeset is not None:
          changeset.end = linecount
        changeset = Token()
        changeset.name = ' '.join(ln[1:-1])
        changeset.start = linecount
        changeset.uri = uri
        current_file.children.append(changeset)
        changeset.parent = current_file
                  
      # Ending line of last tokens
      if len(files) > 0:
        f =  files[-1]
        f.end = linecount + 2
        if len(f.children) > 0:
          f.children[-1].end = linecount + 2

    model = gtk.TreeStore(gobject.TYPE_PYOBJECT)
    
    pp = None

    # "Fake" common top folder, if any
    # TODO: Create hierarchy if patch applies in multiple directories
    if len(files) > 0:
      paths = map(lambda f:f.name, files)
      prefix = os.path.dirname(os.path.commonprefix(paths)) + '/'
      if len(prefix) > 1:
        parent_path = Token()
        parent_path.type = 'path'
        parent_path.name = prefix
        for f in files: f.name = f.name.replace(prefix,'',1)
        pp = model.append(None,(parent_path,))

    # Build tree
    for f in files:
      tree_iter = model.append(pp,(f,))
      for c in f.children:
         model.append(tree_iter,(c,))
    
    return model

  def cellrenderer(self, treeviewcolumn, cellrenderertext, treemodel, it):  
    token = treemodel.get_value(it,0)

    colour = options.singleton().colours["member"]

    if token.type == 'path':
      colour = options.singleton().colours["namespace"]
    elif token.type == 'file':
      colour = options.singleton().colours["class"]

    cellrenderertext.set_property("text", token.name)
    cellrenderertext.set_property("style", pango.STYLE_NORMAL)
    cellrenderertext.set_property("foreground-gdk", colour)

  def get_tag_position(self, model, path):
    tok = model.get_value(model.get_iter(path),0)
    try: return tok.uri, tok.start + 1
    except: return None

  def get_tag_at_line(self, model, doc, linenumber):

    def find_path(model, path, iter, data):
      line = data[0]
      token = model.get_value(iter, 0)
      if token.start <= line and token.end > line:
        print path
        data[1].append(path)
        #return True
      return False

    path_found = []
    model.foreach(find_path, (linenumber, path_found))

    if len(path_found) > 0:
      return path_found[-1]
    return None

  def pixbufrenderer(self, treeviewcolumn, cellrendererpixbuf, treemodel, it):
    token = treemodel.get_value(it,0)
    if token.type == 'path':
      cellrendererpixbuf.set_property("stock-id", gtk.STOCK_DIRECTORY)
    elif token.type == 'file':
      cellrendererpixbuf.set_property("stock-id", gtk.STOCK_FILE)
    else:
      cellrendererpixbuf.set_property("pixbuf",imagelibrary.pixbufs['patch'])


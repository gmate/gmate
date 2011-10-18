# -*- coding: utf-8 -*-
#
# Gedit plugin that does automatic pair character completion.
#
# Copyright © 2010, Kevin McGuinness <kevin.mcguinness@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

__version__ = '1.0.4'
__author__ = 'Kevin McGuinness'

from gi.repository import Gtk, Gedit, GObject, Gdk
import sys
import os

# Defaults
DEFAULT_STMT_TERMINATOR = ';'
LANG_META_STMT_TERMINATOR_KEY = 'statement-terminator'
NEWLINE_CHAR = '\n'

# Map from language identifiers to (opening parens, closing parens) pairs
language_parens = {}

def add_language_parenthesis(name, spec):
  """Add parenthesis for the given language. The spec should be a string in
     which each pair of characters represents a pair of parenthesis for the
     language, eg. "(){}[]".
  """
  parens = [], []
  for i in range(0, len(spec), 2):
    parens[0].append(spec[i+0])
    parens[1].append(spec[i+1])
  language_parens[name] = parens

def to_char(keyval_or_char):
  """Convert a event keyval or character to a character"""
  if isinstance(keyval_or_char, str):
    return keyval_or_char
  return chr(keyval_or_char) if 0 < keyval_or_char < 128 else None

class PairCompletionPlugin(GObject.Object, Gedit.WindowActivatable):
  """Automatic pair character completion for gedit"""

  ViewHandlerName = 'pair_char_completion_handler'

  window = GObject.property(type=Gedit.Window)

  def __init__(self):
    GObject.Object.__init__(self)
    self.ctrl_enter_enabled = True
    self.language_id = 'plain'
    self.opening_parens = language_parens['default'][0]
    self.closing_parens = language_parens['default'][1]

  def do_activate(self):
    self.do_update_state()

  def do_deactivate(self):
    for view in self.window.get_views():
      handler_id = getattr(view, self.ViewHandlerName, None)
      if handler_id is not None:
        view.disconnect(handler_id)
      setattr(view, self.ViewHandlerName, None)

  def do_update_state(self):
    self.update_ui()


  def update_ui(self):
    view = self.window.get_active_view()
    doc = self.window.get_active_document()
    if isinstance(view, Gedit.View) and doc:
      if getattr(view, self.ViewHandlerName, None) is None:
        handler_id = view.connect('key-press-event', self.on_key_press, doc)
        setattr(view, self.ViewHandlerName, handler_id)

  def is_opening_paren(self,char):
    return char in self.opening_parens

  def is_closing_paren(self,char):
    return char in self.closing_parens

  def get_matching_opening_paren(self,closer):
    try:
      return self.opening_parens[self.closing_parens.index(closer)]
    except ValueError:
      return None

  def get_matching_closing_paren(self,opener):
    try:
      return self.closing_parens[self.opening_parens.index(opener)]
    except ValueError:
      return None

  def would_balance_parens(self, doc, closing_paren):
    iter1 = doc.get_iter_at_mark(doc.get_insert())
    opening_paren = self.get_matching_opening_paren(closing_paren)
    balance = 1
    while balance != 0 and not iter1.is_start():
      iter1.backward_char()
      if iter1.get_char() == opening_paren:
        balance -= 1
      elif iter1.get_char() == closing_paren:
        balance += 1
    return balance == 0

  def compare_marks(self, doc, mark1, mark2):
    return doc.get_iter_at_mark(mark1).compare(doc.get_iter_at_mark(mark2))

  def enclose_selection(self, doc, opening_paren):
    closing_paren = self.get_matching_closing_paren(opening_paren)
    doc.begin_user_action()
    mark1 = doc.get_insert()
    mark2 = doc.get_selection_bound()
    if self.compare_marks(doc, mark1, mark2) > 0:
      mark1, mark2 = mark2, mark1
    doc.insert(doc.get_iter_at_mark(mark1), opening_paren)
    doc.insert(doc.get_iter_at_mark(mark2), closing_paren)
    iter1 = doc.get_iter_at_mark(mark2)
    doc.place_cursor(iter1)
    doc.end_user_action()
    return True

  def auto_close_paren(self, doc, opening_paren):
    closing_paren = self.get_matching_closing_paren(opening_paren)
    doc.begin_user_action()
    doc.insert_at_cursor(opening_paren+closing_paren)
    iter1 = doc.get_iter_at_mark(doc.get_insert())
    iter1.backward_char()
    doc.place_cursor(iter1)
    doc.end_user_action()
    return True

  def move_cursor_forward(self, doc):
    doc.begin_user_action()
    iter1 = doc.get_iter_at_mark(doc.get_insert())
    iter1.forward_char()
    doc.place_cursor(iter1)
    doc.end_user_action()
    return True

  def move_to_end_of_line_and_insert(self, doc, text):
    doc.begin_user_action()
    mark = doc.get_insert()
    iter1 = doc.get_iter_at_mark(mark)
    iter1.set_line_offset(0)
    iter1.forward_to_line_end()
    doc.place_cursor(iter1)
    doc.insert_at_cursor(text)
    doc.end_user_action()
    return True

  def insert_two_lines(self, doc, text):
    doc.begin_user_action()
    mark = doc.get_insert()
    iter1 = doc.get_iter_at_mark(mark)
    doc.place_cursor(iter1)
    doc.insert_at_cursor(text)
    doc.insert_at_cursor(text)
    mark = doc.get_insert()
    iter2 = doc.get_iter_at_mark(mark)
    iter2.backward_chars(len(text))
    doc.place_cursor(iter2)
    doc.end_user_action()
    return True

  def get_char_under_cursor(self, doc):
    return doc.get_iter_at_mark(doc.get_insert()).get_char()

  def get_stmt_terminator(self, doc):
    terminator = DEFAULT_STMT_TERMINATOR
    lang = doc.get_language()
    if lang is not None:
      # Allow this to be changed by the language definition
      lang_terminator = lang.get_metadata(LANG_META_STMT_TERMINATOR_KEY)
      if lang_terminator is not None:
        terminator = lang_terminator
    return terminator

  def get_current_line_indent(self, doc):
    it_start = doc.get_iter_at_mark(doc.get_insert())
    it_start.set_line_offset(0)
    it_end = it_start.copy()
    it_end.forward_to_line_end()
    indentation = []
    while it_start.compare(it_end) < 0:
      char = it_start.get_char()
      if char == ' ' or char == '\t':
        indentation.append(char)
      else:
        break
      it_start.forward_char()
    return ''.join(indentation)

  def is_ctrl_enter(self, event):
    return (self.ctrl_enter_enabled and
      event.keyval == Gdk.KEY_Return and
      event.get_state() & Gdk.ModifierType.CONTROL_MASK)

  def should_auto_close_paren(self, doc):
    iter1 = doc.get_iter_at_mark(doc.get_insert())
    if iter1.is_end() or iter1.ends_line():
      return True
    char = iter1.get_char()
    return not (char.isalnum() or char == '_')

  def update_language(self, doc):
    lang = doc.get_language()
    lang_id = lang.get_id() if lang is not None else 'plain'
    if lang_id != self.language_id:
      parens = language_parens.get(lang_id, language_parens['default'])
      self.opening_parens = parens[0]
      self.closing_parens = parens[1]
      self.language_id = lang_id

  def on_key_press(self, view, event, doc):
    handled = False
    self.update_language(doc)
    ch = to_char(event.keyval)
    key = Gdk.keyval_name(event.keyval)
    if self.is_closing_paren(ch):
      # Skip over closing parenthesis if doing so would mean that the
      # preceeding parenthesis are correctly balanced
      if (self.get_char_under_cursor(doc) == ch and
          self.would_balance_parens(doc, ch)):
        handled = self.move_cursor_forward(doc)
    if not handled and self.is_opening_paren(ch):
      if doc.get_has_selection():
        # Enclose selection in parenthesis or quotes
        handled = self.enclose_selection(doc, ch)
      elif self.should_auto_close_paren(doc):
        # Insert matching closing parenthesis and move cursor back one
        handled = self.auto_close_paren(doc, ch)
    if not handled and self.is_ctrl_enter(event):
      # Handle Ctrl+Return and Ctrl+Shift+Return
      text_to_insert = NEWLINE_CHAR + self.get_current_line_indent(doc)
      if event.get_state() & Gdk.EventMask.SHIFT_MASK:
        text_to_insert = self.get_stmt_terminator(doc) + text_to_insert
      self.move_to_end_of_line_and_insert(doc, text_to_insert)
      view.scroll_mark_onscreen(doc.get_insert())
      handled = True
    if not handled and key in ('Enter', 'Return', 'ISO_Return'):
      # Enter was just pressed
      char_under_cusor = self.get_char_under_cursor(doc)
      if (self.is_closing_paren(char_under_cusor) and
        self.would_balance_parens(doc, char_under_cusor)):
        # If the character under the cursor would balance parenthesis
        text_to_insert = NEWLINE_CHAR + self.get_current_line_indent(doc)
        self.insert_two_lines(doc, text_to_insert)
        handled = True
    return handled

# Load language parenthesis
for path in sys.path:
  fn = os.path.join(path, 'pair_char_lang.py')
  if os.path.isfile(fn):
    execfile(fn, {'lang': add_language_parenthesis})
    break

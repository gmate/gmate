# -*- coding: utf-8 -*-
# vim: ts=4 nowrap textwidth=80
# Smart Indent Plugin
# Copyright © 2008 Alexandre da Silva / Carlos Antonio da Silva
#
# This file is part of Gmate.
#
# See LICENTE.TXT for licence information

import gedit
import gtk
import gobject
import re

class SmartIndentPlugin(gedit.Plugin):
    handler_ids = []

    def __init__(self):
        gedit.Plugin.__init__(self)

    def activate(self, window):
        view = window.get_active_view()
        self.setup_smart_indent(view, 'none')

    def deactivate(self, window):
        for (handler_id, view) in self.handler_ids:
            view.disconnect(handler_id)

    def update_ui(self, window):
        view = window.get_active_view()
        lang = 'none'
        if view:
            buf = view.get_buffer()
            language = buf.get_language()
            if language:
                lang = language.get_id()
        self.setup_smart_indent(view, lang)

    def setup_smart_indent(self, view, lang):
        if type(view) == gedit.View:
            if getattr(view, 'smart_indent_instance', False) == False:
                setattr(view, 'smart_indent_instance', SmartIndent())
                handler_id = view.connect('key-press-event', view.smart_indent_instance.key_press_handler)
                self.handler_ids.append((handler_id, view))
            view.smart_indent_instance.set_language(lang)

class SmartIndent:

    def __init__(self):
        self.__not_available = True
        self.__line_unindented = -1
        self.__line_no = -1
        return

    def set_language(self, lang):
        self.__not_available = False
        if lang == 'none':
            self.__not_available = True
        elif lang == 'ruby':
            self.re_indent_next = re.compile(r'[^#]*\s+\bdo\b(\s*|(\s+\|.+\|\s*))|\s*(\bif\b\s+.*|\belsif\b.*|\belse\b.*|\bdo\b(\s*|\s+.*)|\bcase\b\s+.*|\bwhen\b\s+.*|\bwhile\b\s+.*|\bfor\b\s+.*|\buntil\b\s+.*|\bloop\b\s+.*|\bdef\b\s+.*|\bclass\b\s+.*|\bmodule\b\s+.*|\bbegin\b.*|\bunless\b\s+.*|\brescue\b.*|\bensure\b.*)+')
            self.re_unindent_curr = re.compile(r'^\s*(else.*|end\s*|elsif.*|rescue.*|when.*|ensure.*)$')
            self.unindent_keystrokes = 'edfn'
        elif lang == 'python':
            self.re_indent_next = re.compile(r'\s*[^#]{3,}:\s*(#.*)?')
            self.re_unindent_curr = re.compile(r'^\s*(else|elif\s.*|except(\s.*)?|finally)\s*:')
            self.unindent_keystrokes = ':'
        elif lang == 'javascript':
            self.re_indent_next = re.compile(r'\s*(((if|while)\s*\(|else\s*|else\s+if\s*\(|for\s*\(.*\))[^{;]*)')
            self.re_unindent_curr = re.compile(r'^.*(default:\s*|case.*:.*)$')
            self.unindent_keystrokes = ':'
        elif lang == 'php':
            self.re_indent_next = re.compile(r'\s*(((if|while|else\s*(if)?|for(each)?|switch|declare)\s*\(.*\)[^{:;]*)|(do\s*[^\({:;]*))')
            self.re_unindent_curr = re.compile(r'^.*(default:\s*|case.*:.*)$')
            self.unindent_keystrokes = ':'
        else:
            self.__not_available = True

    def __update_line_no(self, buf):
        cursor_iter = buf.get_iter_at_mark(buf.get_insert())
        self.__line_no = cursor_iter.get_line()
        if self.__line_no != self.__line_unindented:
            self.__line_unindented = -1

    def __get_current_line(self, view, buf):
        cursor_iter = buf.get_iter_at_mark(buf.get_insert())
        line_start_iter = cursor_iter.copy()
        view.backward_display_line_start(line_start_iter)
        return buf.get_text(line_start_iter, cursor_iter)

    def key_press_handler(self, view, event):
        buf = view.get_buffer()
        if self.__not_available or buf.get_has_selection(): return
        # Get tabs/indent configuration
        if view.get_insert_spaces_instead_of_tabs():
          indent_width = ' ' * view.get_tab_width()
        else:
          indent_width = '\t'
        keyval = event.keyval
        self.__update_line_no(buf)
        if keyval == 65293:
            # Check next line indentation for current line
            line = self.__get_current_line(view, buf)
            if self.re_indent_next and self.re_indent_next.match(line):
                old_indent = line[:len(line) - len(line.lstrip())]
                indent = '\n'+ old_indent + indent_width
                buf.insert_interactive_at_cursor(indent, True)
                return True
        elif keyval == 65288:
            line = self.__get_current_line(view, buf)
            if line.strip() == '' and line != '':
                length = len(indent_width)
                nb_to_delete = len(line) % length or length
                cursor_position = buf.get_property('cursor-position')
                iter_cursor = buf.get_iter_at_offset(cursor_position)
                iter_before = buf.get_iter_at_offset(cursor_position - nb_to_delete)
                buf.delete_interactive(iter_before, iter_cursor, True)
                return True
        elif keyval in [ord(k) for k in self.unindent_keystrokes]:
            line = self.__get_current_line(view, buf)
            if self.__line_unindented != self.__line_no:
                line_eval = line+chr(event.keyval)
                if self.re_unindent_curr and self.re_unindent_curr.match(line_eval):
                    cursor_iter = buf.get_iter_at_mark(buf.get_insert())
                    line_start_iter = cursor_iter.copy()
                    view.backward_display_line_start(line_start_iter)
                    iter_end_del = buf.get_iter_at_offset(line_start_iter.get_offset() + len(indent_width))
                    text = buf.get_text(line_start_iter, iter_end_del)
                    if text.strip() == '':
                        buf.delete_interactive(line_start_iter, iter_end_del, True)
                        self.__line_unindented = self.__line_no
                        return False
        return False

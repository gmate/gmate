# Zen Coding for Gedit
#
# Copyright (C) 2010 Franck Marcia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys, os, re, locale

import zen_core, zen_actions, zen_file, html_matcher
from image_size import update_image_size

import zen_dialog
from html_navigation import HtmlNavigation
from lorem_ipsum import lorem_ipsum

try:
    sys.path.append('/usr/lib/gedit/plugins/')
    from snippets import Document as SnippetDocument
    USE_SNIPPETS = True
except:
    print 'failed importing snippets'
    USE_SNIPPETS = False


class ZenSnippet():

    def __init__(self, abbreviation, content):
        self.valid = True
        self.properties = {
            'text': content,
            'drop-targets': '',
            'tag': abbreviation,
            'description': 'zencoding',
            'accelerator': ''}

    def __getitem__(self, prop):
        return self.properties[prop]


placeholder_count = 0


def placeholder_feed(m):

    global placeholder_count
    placeholder_count += 1

    skip = len(zen_core.get_caret_placeholder()) + 1

    if m and m.group(1):
        if m.group(1).startswith('{{'):
            return '${' + repr(placeholder_count)
        elif m.group(1).startswith('>'):
            return '>${' + repr(placeholder_count) + ':' + m.group(1)[skip:-1] + '}<'
        else:
            return '$' + repr(placeholder_count)
    else:
        return ''


class ZenEditor():

    def __init__(self, window):

        self.window = window

        self.last_wrap = ''
        self.last_expand = ''
        self.last_lorem_ipsum = 'list 5*5'

        self.placeholder = zen_core.get_caret_placeholder()
        zen_core.set_caret_placeholder('')

        self.html_navigation = None
        self.snippet_document = {}

    # --- Original interface ---------------------------------------------------
    def set_context(self, view):

        default_locale = locale.getdefaultlocale()[0]
        if default_locale:
            lang = re.sub(r'_[^_]+$', '', default_locale)
            if lang != default_locale:
                zen_core.set_variable('lang', lang)
                zen_core.set_variable('locale', default_locale.replace('_', '-'))
            else:
                zen_core.set_variable('lang', default_locale)
                zen_core.set_variable('locale', default_locale)

        self.document = self.window.get_active_document()
        if self.document:
            zen_core.set_variable('charset', self.document.get_encoding().get_charset())

        self.view = view
        if self.view:
            self.buffer = self.view.get_buffer()
            if self.view.get_insert_spaces_instead_of_tabs():
                zen_core.set_variable('indentation', " " * self.view.get_tab_width())
            else:
                zen_core.set_variable('indentation', "\t")

            #zen_core.set_newline(???)

            if USE_SNIPPETS:
                if not (self.view in self.snippet_document):
                    self.snippet_document[self.view] = SnippetDocument()
                    self.snippet_document[self.view].view = self.view
            else:
                self.snippet_document[self.view] = None

    def get_selection_range(self):

        offset_start = self.get_insert_offset()
        offset_end = self.get_selection_bound_offset()

        if offset_start < offset_end:
            return offset_start, offset_end

        return offset_end, offset_start

    def create_selection(self, offset_start, offset_end=None):

        if offset_end is None:
            iter_start = self.buffer.get_iter_at_offset(offset_start)
            self.buffer.place_cursor(iter_start)

        else:
            iter_start = self.buffer.get_iter_at_offset(offset_start)
            iter_end = self.buffer.get_iter_at_offset(offset_end)
            self.buffer.select_range(iter_start, iter_end)

    def get_current_line_range(self):

        iter_start = self.get_insert_iter()
        iter_start.set_line_offset(0)
        iter_end = iter_start.copy()

        if iter_end.forward_visible_line():
            iter_end.backward_char()

        else:
            iter_end = self.buffer.get_end_iter()

        return iter_start.get_offset(), iter_end.get_offset()

    def get_caret_pos(self):
        return self.get_insert_offset()

    def set_caret_pos(self, pos):
        self.buffer.place_cursor(self.buffer.get_iter_at_offset(pos))

    def get_current_line(self):

        offset_start, offset_end = self.get_current_line_range()
        iter_start = self.buffer.get_iter_at_offset(offset_start)
        iter_end = self.buffer.get_iter_at_offset(offset_end)
        return self.buffer.get_text(iter_start, iter_end, True).decode('UTF-8')

    def replace_content(self, value, offset_start=None, offset_end=None):

        if offset_start is None and offset_end is None:
            iter_start = self.buffer.get_iter_at_offset(0)
            iter_end = self.get_end_iter()

        elif offset_end is None:
            iter_start = self.buffer.get_iter_at_offset(offset_start)
            iter_end = self.buffer.get_iter_at_offset(offset_start)

        else:
            iter_start = self.buffer.get_iter_at_offset(offset_start)
            iter_end = self.buffer.get_iter_at_offset(offset_end)

        self.buffer.delete(iter_start, iter_end)
        self.set_caret_pos(offset_start)
        self.insertion_start = self.get_insert_offset()

        padding = zen_actions.get_current_line_padding(self)
        padding = re.sub('[\r\n]', '', padding)
        self.buffer.insert_at_cursor(zen_core.pad_string(value, padding))

        self.insertion_end = self.get_insert_offset()

    def get_content(self):
        iter_start = self.buffer.get_iter_at_offset(0)
        iter_end = self.get_end_iter()
        return self.buffer.get_text(iter_start, iter_end, True).decode('UTF-8')

    def get_syntax(self):
        lang = self.window.get_active_document().get_language()
        lang = lang and lang.get_name()
        if lang == 'CSS': lang = 'css'
        elif lang == 'XSLT': lang = 'xsl'
        else: lang = 'html'
        return lang

    def get_profile_name(self):
        return 'xhtml'

    def prompt(self, title):
        done, result = zen_dialog.main(self, self.window, None, title)
        if done:
            return result
        return ''

    def get_selection(self):
        offset_start, offset_end = self.get_selection_range()
        iter_start = self.buffer.get_iter_at_offset(offset_start)
        iter_end = self.buffer.get_iter_at_offset(offset_end)
        return self.buffer.get_text(iter_start, iter_end, True).decode('UTF-8')

    def get_file_path(self):
        return re.sub('^file://', '', self.document.get_uri())

    # --- Iter and offset oneliners --------------------------------------------

    def get_insert_iter(self):
        return self.buffer.get_iter_at_mark(self.buffer.get_insert())

    def get_insert_offset(self):
        return self.get_insert_iter().get_offset()

    def get_selection_bound_iter(self):
        return self.buffer.get_iter_at_mark(self.buffer.get_selection_bound())

    def get_selection_bound_offset(self):
        return self.get_selection_bound_iter().get_offset()

    def get_end_iter(self):
        return self.buffer.get_iter_at_offset(self.buffer.get_char_count())

    def get_end_offset(self):
        return self.get_end_iter().get_offset()

    #--- Miscellaneous stuff ---------------------------------------------------

    def start_edit(self):
        # bug when the cursor is at the very beginning
        if self.insertion_start == 0:
            self.insertion_start = 1
        self.set_caret_pos(self.insertion_start)
        if not self.next_edit_point() or (self.get_insert_offset() > self.insertion_end):
            self.set_caret_pos(self.insertion_end)

    def show_caret(self):
        self.view.scroll_mark_onscreen(self.buffer.get_insert())

    def get_user_settings_error(self):
        return zen_core.get_variable('user_settings_error')

    def save_selection(self):
        self.save_offset_insert = self.get_insert_offset()
        self.save_offset_selection_bound = self.get_selection_bound_offset()

    def restore_selection(self):
        iter_insert = self.buffer.get_iter_at_offset(self.save_offset_insert)
        iter_selection_bound = self.buffer.get_iter_at_offset(self.save_offset_selection_bound)
        self.buffer.select_range(iter_insert, iter_selection_bound)

    def prepare_nav(self):
        offset_start, offset_end = self.get_selection_range()
        content = self.get_content()
        if not self.html_navigation:
            self.html_navigation = HtmlNavigation(content)
        return offset_start, offset_end, content

    #--- Snippet hook ----------------------------------------------------------

    def expand_with_snippet(self, abbr, mode = 0):
        # mode_names = { 0: 'expand abbr',  1: 'expand with abbr', 2: 'wrap with abbr' }

        if mode < 2:
            content = zen_core.expand_abbreviation(abbr, self.get_syntax(), self.get_profile_name())
        else:
            content = self.core_wrap_with_abbreviation(abbr)

        if content:

            global placeholder_count
            placeholder_count = 0
            search_string = '(' + self.placeholder + '|\{' + self.placeholder + '|>' + self.placeholder + '[^<]+<' + ')'
            content = re.sub(search_string, placeholder_feed, content)

            offset_start, offset_end = self.get_selection_range()
            if offset_start == offset_end and mode == 0:
                offset_start -= len(abbr)

            snippet = ZenSnippet(abbr, content)
            iter_start = self.buffer.get_iter_at_offset(offset_start)
            iter_end = self.buffer.get_iter_at_offset(offset_end)

            self.snippet_document[self.view].apply_snippet(snippet, iter_start, iter_end)

        return content

    #--- Expand abbreviation ---------------------------------------------------

    def expand_abbreviation(self):

        zen_core.set_caret_placeholder(self.placeholder)

        abbr = zen_actions.find_abbreviation(self)

        if abbr:

            if self.snippet_document[self.view]:
                self.expand_with_snippet(abbr)

            else:
                self.buffer.begin_user_action()
                content = zen_core.expand_abbreviation(abbr, self.get_syntax(), self.get_profile_name())
                if content:
                    content = content.replace(self.placeholder, '')
                    content = re.sub('\$\d+|\$\{\d+:[^\}]*\}', '', content)
                    unused, offset_end = self.get_selection_range()
                    self.replace_content(content, offset_end - len(abbr), offset_end)
                    self.start_edit()
                self.buffer.end_user_action()

        zen_core.set_caret_placeholder('')

    #--- Expand with abbreviation ----------------------------------------------

    def callback_expand_with_abbreviation(self, done, abbr, last = False):

        self.buffer.begin_user_action()

        if done:
            self.buffer.undo()
            self.restore_selection()

        if last and self.snippet_document[self.view]:
            content = self.expand_with_snippet(abbr, 1)

        else:

            content = zen_core.expand_abbreviation(abbr, self.get_syntax(), self.get_profile_name())

            if content:
                content = content.replace(self.placeholder, '')
                content = re.sub('\$\d+|\$\{\d+:[^\}]*\}', '', content)
                self.replace_content(content, self.get_insert_offset())

        self.buffer.end_user_action()

        return not not content

    def expand_with_abbreviation(self):

        zen_core.set_caret_placeholder(self.placeholder)
        self.save_selection()

        done, self.last_expand = zen_dialog.main(self, self.window, self.callback_expand_with_abbreviation, self.last_expand, True)

        if done and not self.snippet_document[self.view]:
            self.start_edit()

        zen_core.set_caret_placeholder('')

    #--- Wrap with abbreviation ------------------------------------------------

    def core_wrap_with_abbreviation(self, abbr):

        if not abbr:
            return None

        syntax = self.get_syntax()
        profile_name = self.get_profile_name()

        start_offset, end_offset = self.get_selection_range()
        content = self.get_content()

        if start_offset == end_offset:
            rng = html_matcher.match(content, start_offset, profile_name)
            if rng[0] is None:
                return None
            else:
                start_offset, end_offset = rng

        start_offset, end_offset = zen_actions.narrow_to_non_space(content, start_offset, end_offset)
        line_bounds = zen_actions.get_line_bounds(content, start_offset)
        padding = zen_actions.get_line_padding(content[line_bounds[0]:line_bounds[1]])

        new_content = content[start_offset:end_offset]
        return zen_core.wrap_with_abbreviation(abbr, zen_actions.unindent_text(new_content, padding), syntax, profile_name)

    def callback_wrap_with_abbreviation(self, done, abbr, last = False):

        self.buffer.begin_user_action()

        if done:
            self.buffer.undo()
            self.restore_selection()

        if last and self.snippet_document[self.view]:
            content = self.expand_with_snippet(abbr, 2)

        else:

            content = self.core_wrap_with_abbreviation(abbr)

            if content:
                content = content.replace(self.placeholder, '')
                content = re.sub('\$\d+|\$\{\d+:[^\}]*\}', '', content)
                offset_start, offset_end = self.get_selection_range()
                self.replace_content(content, offset_start, offset_end)

        self.buffer.end_user_action()

        return not not content

    def wrap_with_abbreviation(self):

        zen_core.set_caret_placeholder(self.placeholder)
        self.save_selection()

        done, self.last_wrap = zen_dialog.main(self, self.window, self.callback_wrap_with_abbreviation, self.last_wrap, True)

        if done and not self.snippet_document[self.view]:
            self.start_edit()

        zen_core.set_caret_placeholder('')

    #--- Zenify ----------------------------------------------------------------

    def zenify(self, mode):

        offset_start, offset_end, content = self.prepare_nav()
        result = self.html_navigation.zenify(offset_start, offset_end, content, mode)

        if result:
            self.save_selection()
            self.prompt(result)
            self.restore_selection()

    #--- Lorem ipsum -----------------------------------------------------------

    def callback_lorem_ipsum(self, done, cmd, last = False):
        self.buffer.begin_user_action()
        if done:
            self.buffer.undo()
            self.restore_selection()
        content = lorem_ipsum(cmd)
        if content:
            self.replace_content(content, self.get_insert_offset())
        self.buffer.end_user_action()
        return not not content

    def lorem_ipsum(self):
        self.save_selection()
        done, self.last_lorem_ipsum = zen_dialog.main(self, self.window, self.callback_lorem_ipsum, self.last_lorem_ipsum, False)

    #--- Select inward or outward ----------------------------------------------

    def match_pair_inward(self):
        offset_start, offset_end, content = self.prepare_nav()
        offset_start, offset_end = self.html_navigation.inner_bounds(offset_start, offset_end, content)
        if not (offset_start is None or offset_end is None):
            self.create_selection(offset_start, offset_end)

    def match_pair_outward(self):
        offset_start, offset_end, content = self.prepare_nav()
        offset_start, offset_end = self.html_navigation.outer_bounds(offset_start, offset_end, content)
        if not (offset_start is None or offset_end is None):
            self.create_selection(offset_start, offset_end)

    #--- Tag jumps -------------------------------------------------------------

    def new_tag(self, direction):

        offset_start, offset_end, content = self.prepare_nav()

        if direction == 'next':
            node = self.html_navigation.next_tag(offset_start, offset_end, content)

        else:
            node = self.html_navigation.previous_tag(offset_start, offset_end, content)

        if node:
            iter_start = self.buffer.get_iter_at_offset(node.start)
            iter_end = self.buffer.get_iter_at_offset(node.end)
            self.create_selection(node.start, node.end)
            self.show_caret()

    def prev_tag(self):
        self.new_tag('previous')

    def next_tag(self):
        self.new_tag('next')

    #--- Node jumps ------------------------------------------------------------

    def new_node(self, direction, with_spaces = True):

        offset_start, offset_end, content = self.prepare_nav()

        while True:

            if direction == 'next':
                node = self.html_navigation.next_node(offset_start, offset_end, content)

            else:
                node = self.html_navigation.previous_node(offset_start, offset_end, content)

            if node:

                iter_start = self.buffer.get_iter_at_offset(node.start)
                iter_end = self.buffer.get_iter_at_offset(node.end)

                found = self.buffer.get_text(iter_start, iter_end, True).decode('UTF-8')
                if not with_spaces and found.isspace() and found.find('\n') != -1:
                    offset_start = node.start
                    offset_end = node.end

                else:
                    self.create_selection(node.start, node.end)
                    break

            else:
                break

        self.show_caret()

    def prev_node(self):
        self.new_node('previous')

    def next_node(self):
        self.new_node('next')

    #--- Edit points jumps -----------------------------------------------------

    def prev_edit_point(self):
        result = zen_actions.prev_edit_point(self)
        self.show_caret()
        return result

    def next_edit_point(self):
        result = zen_actions.next_edit_point(self)
        self.show_caret()
        return result

    #--- Image actions ---------------------------------------------------------

    def update_image_size(self):
        self.buffer.begin_user_action()
        update_image_size(self)
        self.buffer.end_user_action()

    def encode_decode_base64(self):
        self.buffer.begin_user_action()
        try:
            zen_actions.encode_decode_base64(self)
        except:
            pass
        self.buffer.end_user_action()

    #--- Other edition actions -------------------------------------------------

    def merge_lines(self):
        self.buffer.begin_user_action()
        zen_actions.merge_lines(self)
        self.buffer.end_user_action()

    def remove_tag(self):
        self.buffer.begin_user_action()
        zen_actions.remove_tag(self)
        self.buffer.end_user_action()

    def split_join_tag(self):
        self.buffer.begin_user_action()
        zen_actions.split_join_tag(self)
        self.buffer.end_user_action()

    def toggle_comment(self):
        self.buffer.begin_user_action()
        zen_actions.toggle_comment(self)
        self.buffer.end_user_action()

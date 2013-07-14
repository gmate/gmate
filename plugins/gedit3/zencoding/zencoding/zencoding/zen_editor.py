'''
High-level editor interface that communicates with underlying editor (like
Espresso, Coda, etc.) or browser. Basically, you should call set_context(obj) 
method to set up undelying editor context before using any other method.

This interface is used by zen_actions.py for performing different
actions like Expand abbreviation

@example
import zen_editor
zen_editor.set_context(obj);
//now you are ready to use editor object
zen_editor.get_selection_range();

@author Sergey Chikuyonok (serge.che@gmail.com)
@link http://chikuyonok.ru

Gedit implementation:
@author Franck Marcia (franck.marcia@gmail.com)
'''

import zen_core, zen_actions
import os, re, locale
import zen_dialog

class ZenEditor():

    def __init__(self):
        self.last_wrap = ''
        self.last_expand = ''
        zen_core.set_caret_placeholder('')

    def set_context(self, context):
        """
        Setup underlying editor context. You should call this method before 
        using any Zen Coding action.
        @param context: context object
        """
        self.context = context # window
        self.buffer = self.context.get_active_view().get_buffer()
        self.view = context.get_active_view()
        self.document = context.get_active_document()
        
        default_locale = locale.getdefaultlocale()[0] if locale.getdefaultlocale()[0] else "en_US"
        lang = re.sub(r'_[^_]+$', '', default_locale)
        if lang != default_locale:
            zen_core.set_variable('lang', lang)
            zen_core.set_variable('locale', default_locale.replace('_', '-'))
        else:
            zen_core.set_variable('lang', default_locale)
            zen_core.set_variable('locale', default_locale)
        
        self.encoding = self.document.get_encoding().get_charset()
        zen_core.set_variable('charset', self.encoding)
        
        if self.view.get_insert_spaces_instead_of_tabs():
            zen_core.set_variable('indentation', " " * context.get_active_view().get_tab_width())
        else:
            zen_core.set_variable('indentation', "\t")
        
    def get_selection_range(self):
        """
        Returns character indexes of selected text
        @return: list of start and end indexes
        @example
        start, end = zen_editor.get_selection_range();
        print('%s, %s' % (start, end))
        """
        offset_start = self.get_insert_offset()
        offset_end = self.get_selection_bound_offset()
        if offset_start < offset_end:
            return offset_start, offset_end
        return offset_end, offset_start


    def create_selection(self, offset_start, offset_end=None):
        """
        Creates selection from start to end character indexes. If end is 
        omitted, this method should place caret and start index.
        @type start: int
        @type end: int
        @example
        zen_editor.create_selection(10, 40)
        # move caret to 15th character
        zen_editor.create_selection(15)
        """
        if offset_end is None:
            iter_start = self.buffer.get_iter_at_offset(offset_start)
            self.buffer.place_cursor(iter_start)
        else:
            iter_start = self.buffer.get_iter_at_offset(offset_start)
            iter_end = self.buffer.get_iter_at_offset(offset_end)
            self.buffer.select_range(iter_start, iter_end)

    def get_current_line_range(self):
        """
        Returns current line's start and end indexes
        @return: list of start and end indexes
        @example
        start, end = zen_editor.get_current_line_range();
        print('%s, %s' % (start, end))
        """
        iter_current = self.get_insert_iter()
        offset_start = self.buffer.get_iter_at_line(iter_current.get_line()).get_offset()
        offset_end = offset_start + iter_current.get_chars_in_line() - 1
        return offset_start, offset_end

    def get_caret_pos(self):
        """ Returns current caret position """
        return self.get_insert_offset()

    def set_caret_pos(self, pos):
        """
        Sets the new caret position
        @type pos: int
        """
        self.buffer.place_cursor(self.buffer.get_iter_at_offset(pos))

    def get_current_line(self):
        """
        Returns content of current line
        @return: str
        """
        offset_start, offset_end = self.get_current_line_range()
        iter_start = self.buffer.get_iter_at_offset(offset_start)
        iter_end = self.buffer.get_iter_at_offset(offset_end)
        return self.buffer.get_text(iter_start, iter_end, False).decode(self.encoding)

    def replace_content(self, value, offset_start=None, offset_end=None):
        """
        Replace editor's content or its part (from start to end index). If 
        value contains caret_placeholder, the editor will put caret into
        this position. If you skip start and end arguments, the whole target's 
        content will be replaced with value.

        If you pass start argument only, the value will be placed at start 
        string index of current content.

        If you pass start and end arguments, the corresponding substring of 
        current target's content will be replaced with value
        @param value: Content you want to paste
        @type value: str
        @param start: Start index of editor's content
        @type start: int
        @param end: End index of editor's content
        @type end: int
        """
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
        self.insertion_start = self.get_insert_offset()
        
        padding = zen_actions.get_current_line_padding(self)
        self.buffer.insert_at_cursor(zen_core.pad_string(value, padding))

        self.insertion_end = self.get_insert_offset()

    def get_content(self):
        """
        Returns editor's content
        @return: str
        """
        iter_start = self.buffer.get_iter_at_offset(0)
        iter_end = self.get_end_iter()
        return self.buffer.get_text(iter_start, iter_end, False).decode(self.encoding)

    def get_syntax(self):
        """
        Returns current editor's syntax mode
        @return: str
        """
        lang = self.context.get_active_document().get_language()
        lang = lang and lang.get_name()
        if lang == 'CSS': lang = 'css'
        elif lang == 'XSLT': lang = 'xsl'
        else: lang = 'html'
        return lang

    def get_profile_name(self):
        """
        Returns current output profile name (@see zen_coding#setup_profile)
        @return {String}
        """
        return 'xhtml'

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
        
    def start_edit(self):
        # Bug when the cursor is at the very beginning.
        if self.insertion_start == 0:
            self.insertion_start = 1
        self.set_caret_pos(self.insertion_start)
        if not self.next_edit_point() or (self.get_insert_offset() > self.insertion_end):
            self.set_caret_pos(self.insertion_end)
    
    def show_caret(self):
        self.view.scroll_mark_onscreen(self.buffer.get_insert())

    def get_user_settings_error(self):
        return zen_core.get_variable('user_settings_error')

    def expand_abbreviation(self, window):
        self.set_context(window)
        self.buffer.begin_user_action()
        result = zen_actions.expand_abbreviation(self)
        if result:
            self.start_edit()
        self.buffer.end_user_action()

    def save_selection(self):
        self.save_offset_insert = self.get_insert_offset()
        self.save_offset_selection_bound = self.get_selection_bound_offset()

    def restore_selection(self):
        iter_insert = self.buffer.get_iter_at_offset(self.save_offset_insert)
        iter_selection_bound = self.buffer.get_iter_at_offset(self.save_offset_selection_bound)
        self.buffer.select_range(iter_insert, iter_selection_bound)

    def do_expand_with_abbreviation(self, done, abbr):
        self.buffer.begin_user_action()
        if done:
            self.buffer.undo()
            self.restore_selection()
        content = zen_core.expand_abbreviation(abbr, self.get_syntax(), self.get_profile_name())
        if content:
            self.replace_content(content, self.get_insert_offset())
        self.buffer.end_user_action()
        return not not content

    def expand_with_abbreviation(self, window):
        self.set_context(window)
        self.save_selection()
        done, self.last_expand = zen_dialog.main(self, window, self.do_expand_with_abbreviation, self.last_expand)
        if done:
            self.start_edit()

    def do_wrap_with_abbreviation(self, done, abbr):
        self.buffer.begin_user_action()
        if done:
            self.buffer.undo()
            self.restore_selection()
        result = zen_actions.wrap_with_abbreviation(self, abbr)
        self.buffer.end_user_action()
        return result

    def wrap_with_abbreviation(self, window):
        self.set_context(window)
        self.save_selection()
        done, self.last_wrap = zen_dialog.main(self, window, self.do_wrap_with_abbreviation, self.last_wrap)
        if done:
            self.start_edit()

    def match_pair_inward(self, window):
        self.set_context(window)
        zen_actions.match_pair_inward(self)

    def match_pair_outward(self, window):
        self.set_context(window)
        zen_actions.match_pair_outward(self)

    def merge_lines(self, window):
        self.set_context(window)
        self.buffer.begin_user_action()
        result = zen_actions.merge_lines(self)
        self.buffer.end_user_action()
        return result

    def prev_edit_point(self, window=None):
        if window:
            self.set_context(window)
        result = zen_actions.prev_edit_point(self)
        self.show_caret()
        return result

    def next_edit_point(self, window=None):
        if window:
            self.set_context(window)
        result = zen_actions.next_edit_point(self)
        self.show_caret()
        return result

    def remove_tag(self, window):
        self.set_context(window)
        self.buffer.begin_user_action()
        result = zen_actions.remove_tag(self)
        self.buffer.end_user_action()
        return result

    def split_join_tag(self, window):
        self.set_context(window)
        self.buffer.begin_user_action()
        result = zen_actions.split_join_tag(self)
        self.buffer.end_user_action()
        return result

    def toggle_comment(self, window):
        self.set_context(window)
        self.buffer.begin_user_action()
        result = zen_actions.toggle_comment(self)
        self.buffer.end_user_action()
        return result

# -*- coding: utf-8 -*-
# Smart Indent Plugin
# Copyright © 2008 Alexandre da Silva
#
# This file is part of Gmate.
#
# See LICENTE.TXT for licence information

import gedit
import gtk
import gobject
import gconf
import re
import os

GLADE_FILE = os.path.join(os.path.dirname(__file__), "dialog.glade")

gconf_base_uri = u"/apps/gedit-2/plugins/smart_indent"
config_client = gconf.client_get_default()
config_client.add_dir(gconf_base_uri, gconf.CLIENT_PRELOAD_NONE)

tab_size_key_str   = "%s_tab_size"
use_spaces_key_str = "%s_use_spaces"
indent_key_str     = "%s_indent_regex"
unindent_key_str   = "%s_unindent_regex"
keystrokes_key_str = "%s_unindent_keystrokes"

default_tab_size_key   = "/apps/gedit-2/preferences/editor/tabs/tabs_size"
default_use_spaces_key = "/apps/gedit-2/preferences/editor/tabs/insert_spaces"

user_interface = """
<ui>
    <menubar name="MenuBar">
        <menu name="EditMenu" action="Edit">
            <placeholder name='EditOps_6'>
                <menuitem name="Smart Indent Configuration" action="SmartIndentConfiguration"/>
            </placeholder>
        </menu>
    </menubar>
</ui>
"""

default_indent_config = {
    "c_indent_regex"                    : r'(?!^\s*(#|//)).*(\b(if|while|for)\s*\(.*\)|\b(else|do)\b)[^{;]*$',
    "c_unindent_regex"                  : r'^\s*((case\b.*|[\p{Alpha}_][\p{Alnum}_]*)\s*:(?!:)).*$',
    "c_unindent_keystrokes"             : ":",

    "objc_indent_regex"                 : r'\s*(((if|while)\s*\(|else\s*|else\s+if\s*\(|for\s*\(.*\))[^{;]*)',
    "objc_unindent_regex"               : r'^.*(default:\s*|case.*:.*)$',
    "objc_unindent_keystrokes"          : ":",

    "java_indent_regex"                 : r'\s*(((if|while)\s*\(|else\s*|else\s+if\s*\(|for\s*\(.*\))[^{;]*)',
    "java_unindent_regex"               : r'^.*(default:\s*|case.*:.*)$',
    "java_unindent_keystrokes"          : ":",

    "perl_indent_regex"                 : r'[^#]*\.\s*$',
    "perl_unindent_regex"               : '',
    "perl_unindent_keystrokes"          : '',

    "ruby_indent_regex"                 : r'[^#]*\s+\bdo\b(\s*|(\s+\|.+\|\s*))|\s*(\bif\b\s+.*|\belsif\b.*|\belse\b.*|\bdo\b(\s*|\s+.*)|\bcase\b\s+.*|\bwhen\b\s+.*|\bwhile\b\s+.*|\bfor\b\s+.*|\buntil\b\s+.*|\bloop\b\s+.*|\bdef\b\s+.*|\bclass\b\s+.*|\bmodule\b\s+.*|\bbegin\b.*|\bunless\b\s+.*|\brescue\b.*|\bensure\b.*)+',
    "ruby_unindent_regex"               : r'^\s*(else.*|end\s*|elsif.*|rescue.*|when.*|ensure.*)$',
    "ruby_unindent_keystrokes"          : 'edfn',

    "rubyonrails_tab_size"              : 2,
    "rubyonrails_use_spaces"            : True,
    "rubyonrails_indent_regex"          : r'[^#]*\s+\bdo\b(\s*|(\s+\|.+\|\s*))|\s*(\bif\b\s+.*|\belsif\b.*|\belse\b.*|\bdo\b(\s*|\s+.*)|\bcase\b\s+.*|\bwhen\b\s+.*|\bwhile\b\s+.*|\bfor\b\s+.*|\buntil\b\s+.*|\bloop\b\s+.*|\bdef\b\s+.*|\bclass\b\s+.*|\bmodule\b\s+.*|\bbegin\b.*|\bunless\b\s+.*|\brescue\b.*|\bensure\b.*)+',
    "rubyonrails_unindent_regex"        : r'^\s*(else.*|end\s*|elsif.*|rescue.*|when.*|ensure.*)$',
    "rubyonrails_unindent_keystrokes"   : 'edfn',

    "python_tab_size"                   : 4,
    "python_use_spaces"                 : True,
    "python_indent_regex"               : r'\s*[^#]{3,}:\s*(#.*)?',
    "python_unindent_regex"             : r'^\s*(else|elif\s.*|except(\s.*)?|finally)\s*:',
    "python_unindent_keystrokes"        : ':',

    "javascript_indent_regex"           : r'\s*(((if|while)\s*\(|else\s*|else\s+if\s*\(|for\s*\(.*\))[^{;]*)',
    "javascript_unindent_regex"         : r'^.*(default:\s*|case.*:.*)$',
    "javascript_unindent_keystrokes"    : ':',

    "php_indent_regex"                  : r'\s*(((if|while|else\s*(if)?|for(each)?|switch|declare)\s*\(.*\)[^{:;]*)|(do\s*[^\({:;]*))',
    "php_unindent_regex"                : r'^.*(default:\s*|case.*:.*)$',
    "php_unindent_keystrokes"           : ':'
}

def get_tab_size_from_config(lang):
    tab_size_key = tab_size_key_str % lang
    r_tab_size = config_client.get_int(os.path.join(gconf_base_uri, tab_size_key))
    if r_tab_size == None or r_tab_size == 0:
        if default_indent_config.has_key(tab_size_key):
            r_tab_size = default_indent_config[tab_size_key]
    return r_tab_size or ''

def get_use_spaces_from_config(lang):
    use_spaces_key = use_spaces_key_str % lang
    r_use_spaces = config_client.get_bool(os.path.join(gconf_base_uri, use_spaces_key))
    if r_use_spaces == None or not r_use_spaces:
        if default_indent_config.has_key(use_spaces_key):
            r_use_spaces = default_indent_config[use_spaces_key]
    return r_use_spaces or ''

def get_indent_regex_from_config(lang):
    indent_key = indent_key_str % lang
    r_indent = config_client.get_string(os.path.join(gconf_base_uri, indent_key))
    if r_indent == None:
        if default_indent_config.has_key(indent_key):
            r_indent = default_indent_config[indent_key]
    return r_indent or ''

def get_unindent_regex_from_config(lang):
    unindent_key = unindent_key_str % lang
    r_unindent = config_client.get_string(os.path.join(gconf_base_uri, unindent_key))
    if r_unindent == None:
        if default_indent_config.has_key(unindent_key):
            r_unindent = default_indent_config[unindent_key]
    return r_unindent or ''

def get_unindent_keystrokes_from_config(lang):
    keystrokes_key = keystrokes_key_str % lang
    u_keystrokes = config_client.get_string(os.path.join(gconf_base_uri, keystrokes_key))
    if u_keystrokes == None:
        if default_indent_config.has_key(keystrokes_key):
            u_keystrokes = default_indent_config[keystrokes_key]
    return u_keystrokes or ''


class SmartIndentPlugin(gedit.Plugin):
    handler_ids = []

    def __init__(self):
        gedit.Plugin.__init__(self)
        self.instances = {}

    def activate(self, window):
        view = window.get_active_view()
        self.instances[window] = ConfigurationWindowHelper(self, window)

        actions = [
            ('SmartIndentConfiguration', None, _('Smart Indent Configuration'), '<Control><Alt><Shift>t', _("Configure smart indent settings for this language"), self.run_dialog)
        ]

        action_group = gtk.ActionGroup("TabConfigurationActions")
        action_group.add_actions(actions, window)

        self.manager = window.get_ui_manager()
        self.manager.insert_action_group(action_group, -1)
        self.manager.add_ui_from_string(user_interface)

        self.setup_smart_indent(view, 'plain_text')

    def deactivate(self, window):
        for (handler_id, view) in self.handler_ids:
            if view.handler_is_connected(handler_id):
                view.disconnect(handler_id)

        self.instances[window].deactivate()

    def run_dialog(self, action, window):
        self.instances[window].configuration_dialog()

    def update_ui(self, window):
        view = window.get_active_view()
        lang = 'plain_text'
        if view:
            buf = view.get_buffer()
            language = buf.get_language()
            if language:
                lang = language.get_id()
        self.setup_smart_indent(view, lang)

    def setup_smart_indent(self, view, lang):
        # Configure a "per-view" instance
        if type(view) == gedit.View:
            if getattr(view, 'smart_indent_instance', False) == False:
                setattr(view, 'smart_indent_instance', SmartIndent())
                handler_id = view.connect('key-press-event', view.smart_indent_instance.key_press_handler)
                self.handler_ids.append((handler_id, view))
            view.smart_indent_instance.set_language(lang, view)


class ConfigurationWindowHelper:

    def __init__(self, plugin, window):
        self.window = window
        self.plugin = plugin
        self.dialog = None

    def configuration_dialog(self):
        glade_xml = gtk.glade.XML(GLADE_FILE)
        if self.dialog:
            self.dialog.set_focus(True)
            return

        self.dialog = glade_xml.get_widget('config_dialog')
        self.dialog.connect('delete_event', self.on_close)
        self.dialog.show_all()
        self.dialog.set_transient_for(self.window)

        self.btn_cancel = glade_xml.get_widget('btn_cancel')
        self.btn_cancel.connect('clicked', self.on_cancel)

        self.btn_apply = glade_xml.get_widget('btn_apply')
        self.btn_apply.connect('clicked', self.on_apply)

        # Get data from current document, not from configuration, because user
        # may want to save current options
        view = self.window.get_active_view()

        self.language = view.get_buffer().get_language()
        if self.language:
            lang_name = self.language.get_name()
            self.lang_id = self.language.get_id()
        else:
            lang_name = _(u'Plain Text')
            self.lang_id = 'plain_text'

        use_spaces = view.get_insert_spaces_instead_of_tabs()
        tab_size = view.get_tab_width()

        self.lbl_language = glade_xml.get_widget('lbl_language')
        self.lbl_language.set_markup("Language: <b>%s</b>" % lang_name)

        self.edt_size = glade_xml.get_widget('edt_size')
        self.edt_size.set_value(get_tab_size_from_config(self.lang_id) or tab_size)

        self.cbx_use_spaces = glade_xml.get_widget('cbx_use_spaces')
        self.cbx_use_spaces.set_active(get_use_spaces_from_config(self.lang_id) or use_spaces)

        self.edt_indent_regex = glade_xml.get_widget('edt_indent_regex')
        self.edt_indent_regex.set_text(get_indent_regex_from_config(self.lang_id) or '')

        self.edt_unindent_regex = glade_xml.get_widget('edt_unindent_regex')
        self.edt_unindent_regex.set_text(get_unindent_regex_from_config(self.lang_id) or '')

        self.edt_unindent_keystrokes = glade_xml.get_widget('edt_unindent_keystrokes')
        self.edt_unindent_keystrokes.set_text(get_unindent_keystrokes_from_config(self.lang_id) or '')


    def close_dialog(self):
        self.dialog.destroy()
        self.dialog = None
        self.size_picker = None
        self.use_spaces_check = None

    def on_close(self, *args):
        self.close_dialog()

    def on_cancel(self, *args):
        self.close_dialog()

    def deactivate(self):
        self.window = None
        self.plugin = None

    def on_apply(self, *args):
        view = self.window.get_active_view()

        buf = view.get_buffer()

        size = self.edt_size.get_value_as_int()
        use_spaces = self.cbx_use_spaces.get_active()
        indent_regex = self.edt_indent_regex.get_text()
        unindent_regex = self.edt_unindent_regex.get_text()
        unindent_keystrokes = self.edt_unindent_keystrokes.get_text()

        tab_size_key = tab_size_key_str % self.lang_id
        use_spaces_key = use_spaces_key_str % self.lang_id
        indent_key = indent_key_str % self.lang_id
        unindent_key = unindent_key_str % self.lang_id
        keystrokes_key = keystrokes_key_str % self.lang_id

        config_client.set_int(os.path.join(gconf_base_uri,tab_size_key), size)
        config_client.set_bool(os.path.join(gconf_base_uri,use_spaces_key), use_spaces)
        config_client.set_string(os.path.join(gconf_base_uri,indent_key), indent_regex)
        config_client.set_string(os.path.join(gconf_base_uri,unindent_key), unindent_regex)
        config_client.set_string(os.path.join(gconf_base_uri,keystrokes_key), unindent_keystrokes)

#		It's already being done in SmartIndent set_language method
#        view.set_insert_spaces_instead_of_tabs(use_spaces)
#        view.set_tab_width(size)
        if getattr(view, 'smart_indent_instance', False):
            view.smart_indent_instance.set_language(self.lang_id, view)

        self.close_dialog()


class SmartIndent:

    def __init__(self):
        self.__not_available = True
        self.__line_unindented = -1
        self.__line_no = -1
        self.clear_variables()
        return

    def clear_variables(self):
        self.re_indent_next      = None
        self.re_unindent_curr    = None
        self.unindent_keystrokes = None

    def set_indent_config(self, lang):
        self.clear_variables()
        r_indent = get_indent_regex_from_config(lang)
        r_unindent = get_unindent_regex_from_config(lang)
        u_keystrokes = get_unindent_keystrokes_from_config(lang)
        if r_indent:
            self.re_indent_next = re.compile(r_indent)
        if r_unindent:
            self.re_unindent_curr = re.compile(r_unindent)
        if u_keystrokes:
            self.unindent_keystrokes = u_keystrokes
        # Return configured if some of the options is present
        if r_indent or r_unindent or u_keystrokes:
            return True
        else:
            return False

    def set_language(self, lang, view):
        self.__not_available = not self.set_indent_config(lang)
        # Defaults
        tab_size = get_tab_size_from_config(lang) or 4
        use_spaces = get_use_spaces_from_config(lang) or True
        # Set the buffer tab configuration
        view.set_tab_width(tab_size)
        view.set_insert_spaces_instead_of_tabs(use_spaces)
        # Update in configuration
        config_client.set_int(default_tab_size_key, tab_size)
        config_client.set_bool(default_use_spaces_key, use_spaces)


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
        elif self.unindent_keystrokes:
            if keyval in [ord(k) for k in self.unindent_keystrokes]:
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


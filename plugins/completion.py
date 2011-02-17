# Copyright (C) 2006-2008 Osmo Salomaa
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

"""Complete words with the tab key.

This plugin provides a 'stupid' word completion plugin, one that is aware of
all words in all open documents, but knows nothing of any context or syntax.
This plugin can be used to speed up writing and to avoid spelling errors in
either regular text documents or in programming documents if no programming
language -aware completion is available.

Words are automatically scanned at regular intervals. Once you have typed a
word and the interval has passed, the word is available in the completion
system. A completion window listing possible completions is shown and updated
as you type. You can complete to the topmost word in the window with the Tab
key, or choose another completion with the arrow keys and complete with the Tab
key. The keybindinds are configurable only by editing the source code.
"""

import gedit
import gobject
import gtk
import pango
import re
from lib import sgconf # gmate lib

class CompletionWindow(gtk.Window):

    """Window for displaying a list of words to complete to.

    This is a popup window merely to display words. This window is not meant
    to receive or handle input from the user, rather the various methods should
    be called to chang the list of words and which one of them is selected.
    """

    def __init__(self, parent):

        gtk.Window.__init__(self, gtk.WINDOW_POPUP)
        self._store = None
        self._view = None
        self._moved = False
        self.set_transient_for(parent)
        self._init_view()
        self._init_containers()

    def _init_containers(self):
        """Initialize the frame and the scrolled window."""

        scroller = gtk.ScrolledWindow()
        scroller.set_policy(*((gtk.POLICY_NEVER,) * 2))
        scroller.add(self._view)
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_OUT)
        frame.add(scroller)
        self.add(frame)

    def _init_view(self):
        """Initialize the tree view listing the complete words."""

        self._store = gtk.ListStore(gobject.TYPE_STRING)
        self._view = gtk.TreeView(self._store)
        renderer = gtk.CellRendererText()
        renderer.xpad = renderer.ypad = 6
        column = gtk.TreeViewColumn("", renderer, text=0)
        self._view.append_column(column)
        self._view.set_enable_search(False)
        self._view.set_headers_visible(False)
        self._view.set_rules_hint(True)
        selection = self._view.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)

    def get_selected(self):
        """Return the index of the selected row."""

        selection = self._view.get_selection()
        self._moved = False
        return selection.get_selected_rows()[1][0][0]

    def select_next(self):
        """Select the next complete word."""

        row = min(self.get_selected() + 1, len(self._store) - 1)
        selection = self._view.get_selection()
        selection.unselect_all()
        selection.select_path(row)
        self._moved = True
        self._view.scroll_to_cell(row)

    def select_previous(self):
        """Select the previous complete word."""

        row = max(self.get_selected() - 1, 0)
        selection = self._view.get_selection()
        selection.unselect_all()
        selection.select_path(row)
        self._moved = True
        self._view.scroll_to_cell(row)

    def set_completions(self, completions):
        """Set the completions to display."""

        # 'gtk.Window.resize' followed later by 'gtk.TreeView.columns_autosize'
        # will allow the window to either grow or shrink to fit the new data.
        self.resize(1, 1)
        self._store.clear()
        for word in completions:
            self._store.append((word,))
        self._view.columns_autosize()
        self._view.get_selection().select_path(0)

    def set_font_description(self, font_desc):
        """Set the font description used in the view."""

        self._view.modify_font(font_desc)

class Settings(sgconf.Options):
    _uri = u"/apps/gedit-2/plugins/completion"

    max_completions_show = sgconf.IntOption(6)
    enter_behaviour_mode = sgconf.StringOption('complete')

class CompletionConfigDialog(gtk.Dialog):
    Title = 'Completion plugin settings'
    MaxCompletionsShow = 'Maximum suggestions for show:'
    # two variants of completion works:
    OnEnterComplete = ('Completion on enter, new line on <mod> + enter', 'complete')
    OnEnterNewLine =  ('Completion after select suggestion in popup menu', 'newline')
    EnterBehaviourKey = 'behaviour'
    EnterBehaviourFrameText = "<b>Behaviour for key 'enter':</b>"

    def __init__(self, settings):
        gtk.Dialog.__init__(self, self.Title, None, gtk.DIALOG_DESTROY_WITH_PARENT)
        self._settings = settings
        self.set_resizable(False)
        mainbox = gtk.VBox()
        mainbox.set_border_width(10)
        mainbox.set_spacing(10)
        
        close_button = self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        close_button.grab_default()
        close_button.connect('clicked', self.on_close, None)
        
        # Enter Behaviour frame
        frame = gtk.Frame(self.EnterBehaviourFrameText)
        frame.set_shadow_type(gtk.SHADOW_NONE)
        frame.get_label_widget().set_use_markup(True)

        scope_box = gtk.VBox(False, 0)
        scope_box.set_border_width(5)
        def entermode_radio(text, mode, group=None):
            btn = gtk.RadioButton(group, text)
            btn.set_data(self.EnterBehaviourKey, mode)
            btn.connect('toggled', self.enter_mode_change)
            btn.set_active(self._settings.enter_behaviour_mode == mode)
            scope_box.pack_start(btn)
            return btn
        btn1 = entermode_radio(*self.OnEnterComplete)
        btn2 = entermode_radio(*(self.OnEnterNewLine +  (btn1, )))
        frame.add(scope_box)
        mainbox.pack_start(frame)
        
        # Max Completions frame
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_NONE)
        hbox = gtk.HBox()
        hbox.set_spacing(10)
        label = gtk.Label(self.MaxCompletionsShow)
        label.set_use_markup(True)

        # gtk.Adjustment(value=0, lower=0, upper=0, step_incr=0, page_incr=0,
        # page_size=0)
        adj = gtk.Adjustment(self._settings.max_completions_show, 1, 60, 1, 5)
        self._max_compl_show = gtk.SpinButton(adj)

        hbox.pack_start(label)
        hbox.pack_start(self._max_compl_show)
        frame.add(hbox)
        mainbox.pack_start(frame)

        # Show
        self.vbox.pack_start(mainbox)
        self.vbox.show_all()
        self.show()

    def on_close(self, widget, data=None):
        self._settings.max_completions_show = self._max_compl_show.get_value_as_int()
        gtk.Widget.destroy(self)

    def enter_mode_change(self, widget):
        mode = widget.get_data(self.EnterBehaviourKey)
        if mode is not None and mode in ('complete', 'newline'):
            self._settings.enter_behaviour_mode = mode


class CompletionPlugin(gedit.Plugin):

    """Complete words with the tab key.

    Instance variables are as follows. '_completion_windows' is a dictionary
    mapping 'gedit.Windows' to 'CompletionWindows'.

    '_all_words' is a dictionary mapping documents to a frozen set containing
    all words in the document. '_favorite_words' is a dictionary mapping
    documents to a set of words that the user has completed to. Favorites are
    thus always document-specific and there are no degrees to favoritism. These
    favorites will be displayed at the top of the completion window. As
    '_all_words' and '_favorite_words' are both sets, the exact order in which
    the words are listed in the completion window is unpredictable.

    '_completions' is a list of the currently active complete words, shown in
    the completion window, that the user can complete to. Similarly '_remains'
    is a list of the untyped parts the _completions, i.e. the part that will be
    inserted when the user presses the Tab key. '_completions' and '_remains'
    always contain words for the gedit window, document and text view that has
    input focus.

    '_font_ascent' is the ascent of the font used in gedit's text view as
    reported by pango. It is needed to be able to properly place the completion
    window right below the caret regardless of the font and font size used.
    """

    # Unlike gedit itself, consider underscores alphanumeric characters
    # allowing completion of identifier names in many programming languages.
    _re_alpha = re.compile(r"\w+", re.UNICODE | re.MULTILINE)
    _re_non_alpha = re.compile(r"\W+", re.UNICODE | re.MULTILINE)

    # TODO: Are these sane defaults?
    _scan_frequency = 10000 # ms

    def __init__(self):

        gedit.Plugin.__init__(self)
        self._all_words = {}
        self._completion_windows = {}
        self._completions = []
        self._favorite_words = {}
        self._font_ascent = 0
        self._remains = []
        self._settings = Settings()

    def is_configurable(self):
        return True

    def create_configure_dialog(self):
        self._config_dialog = CompletionConfigDialog(self._settings)
        return self._config_dialog

    def _complete_current(self):
        """Complete the current word."""

        window = gedit.app_get_default().get_active_window()
        doc = window.get_active_document()
        index = self._completion_windows[window].get_selected()
        doc.insert_at_cursor(self._remains[index])
        words = self._favorite_words.setdefault(doc, set(()))
        words.add(self._completions[index])
        self._terminate_completion()

    def _connect_document(self, doc):
        """Connect to document's 'loaded' signal."""

        callback = lambda doc, x, self: self._scan_document(doc)
        handler_id = doc.connect("loaded", callback, self)
        doc.set_data(self.__class__.__name__, (handler_id,))

    def _connect_view(self, view, window):
        """Connect to view's editing signals."""

        callback = lambda x, y, self: self._terminate_completion()
        id_1 = view.connect("focus-out-event", callback, self)
        callback = self._on_view_key_press_event
        id_2 = view.connect("key-press-event", callback, window)
        view.set_data(self.__class__.__name__, (id_1, id_2))

    def _display_completions(self, view, event):
        """Find completions and display them in the completion window."""

        doc = view.get_buffer()
        insert = doc.get_iter_at_mark(doc.get_insert())
        start = insert.copy()
        while start.backward_char():
            char = unicode(start.get_char())
            if not self._re_alpha.match(char):
                start.forward_char()
                break
        incomplete = unicode(doc.get_text(start, insert))
        incomplete += unicode(event.string)
        if incomplete.isdigit():
            # Usually completing numbers is not a good idea.
            return self._terminate_completion()
        self._find_completions(doc, incomplete)
        if not self._completions:
            return self._terminate_completion()
        self._show_completion_window(view, insert)

    def _find_completions(self, doc, incomplete):
        """Find completions for incomplete word and save them."""

        self._completions = []
        self._remains = []
        favorites = self._favorite_words.get(doc, ())
        _all_words = set(())
        for words in self._all_words.itervalues():
            _all_words.update(words)
        limit = self._settings.max_completions_show
        for sequence in (favorites, _all_words):
            for word in sequence:
                if not word.startswith(incomplete): continue
                if word == incomplete: continue
                if word in self._completions: continue
                self._completions.append(word)
                self._remains.append(word[len(incomplete):])
                if len(self._remains) >= limit: break

    def _check_by_completion_moved(self, moved):
        if self._settings.enter_behaviour_mode == 'newline':
            return moved
        return True

    def _on_view_key_press_event(self, view, event, window):
        """Manage actions for completions and the completion window."""

        if event.state & gtk.gdk.CONTROL_MASK:
            return self._terminate_completion()
        if event.state & gtk.gdk.SUPER_MASK:
            return self._terminate_completion()
        if event.state & gtk.gdk.MOD1_MASK:
            return self._terminate_completion()

        completion_window = self._completion_windows[window]
        if (event.keyval == gtk.keysyms.Return) and self._remains and \
                self._check_by_completion_moved(completion_window._moved):
            return not self._complete_current()
        
        if (event.keyval == gtk.keysyms.Up) and self._remains:
            return not completion_window.select_previous()
        if (event.keyval == gtk.keysyms.Down) and self._remains:
            return not completion_window.select_next()
        string = unicode(event.string)
        if len(string) != 1:
            # Do not suggest completions after pasting text.
            return self._terminate_completion()
        if self._re_alpha.match(string) is None:
            return self._terminate_completion()
        doc = view.get_buffer()
        insert = doc.get_iter_at_mark(doc.get_insert())
        if self._re_alpha.match(unicode(insert.get_char())):
            # Do not suggest completions in the middle of a word.
            return self._terminate_completion()
        return self._display_completions(view, event)

    def _on_window_tab_added(self, window, tab):
        """Connect to signals of the document and view in tab."""

        self._update_fonts(tab.get_view())
        name = self.__class__.__name__
        doc = tab.get_document()
        handler_id = doc.get_data(name)
        if handler_id is None:
            self._connect_document(doc)
        view = tab.get_view()
        handler_id = view.get_data(name)
        if handler_id is None:
            self._connect_view(view, window)

    def _on_window_tab_removed(self, window, tab):
        """Remove closed document's word and favorite sets."""

        doc = tab.get_document()
        self._all_words.pop(doc, None)
        self._favorite_words.pop(doc, None)

    def _scan_active_document(self, window):
        """Scan all the words in the active document in window."""

        # Return False to not scan again.
        if window is None: return False
        doc = window.get_active_document()
        if doc is not None:
            self._scan_document(doc)
        return True

    def _scan_document(self, doc):
        """Scan and save all words in document."""

        text = unicode(doc.get_text(*doc.get_bounds()))
        self._all_words[doc] = frozenset(self._re_non_alpha.split(text))

    def _show_completion_window(self, view, itr):
        """Show the completion window below the caret."""

        text_window = gtk.TEXT_WINDOW_WIDGET
        rect = view.get_iter_location(itr)
        x, y = view.buffer_to_window_coords(text_window, rect.x, rect.y)
        window = gedit.app_get_default().get_active_window()
        x, y = view.translate_coordinates(window, x, y)
        x += window.get_position()[0] + self._font_ascent
        # Use 24 pixels as an estimate height for window title bar.
        # TODO: There must be a better way than a hardcoded pixel value.
        y += window.get_position()[1] + 24 + (2 * self._font_ascent)
        completion_window = self._completion_windows[window]
        completion_window.set_completions(self._completions)
        completion_window.move(int(x), int(y))
        completion_window.show_all()

    def _terminate_completion(self):
        """Hide the completion window and cancel completions."""

        window = gedit.app_get_default().get_active_window()
        self._completion_windows[window].hide()
        self._completions = []
        self._remains = []

    def _update_fonts(self, view):
        """Update font descriptions and ascent metrics."""

        context = view.get_pango_context()
        font_desc = context.get_font_description()
        if self._font_ascent == 0:
            # Acquiring pango metrics is a bit slow,
            # so do this only when absolutely needed.
            metrics = context.get_metrics(font_desc, None)
            self._font_ascent = metrics.get_ascent() / pango.SCALE
        for completion_window in self._completion_windows.itervalues():
            completion_window.set_font_description(font_desc)

    def activate(self, window):
        """Activate plugin."""

        callback = self._on_window_tab_added
        id_1 = window.connect("tab-added", callback)
        callback = self._on_window_tab_removed
        id_2 = window.connect("tab-removed", callback)
        window.set_data(self.__class__.__name__, (id_1, id_2))
        for doc in window.get_documents():
            self._connect_document(doc)
            self._scan_document(doc)
        views = window.get_views()
        for view in views:
            self._connect_view(view, window)
        if views: self._update_fonts(views[0])
        self._completion_windows[window] = CompletionWindow(window)
        # Scan the active document in window if it has input focus
        # for new words at constant intervals.
        def scan(self, window):
            if not window.is_active(): return True
            return self._scan_active_document(window)
        freq = self._scan_frequency
        priority = gobject.PRIORITY_LOW
        gobject.timeout_add(freq, scan, self, window, priority=priority)

    def deactivate(self, window):
        """Deactivate plugin."""

        widgets = [window]
        widgets.extend(window.get_views())
        widgets.extend(window.get_documents())
        name = self.__class__.__name__
        for widget in widgets:
            for handler_id in widget.get_data(name):
                widget.disconnect(handler_id)
            widget.set_data(name, None)
        self._terminate_completion()
        self._completion_windows.pop(window)
        for doc in window.get_documents():
            self._all_words.pop(doc, None)
            self._favorite_words.pop(doc, None)

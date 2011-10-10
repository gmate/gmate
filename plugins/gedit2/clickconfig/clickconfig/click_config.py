# -*- coding: utf8 -*-
#  Click Config  plugin for Gedit
#
#  Copyright (C) 2010 Derek Veit
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module provides the plugin object that Gedit interacts with.

Classes:
ClickConfigPlugin       -- object is loaded once by an instance of Gedit
ClickConfigWindowHelper -- object is constructed for each Gedit window

Each time the same Gedit instance makes a new window, Gedit calls the
plugin's activate method.  Each time ClickConfigPlugin is so activated,
it constructs a ClickConfigWindowHelper object to handle the new window.

Settings common to all Gedit windows are attributes of ClickConfigPlugin.
Settings specific to one window are attributes of ClickConfigWindowHelper.

"""

import itertools
import os
import re
import sys
import time

import gedit
import gtk
import gtksourceview2

from .data import SelectionOp, ConfigSet, Config
from .ui import ConfigUI
from .logger import Logger
LOGGER = Logger(level=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')[2])

class ClickConfigPlugin(gedit.Plugin):
    
    """
    An object of this class is loaded once by a Gedit instance.
    
    It establishes and maintains the configuration data, and it creates
    a ClickConfigWindowHelper object for each Gedit main window.
    
    Public methods:
    activate                -- Gedit calls this to start the plugin.
    deactivate              -- Gedit calls this to stop the plugin.
    update_ui               -- Gedit calls this at certain times when
                               the ui changes.
    is_configurable         -- Gedit calls this to check if the plugin
                               is configurable.
    create_configure_dialog -- Gedit calls this when "Configure" is
                               selected in the Preferences Plugins tab.
                               Also, ClickConfigWindowHelper calls this
                               when Edit > Click Config > Configure is
                               selected.
    update_configuration    -- The ConfigUI object calls this when Apply
                               or OK is clicked on the configuration
                               window.
    open_config_dir         -- Opens a Nautilus window of the
                               configuration file's directory.  This is
                               called by the ConfigUI object when the
                               Browse button is clicked.
    get_gedit_window        -- Returns the current Gedit window.
    
    """
    
    def __init__(self):
        """Initialize plugin attributes."""
        LOGGER.log()
        
        gedit.Plugin.__init__(self)
        
        self._instances = {}
        """Each Gedit window will get a ClickConfigWindowHelper instance."""
        
        self.plugin_path = None
        """The directory path of this file and the configuration file."""
        
        self.config_ui = None
        """This will identify the (singular) ConfigUI object."""
        
        self.conf = None
        """This object contains all the settings."""
    
    def activate(self, window):
        """Start a ClickConfigWindowHelper instance for this Gedit window."""
        LOGGER.log()
        if not self._instances:
            LOGGER.log('Click Config activating.')
            self.conf = Config(self)
            self.set_conf_defaults()
            self.plugin_path = os.path.dirname(os.path.realpath(__file__))
            self.conf.filename = os.path.join(self.plugin_path,
                                                 'click_config_configs')
            if os.path.exists(self.conf.filename):
                self.conf.load()
            self.conf.check_language_configsets()
        self._instances[window] = ClickConfigWindowHelper(self, window)
        self._instances[window].activate()
    
    def deactivate(self, window):
        """End the ClickConfigWindowHelper instance for this Gedit window."""
        LOGGER.log()
        self._instances[window].deactivate()
        self._instances.pop(window)
        if not self._instances:
            self.conf = None
            self.config_ui = None
            self.plugin_path = None
            LOGGER.log('Click Config deactivated.')
    
    def update_ui(self, window):
        """Forward Gedit's update_ui command for this window."""
        LOGGER.log()
        self._instances[window].update_ui()
    
    def is_configurable(self):
        """Identify for Gedit that Click Config is configurable."""
        LOGGER.log()
        return True
    
    def create_configure_dialog(self):
        """Produce the configuration window and provide it to Gedit."""
        LOGGER.log()
        if self.config_ui:
            self.config_ui.window.present()
        else:
            self.config_ui = ConfigUI(self)
        return self.config_ui.window
    
    def set_conf_defaults(self):
        """
        Set the configuration to initial default values.
        These values get replaced if there is a configuration file.
        """
        LOGGER.log()
        self.conf.ops = [
            SelectionOp('None',
                preserved=True),
            SelectionOp('Gedit word',
                pattern='[a-zA-Z]+|[0-9]+|[^a-zA-Z0-9]+',
                preserved=True),
            SelectionOp('GNOME Terminal default',
                pattern='[-A-Za-z0-9,./?%&#:_]+'),
            SelectionOp('Line',
                pattern='.*',
                preserved=True),
            SelectionOp('Line+',
                pattern='^.*\\n',
                flags=re.M,
                preserved=True),
            SelectionOp('Python name',
                pattern='[_a-zA-Z][_a-zA-Z0-9]*',
                preserved=True),
            SelectionOp('Paragraph',
                pattern=('(?: ^ (?:  [ \\t]*  \\S+  [ \\t]*  )  +  \\n  )+'
                 '  # \xe2\x9c\x94X allows comment'),
                flags=(re.M + re.X)),
            SelectionOp('Paragraph+',
                pattern='(?:^(?:[ \\t]*\\S+[ \\t]*)+\\n)+(?:[ \\t]*\\n)?',
                flags=re.M,
                preserved=True),
            SelectionOp('Python name 2',
                pattern='[_a-z][_.a-z0-9]*',
                flags=re.I),
            ]
        self.conf.configsets = [
            ConfigSet('Gedit built-in',
                op_names=[
                    'None',
                    'Gedit word',
                    'Line',
                    'None',
                    'None',
                    ],
                preserved=True),
            ConfigSet('Click Config default',
                op_names=[
                    'None',
                    'Gedit word',
                    'Python name',
                    'Line+',
                    'Paragraph+',
                    ],
                preserved=True),
            ConfigSet('Custom',
                op_names=[
                    'None',
                    'Gedit word',
                    'Python name',
                    'Line+',
                    'Paragraph+',
                    ]),
            ]
        self.conf.current_configset_name = 'Custom'
        self.conf.current_op_name = 'None'
        self.conf.languages = {
            '-None-': 'Click Config default',
            'Python': 'Custom',
            }
        self.conf.is_set_by_language = False
    
    def update_configuration(self, conf):
        """Adopt the provided configuration and save it."""
        LOGGER.log()
        self.conf = conf
        self.conf.save()
        for window in self._instances:
            self._instances[window].update_menu()
        LOGGER.log('Configuration updated.')
    
    def open_config_dir(self):
        """Open a Nautilus window of the configuration file's directory."""
        LOGGER.log()
        import subprocess
        directory = os.path.dirname(self.conf.filename)
        args = ['nautilus', directory]
        subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    def get_gedit_window(self):
        """
        Return the current Gedit window.
        ConfigUI uses this to identify its parent window.
        """
        LOGGER.log()
        return gedit.app_get_default().get_active_window()
    
    def _get_languages(self):
        """Return a list of the languages known to Gedit."""
        LOGGER.log()
        gtk_lang_mgr = gtksourceview2.language_manager_get_default()
        language_ids = gtk_lang_mgr.get_language_ids()
        language_names = []
        for language_id in language_ids:
            language = gtk_lang_mgr.get_language(language_id)
            language_names.append(language.get_name())
        language_names.sort(lambda a, b:
                                cmp(a.lower(), b.lower()))
        return language_names
    
    def _get_languages_by_section(self):
        """Return a dictionary of the languages known to Gedit, grouped."""
        LOGGER.log()
        gtk_lang_mgr = gtksourceview2.language_manager_get_default()
        language_ids = gtk_lang_mgr.get_language_ids()
        languages_by_section = {}
        for language_id in language_ids:
            language = gtk_lang_mgr.get_language(language_id)
            section = language.get_section()
            name = language.get_name()
            if section in languages_by_section:
                languages_by_section[section].append(name)
            else:
                languages_by_section[section] = [name]
        for section in languages_by_section:
            languages_by_section[section].sort(lambda a, b:
                                                cmp(a.lower(), b.lower()))
        return languages_by_section

class ClickConfigWindowHelper(object):
    
    """
    ClickConfigPlugin creates a ClickConfigWindowHelper object for each
    Gedit window.  This object receives mouse and menu inputs from the
    Gedit window and responds by selecting text, or if the menu item is
    for Configuration, it calls the plugin's method to open the
    configuration window.
    
    Public methods:
    deactivate         -- ClickConfigPlugin calls this when Gedit calls
                          deactivate for this window.
    open_config_window -- calls ClickConfigPlugin method to open the
                          configuration window.
    update_ui          -- ClickConfigPlugin calls this when Gedit calls
                          update_ui for this window.  It activates the
                          menu for the Gedit window and connects the
                          mouse event handler to the current View.
                          Also, ClickConfigWindowHelper.__init_ calls
                          this.
    on_scrollwin_add   -- update_ui connects this to the 'add' event of
                          a new ScrolledWindow it finds in order to find
                          out about a new Viewport created by the Split
                          View plugin.
    on_viewport_add    -- on_scrollwin_add connects this to the 'add'
                          event of a new Viewport it finds in order to
                          find out about new views created by the Split
                          View plugin.  When called, it calls update_ui
                          to connect the mouse event handler to both
                          views.
    
    """
    
    def __init__(self, plugin, window):
        """Initialize values of this Click Config instance."""
        LOGGER.log()
        
        self._window = window
        """The window this ClickConfigWindowHelper runs on."""
        self._plugin = plugin
        """The ClickConfigPlugin that spawned this ClickConfigWindowHelper."""
        
        LOGGER.log('Started for %s' % self._window)
        
        self._ui_id = None
        """The menu's UI identity, saved for removal."""
        self._action_group = None
        """The menu's action group, saved for removal."""
        
        self._time_of_last_click = [None, 0, 0, 0, 0, 0]
        """Times of the most recent clicks for each of the five click types."""
        
        gtk_settings = gtk.settings_get_default()
        gtk_doubleclick_ms = gtk_settings.get_property('gtk-double-click-time')
        self._double_click_time = float(gtk_doubleclick_ms)/1000
        """Maximum time between consecutive clicks in a multiple click."""
        
        self._mouse_handler_ids_per_view = {}
        """The mouse handler id for each of the window's views."""
        
        self._key_handler_ids_per_view = {}
        """The key_press handler id for each of the window's views."""
        
        self._handlers_per_scrollwin = {}
        """A special 'add' signal handler for each ScrolledWindow found."""
        self._handlers_per_viewport = {}
        """A special 'add' signal handler for each Viewport found."""
        
        self._drag_handler_ids = ()
        """Motion and button-release handlers for drag selecting."""
        
        # These attributes are used for extending the selection for click-drag.
        self._word_re = None
        """The compiled regular expression object of the current click."""
        self._boundaries = None
        """All start and end positions of matches of the current click."""
        self._click_start_iter = None
        """Start iter of the clicked selection."""
        self._click_end_iter = None
        """End iter of the clicked selection."""
    
    def _insert_menu(self):
        """Create the Click Config submenu under the Edit menu."""
        LOGGER.log()
        
        actions = []
        
        name = 'ClickConfig'
        stock_id = None
        label = 'Click Config'
        actions.append((name, stock_id, label))
        
        name = 'Configure'
        stock_id = None
        label = 'Configure'
        accelerator = '<Control>b'
        tooltip = 'Configure Click Config'
        callback = lambda action: self.open_config_window()
        actions.append((name, stock_id, label, accelerator, tooltip, callback))
        
        op_menuitems = ''
        for op_name in self._plugin.conf.get_op_names()[1:]:
            # Iterating get_op_names ensures that the names are sorted.
            op = self._plugin.conf.get_op(op_name=op_name)
            name = op.name
            stock_id = None
            label = op.name
            accelerator = ''
            flag_text =  ' I' * bool(op.flags & re.I)
            flag_text += ' M' * bool(op.flags & re.M)
            flag_text += ' S' * bool(op.flags & re.S)
            flag_text += ' X' * bool(op.flags & re.X)
            flag_text = flag_text or '(None)'
            tooltip = ('Select text at the cursor location: '
                    'pattern = %s, flags = %s' % (repr(op.pattern), flag_text))
            callback = lambda action: self._select_op(
                        self._plugin.conf.get_op(op_name=action.get_name()))
            action = (name, stock_id, label, accelerator, tooltip, callback)
            actions.append(action)
            op_menuitems += '\n' + ' ' * 22 + '<menuitem action="%s"/>' % name
        
        self._action_group = gtk.ActionGroup("ClickConfigPluginActions")
        self._action_group.add_actions(actions)
        manager = self._window.get_ui_manager()
        manager.insert_action_group(self._action_group, -1)
        
        ui_str = """
            <ui>
              <menubar name="MenuBar">
                <menu name="EditMenu" action="Edit">
                  <placeholder name="EditOps_6">
                    <menu action="ClickConfig">
                      <menuitem action="Configure"/>
                      <separator/>%s
                    </menu>
                  </placeholder>
                </menu>
              </menubar>
            </ui>
            """ % op_menuitems
        self._ui_id = manager.add_ui_from_string(ui_str)
    
        LOGGER.log('Menu added for %s' % self._window)
    
    def _remove_menu(self):
        """Remove the Click Config submenu."""
        LOGGER.log()
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        self._action_group = None
        manager.ensure_update()
        LOGGER.log('Menu removed for %s' % self._window)
    
    def update_menu(self):
        """Update the menu (in case the SelectionOp list has changed)."""
        LOGGER.log()
        self._remove_menu()
        self._insert_menu()
    
    def activate(self):
        """End this instance of Click Config"""
        LOGGER.log()
        LOGGER.log('Click Config activating for %s' % self._window)
        self._insert_menu()
        self.update_ui()
    
    def deactivate(self):
        """End this instance of Click Config"""
        LOGGER.log()
        self._disconnect_mouse_handlers()
        self._disconnect_scrollwin_handlers()
        self._disconnect_viewport_handlers()
        self._remove_menu()
        self._time_of_last_click = None
        self._double_click_time = None
        self._plugin = None
        LOGGER.log('Click Config deactivated for %s' % self._window)
        self._window = None
    
    def open_config_window(self):
        """Open the Click Config plugin configuration window."""
        LOGGER.log()
        self._plugin.create_configure_dialog()
        self._plugin.config_ui.window.show()
    
    def get_doc_language(self):
        """Return the programming language of the current document."""
        LOGGER.log()
        doc = self._window.get_active_document()
        doc_language = doc.get_language()
        if doc_language:
            doc_language_name = doc_language.get_name()
        else:
            doc_language_name = '-None-'
        return doc_language_name
    
    def update_ui(self):
        """
        Identify the document and connect the menu and mouse handling.
        
        A mouse handler connection must be made for each view.
        
        The Split View 2 plugin creates two views in each tab, and
        GeditWindow.get_active_view() only gets the first one.  So it's
        necessary to get the active tab and then drill down to get its
        view(s), so that a mouse handler can be attached to each.
        """
        LOGGER.log()
        doc = self._window.get_active_document()
        tab = self._window.get_active_tab()
        current_view = self._window.get_active_view()
        if doc and current_view and current_view.get_editable():
            if self._plugin.conf.is_set_by_language:
                language = self.get_doc_language()
                LOGGER.log('Language detected: %s' % language)
                if language in self._plugin.conf.languages:
                    configset_name = self._plugin.conf.languages[language]
                    self._plugin.conf.current_configset_name = configset_name
                    LOGGER.log('ConfigSet selected: %s' %
                                             configset_name)
            self._action_group.set_sensitive(True)
            scrollwin = tab.get_children()[0]
            if scrollwin not in self._handlers_per_scrollwin:
                """Prepare to catch new Split View views."""
                self._handlers_per_scrollwin[scrollwin] = \
                    scrollwin.connect('add',
                                      self.on_scrollwin_add, self._window)
            child = scrollwin.get_child()
            if type(child).__name__ == 'View':
                """Connect to the view within the normal GUI structure."""
                view = child
                self._connect_view(view)
            elif type(child).__name__ == 'Viewport':
                """Connect to views within Split View's GUI structure."""
                viewport = child
                vbox = viewport.get_child()
                if vbox:
                    vpaned = vbox.get_children()[1]
                    scrolled_window_1 = vpaned.get_child1()
                    scrolled_window_2 = vpaned.get_child2()
                    view_1 = scrolled_window_1.get_child()
                    view_2 = scrolled_window_2.get_child()
                    LOGGER.log('Split View 1: %s' % repr(view_1))
                    LOGGER.log('Split View 2: %s' % repr(view_2))
                    self._connect_view(view_1)
                    self._connect_view(view_2)
    
    def on_scrollwin_add(self, scrollwin, widget, window):
        """Call update_ui to add any new view added by Split View"""
        LOGGER.log()
        #scrollwin.disconnect(self._handlers_per_scrollwin[scrollwin])
        #self._handlers_per_scrollwin[scrollwin] = None
        if type(widget).__name__ == 'Viewport':
            viewport = widget
            vbox = viewport.get_child()
            if vbox:
                # Have update_ui hook up the views in the Vbox.
                self.update_ui()
            else:
                # Tell on_viewport_add when the Vbox has been added.
                self._handlers_per_viewport[viewport] = \
                    viewport.connect('add', self.on_viewport_add, window)
        # If it's not a Viewport, then it's probably just the normal View.
        return False
    
    def on_viewport_add(self, viewport, widget, window):
        """Call update_ui to add any new view added by Split View"""
        LOGGER.log()
        viewport.disconnect(self._handlers_per_viewport.pop(viewport))
        # The Vbox is there, so have update_ui hook up the views in it.
        # (This is presuming the Hpaned or Vpaned and Views within it
        # are reliably already in the Vbox.  Otherwise, another event
        # handler step or two might be needed.  But, so far, they seem
        # to always be ready.)
        self.update_ui()
        return False
    
    def _connect_view(self, view):
        """Connect the mouse handler to the view."""
        LOGGER.log()
        LOGGER.log(var='view')
        if view not in self._mouse_handler_ids_per_view:
            self._connect_mouse_handler(view)
            LOGGER.log('Connected to: %s' % repr(view))
    
    def _connect_mouse_handler(self, view):
        """Connect the handler for the view's button_press_event."""
        LOGGER.log()
        self._mouse_handler_ids_per_view[view] = \
            view.connect("button_press_event", self._handle_button_press)
    
    def _connect_drag_handler(self, view):
        """
        Connect handlers for the view's motion_notify_event
                                    and button_release_event.
        The motion events will be used to trigger multiple-click
        drag-selecting and the release event will be used to end it.
        """
        LOGGER.log()
        self._drag_handler_ids = (
            view.connect("motion_notify_event", self._drag_select),
            view.connect_after("button_release_event",
                               self._disconnect_drag_handler)
            )
    
    def _drag_select(self, widget, event):
        """
        Extend the text selection to include a selection at the current pointer
        position.
        """
        LOGGER.log()
        view = widget
        
        # Scroll if dragging beyond top or bottom of the view.
        (visible_left_x, visible_top_y,
            view_width, view_height) = view.get_visible_rect()
        visible_bottom_y = visible_top_y + view_height
        if event.y < 0:
            top_line_iter, top_line_y = \
                view.get_line_at_y(visible_top_y)
            if (view.backward_display_line(top_line_iter) or
                    top_line_y < visible_top_y):
                view.scroll_to_iter(top_line_iter, within_margin=0.0)
        if event.y > view_height:
            bottom_line_iter, bottom_line_y = \
                view.get_line_at_y(visible_bottom_y)
            bottom_line_height = view.get_line_yrange(bottom_line_iter)[1]
            if (view.forward_display_line(bottom_line_iter) or
                    bottom_line_y > visible_bottom_y - bottom_line_height):
                view.scroll_to_iter(bottom_line_iter, within_margin=0.0)
        
        drag_iter = self._get_click_iter(view, event)
        
        # self._word_re will be used
        self._select_regex(drag_iter, word_re=None, extend=True)
    
    def _disconnect_drag_handler(self, widget, event=None):
        """Disconnect the event handlers for drag selecting."""
        LOGGER.log()
        view = widget
        for handler_id in self._drag_handler_ids:
            view.disconnect(handler_id)
        # Clear the match data of the click.
        self._word_re = None
        self._boundaries = None
        self._click_start_iter = None
        self._click_end_iter = None
    
    def _disconnect_scrollwin_handlers(self):
        """Disconnect any remaining ScrolledWindow event handlers."""
        LOGGER.log()
        for scrollwin in self._handlers_per_scrollwin.keys():
            handler_id = self._handlers_per_scrollwin.pop(scrollwin)
            if scrollwin.handler_is_connected(handler_id):
                scrollwin.disconnect(handler_id)
    
    def _disconnect_viewport_handlers(self):
        """Disconnect any remaining Viewport event handlers."""
        LOGGER.log()
        for viewport in self._handlers_per_viewport.keys():
            handler_id = self._handlers_per_viewport.pop(viewport)
            if viewport.handler_is_connected(handler_id):
                viewport.disconnect(handler_id)
    
    def _disconnect_mouse_handlers(self):
        """Disconnect from mouse signals from all views in the window."""
        LOGGER.log()
        for view in self._mouse_handler_ids_per_view.keys():
            handler_id = self._mouse_handler_ids_per_view.pop(view)
            if view.handler_is_connected(handler_id):
                view.disconnect(handler_id)
    
    def _handle_button_press(self, view, event):
        """
        Evaluate mouse click and call for text selection as appropriate.
        Return False if the click should still be handled afterwards.
        """
        LOGGER.log()
        handled = False
        if event.button == 1:
            now = time.time()
            handlers_by_type = {
                gtk.gdk.BUTTON_PRESS: self._handle_1button_press,
                gtk.gdk._2BUTTON_PRESS: self._handle_2button_press,
                gtk.gdk._3BUTTON_PRESS: self._handle_3button_press,
                }
            handled, click = handlers_by_type[event.type](now)
            if click:
                click_iter = self._get_click_iter(view, event)
                handled = self._make_assigned_selection(click, click_iter)
                if handled:
                    self._connect_drag_handler(view)
        return handled
    
    def _handle_1button_press(self, now):
        """Detect 5-click, 4-click, or 1-click. Otherwise eat the signal."""
        LOGGER.log()
        handled = False
        click = None
        if now - self._time_of_last_click[4] < self._double_click_time:
            LOGGER.log('Quintuple-click.')
            # QUINTUPLE-CLICKS are handled here.
            self._time_of_last_click[5] = now
            click = 5
        elif now - self._time_of_last_click[3] < self._double_click_time:
            LOGGER.log('Quadruple-click.')
            # QUADRUPLE-CLICKS are handled here.
            self._time_of_last_click[4] = now
            click = 4
        elif now - self._time_of_last_click[2] < self._double_click_time:
            LOGGER.log('(3rd click of a triple-click.)', level='debug')
            # Ignore and consume it.  Triple-clicks are not handled here.
            handled = True
        elif now - self._time_of_last_click[1] < self._double_click_time:
            LOGGER.log('(2nd click of a double-click.)', level='debug')
            # Ignore and consume it.  Double-clicks are not handled here.
            handled = True
        else:
            LOGGER.log('Single-click.')
            # SINGLE-CLICKS are handled here.
            self._time_of_last_click[1] = now
            click = 1
        return handled, click
    
    def _handle_2button_press(self, now):
        """Detect 2-click. Otherwise eat the signal."""
        LOGGER.log()
        handled = False
        click = None
        if (now - self._time_of_last_click[4]) < self._double_click_time:
            LOGGER.log('(4th & 5th of a quintuple-click.)', level='debug')
            # Ignore and consume it.  Quintuple-clicks are not handled here.
            handled = True
        else:
            LOGGER.log('Double-click.')
            # DOUBLE-CLICKS are handled here.
            self._time_of_last_click[2] = now
            click = 2
        return handled, click
    
    def _handle_3button_press(self, now):
        """Detect 3-click. Otherwise eat the signal."""
        LOGGER.log()
        handled = False
        click = None
        if (now - self._time_of_last_click[5]) < self._double_click_time:
            LOGGER.log('(4th-6th of a sextuple-click.)', level='debug')
            # Ignore and consume it.  Sextuple-clicks are not handled here.
            handled = True
        else:
            LOGGER.log('Triple-click.')
            # TRIPLE-CLICKS are handled here.
            self._time_of_last_click[3] = now
            click = 3
        return handled, click
    
    def _get_click_iter(self, view, event):
        """Return the current cursor location based on the click location."""
        LOGGER.log()
        buffer_x, buffer_y = view.window_to_buffer_coords(
                        view.get_window_type(event.window),
                        int(event.x),
                        int(event.y))
        event_iter = view.get_iter_at_location(buffer_x, buffer_y)
        return event_iter
    
    def _get_insert_iter(self):
        """Return the current cursor location based on the insert mark."""
        LOGGER.log()
        doc = self._window.get_active_document()
        insert_mark = doc.get_insert()
        insert_iter = doc.get_iter_at_mark(insert_mark)
        return insert_iter
    
    def _make_assigned_selection(self, click, click_iter):
        """Select text based on the click type and location."""
        LOGGER.log()
        acted = False
        op = self._plugin.conf.get_op(click=click)
        if op.name != 'None':
            acted = self._select_op(op, click_iter=click_iter)
        return acted
    
    # Text selection functions:
    
    def _select_op(self, op, click_iter=None):
        """Finds first regex match that includes the click position."""
        LOGGER.log()
        
        char_spec = op.pattern
        flags = op.flags
        
        LOGGER.log('Selection name: %s' % op.name)
        
        if not click_iter:
            click_iter = self._get_insert_iter()
        
        word_re = re.compile(char_spec, flags)
        
        did_select = self._select_regex(click_iter, word_re)
        return did_select
    
    def _select_regex(self, click_iter, word_re, extend=False):
        """
        Select text in the document matching word_re and containing click_iter.
        """
        LOGGER.log()
        if word_re is None:
            word_re = self._word_re
        else:
            self._word_re = word_re
        doc = self._window.get_active_document()
        multiline = bool(word_re.flags & re.M)
        if multiline:
            source_start_iter, source_end_iter = doc.get_bounds()
            pick_pos = click_iter.get_offset()
        else:
            source_start_iter, source_end_iter = \
                self._get_line_iter_pair(click_iter)
            pick_pos = click_iter.get_line_offset()
        source_text = source_start_iter.get_slice(source_end_iter)
        # There is nothing to select in an empty text.
        if source_text == "":
            return False
        match_start, match_end = self._find_text(source_text, pick_pos, word_re)
        target_start_iter = click_iter.copy()
        target_end_iter = click_iter.copy()
        if multiline:
            target_start_iter.set_offset(match_start)
            target_end_iter.set_offset(match_end)
        else:
            target_start_iter.set_line_offset(match_start)
            target_end_iter.set_line_offset(match_end)
        if extend:
            target_start_iter = min((self._click_start_iter,
                                    target_start_iter),
                                    key=lambda i: i.get_offset())
            #extended_back = target_start_iter != self._click_start_iter
            target_end_iter = max((self._click_end_iter,
                                  target_end_iter),
                                  key=lambda i: i.get_offset())
            #extended_forward = target_end_iter != self._click_end_iter
        else:
            self._click_start_iter = target_start_iter
            self._click_end_iter = target_end_iter
        doc.select_range(target_start_iter, target_end_iter)
        # These two lines will activate search highlighting on the text:
#        found_text = doc.get_text(target_start_iter, target_end_iter)
#        doc.set_search_text(found_text, 1)
        return True
    
    def _find_text(self, source_text, pick_pos, word_re):
        """
        Finds the range of the match, or the range between matches, for regex
        word_re within source_text that includes the position pick_pos.
        If there is no match, then the whole document is selected as being
        between matches.
        """
        LOGGER.log()
        
        # self._boundaries is set by a click selection,
        # remains available for a click-drag selection,
        # and then is set to None by self._disconnect_drag_handler().
        if not self._boundaries:
            self._find_boundaries(source_text, word_re)
        
        after = next((p for p in self._boundaries if p > pick_pos),
                     len(source_text))
        after_index = self._boundaries.index(after)
        before = self._boundaries[after_index - 1]
        
        # For single-line regexes, the boundaries
        # need to be determined each time.
        if not word_re.flags & re.M:
            self._boundaries = None
        
        return before, after
    
    def _find_boundaries(self, source_text, word_re):
        """Find the offsets of all match starting and ending positions."""
        LOGGER.log()
        
        spans = ((m.start(), m.end()) for m in word_re.finditer(source_text))
        boundaries = list(itertools.chain.from_iterable(spans))
        
        source_start = 0
        source_end = len(source_text)
        
        if boundaries:
            if boundaries[0] != source_start:
                boundaries.insert(0, source_start)
            if boundaries[-1] != source_end:
                boundaries.append(source_end)
        else:
            boundaries = [source_start, source_end]
        
        self._boundaries = boundaries
    
    def _get_line_iter_pair(self, a_text_iter):
        """Return iters for the start and end of this iter's line."""
        LOGGER.log()
        left_iter = a_text_iter.copy()
        right_iter = a_text_iter.copy()
        left_iter.set_line_offset(0)
        if not right_iter.ends_line():
            right_iter.forward_to_line_end()
        return left_iter, right_iter


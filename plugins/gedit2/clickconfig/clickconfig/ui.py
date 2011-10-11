# -*- coding: utf8 -*-
#  Click_Config plugin for Gedit
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
This module provides a GUI window for configuring the Click_Config plugin for
Gedit.

The ConfigUI object is constructed with a reference to the ClickConfigPlugin
object through which it accesses the plugin's configuration and logging.

Classes:
ConfigUI -- The Click_Config plugin creates one object of this class when the
            configuration window is opened.  The object removes its own
            reference from the plugin when the configuration window is closed.

In addition to the imported modules, this module requires:
Click_Config.xml -- configuration GUI layout converted from Click_Config.glade

2010-05-26  for Click Config version 1.1.2
    Fixed Issue #4 in ConfigUI._update_config_display.

"""

import os
import re
import sys

import gtk

from treeviewdv import TreeViewDV
from .logger import Logger
LOGGER = Logger(level=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')[2])

class ConfigUI(object):
    
    """
    The configuration window for Click_Config.
    
    Usage:
    config_ui = ConfigUI()
    config_ui.window.show()
    
    See:
    click_config.py ClickConfigPlugin.create_configure_dialog()
    
    """
    
    def __init__(self, plugin):
        """
        1. Create the window.
        2. Make a temporary copy of the configuration.
        3. Update the window's widgets to reflect the configuration.
        4. Connect the event handlers.
        """
        self._plugin = plugin
        LOGGER.log()
        
        # 1. Create the window.
        glade_file = os.path.join(self._plugin.plugin_path, 'Click_Config.xml')
        self.builder = gtk.Builder()
        self.builder.add_from_file(glade_file)
        self.window = self.builder.get_object("config_window")
        gedit_window = self._plugin.get_gedit_window()
        self.window.set_transient_for(gedit_window)
        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        
        # 2. Make a temporary copy of the configuration.
        self._mod_conf = self._plugin.conf.copy()
        self.preserved_sets = [item.name for item in
            self._mod_conf.configsets if item.preserved]
        self.preserved_ops = [item.name for item in
            self._mod_conf.ops if item.preserved]
        
        # 3. Update the window's widgets to reflect the configuration.
        width = self._mod_conf.window_width
        height = (self._mod_conf.window_height_tall if
                       self._mod_conf.is_set_by_language else
                       self._mod_conf.window_height_short)
        if width and height:
            self.window.set_default_size(width, height)
        self._update_config_combobox()
        self._update_config_display()
        self._update_lang_checkbutton()
        self._update_define_combobox()
        self._update_define_display()
        self._update_language_frame()
        self._update_apply_button()
    
        # 4. Connect the event handlers.
        signals_to_actions = {
            'on_config_window_destroy':
                self.on_config_window_destroy,
            'on_config_combobox_entry_changed':
                self.on_config_combobox_entry_changed,
            'on_comboboxentryentry1_key_press_event':
                self.on_comboboxentryentry1_key_press_event,
            'on_config_add_button_clicked':
                self.on_config_add_button_clicked,
            'on_config_remove_button_clicked':
                self.on_config_remove_button_clicked,
            'on_lang_checkbutton_toggled':
                self.on_lang_checkbutton_toggled,
            'on_combobox_changed':
                self.on_combobox_changed,
            'on_define_comboboxentry_changed':
                self.on_define_comboboxentry_changed,
            'on_define_name_entry_key_press_event':
                self.on_define_entry_key_press_event,
            'on_define_regex_entry_changed':
                self.on_define_changed,
            'on_define_regex_entry_key_press_event':
                self.on_define_entry_key_press_event,
            'on_define_i_checkbutton_toggled':
                self.on_define_changed,
            'on_define_m_checkbutton_toggled':
                self.on_define_changed,
            'on_define_s_checkbutton_toggled':
                self.on_define_changed,
            'on_define_x_checkbutton_toggled':
                self.on_define_changed,
            'on_define_add_button_clicked':
                self.on_define_add_button_clicked,
            'on_define_remove_button_clicked':
                self.on_define_remove_button_clicked,
            'on_OK_button_clicked':
                self.on_OK_button_clicked,
            'on_Apply_button_clicked':
                self.on_Apply_button_clicked,
            'on_Cancel_button_clicked':
                self.on_Cancel_button_clicked,
            'on_Browse_button_clicked':
                self.on_Browse_button_clicked,
            'on_Import_button_clicked':
                self.on_Import_button_clicked,
            }
        self.builder.connect_signals(signals_to_actions)
        self.on_config_window_configure_handler_id = self.window.connect(
            'configure-event',
            self.on_config_window_configure_event)
        
        LOGGER.log('Configuration window opened.')
        
        
    ### 1 - General configure window
    
    # 1.1 - Event handlers
    
    def on_config_window_configure_event(self, widget, event):
        """
        Set configuration window height and sizing constraint.
        This event handler is connected by on_lang_checkbutton_toggled.
        """
        LOGGER.log()
        window = widget
        window.disconnect(self.on_config_window_configure_handler_id)
        width, height = window.get_size()
        if self._mod_conf.is_set_by_language:
            window.set_geometry_hints(height_inc=-1)
            height = self._mod_conf.window_height_tall or height
        else:
            height = self._mod_conf.window_height_short or height
            unlikely_height_inc = height * 100
            window.set_geometry_hints(height_inc=unlikely_height_inc)
        self.window.resize(width, height)
    
    def on_config_window_destroy(self, event):
        """Let the ClickConfigPlugin know that the ConfigUI is gone."""
        LOGGER.log()
        LOGGER.log('Configuration window closed.')
        self._plugin.config_ui = None
        return False
    
    def on_OK_button_clicked(self, button):
        """
        Give the ClickConfigPlugin the modified configuration, then close.
        """
        LOGGER.log()
        width, height = self.window.get_size()
        self._mod_conf.window_width = width
        if self._mod_conf.is_set_by_language:
            self._mod_conf.window_height_tall = height
        else:
            self._mod_conf.window_height_short = height
        self._plugin.update_configuration(self._mod_conf.copy())
        self._plugin.update_ui(self._plugin.get_gedit_window())
        self.window.destroy()
    
    def on_Apply_button_clicked(self, button):
        """Give the ClickConfigPlugin the modified configuration."""
        LOGGER.log()
        self._plugin.update_configuration(self._mod_conf.copy())
        self._update_apply_button()
    
    def on_Cancel_button_clicked(self, button):
        """Close without giving ClickConfigPlugin the modified configuration."""
        LOGGER.log()
        self.window.destroy()
    
    def on_Browse_button_clicked(self, button):
        """Browse to the configuration file."""
        LOGGER.log()
        self._plugin.open_config_dir()
    
    def on_Import_button_clicked(self, button):
        """Import ConfigSets and SelectionOps from another configuration file."""
        LOGGER.log()
        filename = self._filechooser_dialog(
            title='Import from a Click_Config configuration file')
        if filename:
            self._mod_conf.import_file(filename)
        self._update_config_combobox()
        self._update_config_display()
        self._update_define_combobox()
        self._update_define_display()
        self._update_language_frame()
        self._update_apply_button()
    
    # 1.2 - Support functions
    
    def _update_apply_button(self):
        """Correct the Apply button's sensitivity."""
        LOGGER.log()
        apply_button = self.builder.get_object('Apply_button')
        has_changes = self._mod_conf != self._plugin.conf
        LOGGER.log(var='has_changes')
        apply_button.set_sensitive(has_changes)
    
    def _filechooser_dialog(self, title='Open'):
        """
        Provide file selection dialog to user and return the selected filename.
        """
        LOGGER.log()
        dialog = gtk.FileChooserDialog(
            title=title,
            parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        file_filter = gtk.FileFilter()
        file_filter.set_name("All files")
        file_filter.add_pattern("*")
        dialog.add_filter(file_filter)
        text_file_filter = gtk.FileFilter()
        text_file_filter.set_name("Text files")
        text_file_filter.add_mime_type("text/plain")
        dialog.add_filter(text_file_filter)
        dialog.set_filter(text_file_filter)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
        else:
            filename = ''
        dialog.destroy()
        return filename
    
    ### 2 - ConfigSet name section
    
    # 2.1 - Event handlers
    
    def on_config_combobox_entry_changed(self, combobox):
        """Update the configuration and interface based on the selection."""
        LOGGER.log()
        # Get objects
        config_combobox_entry = combobox
        config_add_button = self.builder.get_object("config_add_button")
        config_remove_button = self.builder.get_object("config_remove_button")
        # Get circumstance
        config_name = config_combobox_entry.get_active_text().strip()
        is_addable = self._is_config_name_addable(config_name)
        is_removable = self._is_config_name_removable(config_name)
        is_existing = config_name in self._mod_conf.get_configset_names()
        # Update configuration
        if is_existing:
            self._mod_conf.current_configset_name = config_name
        # Update interface
            self._update_config_display()
        config_add_button.set_sensitive(is_addable)
        config_remove_button.set_sensitive(is_removable)
    
    def on_comboboxentryentry1_key_press_event(self, widget, event):
        """React to the Enter key here the same as for the Add button."""
        LOGGER.log()
        keyval = event.keyval
        keyval_name = gtk.gdk.keyval_name(keyval)
        if keyval_name in ('Return', 'KP_Enter'):
            self._add_config()
    
    def on_config_add_button_clicked(self, button):
        """Call function to add the configuration."""
        LOGGER.log()
        self._add_config()

    def on_config_remove_button_clicked(self, button):
        """Call function to remove the configuration."""
        LOGGER.log()
        self._remove_config()
    
    def on_lang_checkbutton_toggled(self, togglebutton):
        """Update is_set_by_language setting and interface."""
        LOGGER.log()
        # Get objects
        lang_checkbutton = togglebutton
        # Get circumstance
        is_checked = lang_checkbutton.get_active()
        # Update configuration
        self._mod_conf.is_set_by_language = is_checked
        width, height = self.window.get_size()
        if is_checked:
            self._mod_conf.window_height_short = height
        else:
            self._mod_conf.window_height_tall = height
        # Update interface
        self._update_language_frame()
        self.on_config_window_configure_handler_id = self.window.connect(
            'configure-event',
            self.on_config_window_configure_event)
    
    # 2.2 - Support functions
    
    def _update_lang_checkbutton(self):
        """Make the 'Configure by language' checkbox match its setting."""
        LOGGER.log()
        # Get objects
        lang_checkbutton = self.builder.get_object("lang_checkbutton")
        # Update interface
        lang_checkbutton.set_active(self._mod_conf.is_set_by_language)
    
    def _update_config_combobox(self):
        """Reflect the ConfigSets and current ConfigSet in the interface."""
        LOGGER.log()
        configset_names = self._mod_conf.get_configset_names()
        combobox_list = configset_names[0:2] + [' - '] + configset_names[2:]
        config_combobox_entry = \
            self.builder.get_object('config_combobox_entry')
        config_combobox_entry.set_row_separator_func(self._row_separator_func)
        self._fill_comboboxentry(config_combobox_entry, combobox_list)
        index = combobox_list.index(self._mod_conf.current_configset_name)
        config_combobox_entry.set_active(index)
        config_add_button = self.builder.get_object('config_add_button')
        config_add_button.set_sensitive(False)
    
    def _fill_comboboxentry(self, comboboxentry, items):
        """Put a list of the ConfigSet names in the combobox."""
        LOGGER.log()
        comboboxentry_liststore = gtk.ListStore(str, str)
        for item in items:
            comboboxentry_liststore.append(['', item])
        comboboxentry.set_model(comboboxentry_liststore)
        comboboxentry.set_text_column(1)
        #GtkWarning: gtk_combo_box_entry_set_text_column: assertion
        # `entry_box->priv->text_column == -1' failed
    
    def _row_separator_func(self, model, iter_):
        """Identify what item represents a separator."""
        LOGGER.log()
        row_is_a_separator = model.get_value(iter_, 1) == ' - '
        return row_is_a_separator

    def _get_configset_names(self):
        """Return a list of the ConfigSet names."""
        LOGGER.log()
        configset_names = [item.name for item in self._mod_conf.configsets]
        configset_names = configset_names[0:2] + sorted(configset_names[2:])
        return configset_names
    
    def _add_config(self):
        """Add the configuration."""
        LOGGER.log()
        # Get objects
        config_combobox_entry = \
            self.builder.get_object("config_combobox_entry")
        # Get circumstance
        config_name = config_combobox_entry.get_active_text().strip()
        is_addable = self._is_config_name_addable(config_name)
        # Update configuration
        if is_addable:
            new_configset = self._mod_conf.get_configset().copy_as(config_name)
            self._mod_conf.add_configset(new_configset)
            self._mod_conf.current_configset_name = config_name
        # Update interface
            self._update_config_combobox()
            self._update_config_display()
            self._update_language_frame()
            LOGGER.log('ConfigSet added: %s.' % config_name)
    
    def _remove_config(self):
        """Remove the configuration."""
        LOGGER.log()
        # Get objects
        config_combobox_entry = \
            self.builder.get_object("config_combobox_entry")
        # Get circumstance
        config_name = config_combobox_entry.get_active_text().strip()
        config_names = self._mod_conf.get_configset_names()
        is_removable = self._is_config_name_removable(config_name)
        # Update configuration
        if is_removable:
            # Switch to preceding config set
            config_name_index = config_names.index(config_name)
            preceding_config_name = config_names[config_name_index - 1]
            self._mod_conf.current_configset_name = preceding_config_name
            # Remove the config set
            old_configset = self._mod_conf.get_configset(config_name)
            self._mod_conf.remove_configset(old_configset)
            self._mod_conf.check_language_configsets()
        # Update interface
            self._update_config_combobox()
            self._update_config_display()
            self._update_language_frame()
            LOGGER.log('ConfigSet removed: %s.' % config_name)
    
    def _is_config_name_addable(self, config_name):
        """Check if ConfigSet of this name can be added."""
        LOGGER.log()
        return config_name not in self._mod_conf.get_configset_names()
    
    def _is_config_name_removable(self, config_name):
        """Check if ConfigSet of this name can be removed."""
        LOGGER.log()
        return (config_name in self._mod_conf.get_configset_names() and
                     config_name not in self.preserved_sets)
    
    ### 3 - ConfigSet settings section
    
    # 3.1 - Event handlers
    
    def on_combobox_changed(self, combobox):
        """
        Update the configuration and interface to reflect the SelectionOp name.
        """
        LOGGER.log()
        # Get objects
        config_combobox_entry = \
            self.builder.get_object("config_combobox_entry")
        # Get circumstance
        op_name = combobox.get_active_text()
        click_number = combobox.get_name()[8:]
        click = int(click_number)
        entry_config_name = config_combobox_entry.get_active_text().strip()
        # Update configuration
        self._mod_conf.set_op(op_name=op_name, click=click)
        # Update interface
        self._set_combobox_op(combobox, op_name)
        self._update_apply_button()
        # Make sure a typed-but-not-added config name isn't showing
        if entry_config_name != self._mod_conf.current_configset_name:
            self._update_config_combobox()
    
    # 3.2 - Support functions
    
    def _fill_combobox(self, combobox, items):
        """Put a list of the SelectionOp names in the combobox."""
        LOGGER.log()
        combobox_liststore = gtk.ListStore(str)
        for item in items:
            combobox_liststore.append([item])
        combobox.set_model(combobox_liststore)
    
    def _update_config_display(self):
        """
        Reflect the five SelectionOps of the current ConfigSet in the widgets.
        """
        LOGGER.log()
        op_names = self._mod_conf.get_op_names()
        for click in range(1, 6):
            combobox = self.builder.get_object('combobox%d' % click)
            # As of GTK+ 2.20, the widget name does not automatically equal the
            # widget id, so I have to set it here to let it work as before.
            combobox.set_name('combobox%d' % click)
            self._fill_combobox(combobox, op_names)
            op_name = self._mod_conf.get_op(click=click).name
            self._set_combobox_op(combobox, op_name)
        self._update_apply_button()

    def _set_combobox_op(self, combobox, op_name):
        """Reflect the SelectionOp in the widgets for the click."""
        LOGGER.log()
        # Get objects
        objects = {}
        objects['combobox'] = combobox
        combobox_name = objects['combobox'].get_name()
        click_number = combobox_name[8:]
        entry_name = "entry" + click_number
        objects['entry'] = self.builder.get_object(entry_name)
        objects['i'] = self.builder.get_object('i_checkbutton' + click_number)
        objects['m'] = self.builder.get_object('m_checkbutton' + click_number)
        objects['s'] = self.builder.get_object('s_checkbutton' + click_number)
        objects['x'] = self.builder.get_object('x_checkbutton' + click_number)
        # Get circumstance
        op_names = self._mod_conf.get_op_names()
        is_editable = not self._mod_conf.get_configset().preserved
        op = self._mod_conf.get_op(op_name=op_name)
        pattern = op.pattern
        flags = op.flags
        index = op_names.index(op_name)
        # Update interface
        objects['combobox'].set_active(index)
        objects['combobox'].set_sensitive(is_editable)
        objects['entry'].set_text(pattern)
        objects['entry'].set_sensitive(False)
        objects['i'].set_active(flags & re.I)
        objects['m'].set_active(flags & re.M)
        objects['s'].set_active(flags & re.S)
        objects['x'].set_active(flags & re.X)
        objects['i'].set_sensitive(False)
        objects['m'].set_sensitive(False)
        objects['s'].set_sensitive(False)
        objects['x'].set_sensitive(False)
        
    ### 4 - Define section
    
    # 4.1 - Event handlers
    
    def on_define_comboboxentry_changed(self, combobox):
        """Update the configuration and interface for the SelectionOp name."""
        LOGGER.log()
        op_name = combobox.get_active_text().strip()
        op_names = self._mod_conf.get_op_names()
        if op_name in op_names:
            self._mod_conf.current_op_name = op_name
            self._update_apply_button()
        self._update_define_display()
    
    def on_define_changed(self, editable):
        """Call function to update the Add button."""
        LOGGER.log()
        self._update_define_add_button()
    
    def on_define_entry_key_press_event(self, widget, event):
        """React to the Enter key here the same as for the Add button."""
        LOGGER.log()
        keyval = event.keyval
        keyval_name = gtk.gdk.keyval_name(keyval)
        if keyval_name in ('Return', 'KP_Enter'):
            self._add_define()
    
    def on_define_add_button_clicked(self, button):
        """Call function to update the SelectionOp for the changed pattern."""
        LOGGER.log()
        self._add_define()
    
    def on_define_remove_button_clicked(self, button):
        """Call function to remove the current SelectionOp."""
        LOGGER.log()
        self._remove_define()
    
    # 4.2 - Support functions
    
    def _update_define_combobox(self):
        """Reflect the SelectionOps and current SelectionOp in the combobox."""
        LOGGER.log()
        define_comboboxentry = self.builder.get_object('define_comboboxentry')
        op_names = self._mod_conf.get_op_names()
        self._fill_comboboxentry(define_comboboxentry, op_names)
        op_name = self._mod_conf.current_op_name
        index = op_names.index(op_name)
        define_comboboxentry.set_active(index)
    
    def _update_define_display(self):
        """Reflect the current SelectionOp in the interface."""
        LOGGER.log()
        # Get objects
        objects = {}
        objects['combobox'] = self.builder.get_object('define_comboboxentry')
        objects['pattern'] = self.builder.get_object('define_regex_entry')
        objects['i'] = self.builder.get_object('define_i_checkbutton')
        objects['m'] = self.builder.get_object('define_m_checkbutton')
        objects['s'] = self.builder.get_object('define_s_checkbutton')
        objects['x'] = self.builder.get_object('define_x_checkbutton')
        objects['add'] = self.builder.get_object("define_add_button")
        objects['remove'] = self.builder.get_object("define_remove_button")
        # Get circumstance
        op_name = objects['combobox'].get_active_text().strip()
        op_names = self._mod_conf.get_op_names()
        is_existing_name = op_name in op_names
        is_preserved_op = op_name in self.preserved_ops
        is_editable = not is_preserved_op
        is_addable = not is_existing_name
        is_removable = is_existing_name and not is_preserved_op
        # Update interface
        if is_existing_name:
            op = self._mod_conf.get_op(op_name=op_name)
            objects['pattern'].set_text(op.pattern)
            objects['i'].set_active(op.flags & re.I)
            objects['m'].set_active(op.flags & re.M)
            objects['s'].set_active(op.flags & re.S)
            objects['x'].set_active(op.flags & re.X)
        objects['pattern'].set_sensitive(is_editable)
        objects['i'].set_sensitive(is_editable)
        objects['m'].set_sensitive(is_editable)
        objects['s'].set_sensitive(is_editable)
        objects['x'].set_sensitive(is_editable)
        objects['add'].set_sensitive(is_addable)
        objects['remove'].set_sensitive(is_removable)
    
    def _update_define_add_button(self):
        """Correct the Add button's sensitivity for the pattern and flags."""
        LOGGER.log()
        # Get objects
        objects = {}
        objects['combobox'] = self.builder.get_object('define_comboboxentry')
        objects['pattern'] = self.builder.get_object('define_regex_entry')
        objects['i'] = self.builder.get_object('define_i_checkbutton')
        objects['m'] = self.builder.get_object('define_m_checkbutton')
        objects['s'] = self.builder.get_object('define_s_checkbutton')
        objects['x'] = self.builder.get_object('define_x_checkbutton')
        objects['add'] = self.builder.get_object("define_add_button")
        # Get circumstance
        op_name = objects['combobox'].get_active_text().strip()
        pattern = objects['pattern'].get_text()
        flags = (objects['i'].get_active() * re.I +
                 objects['m'].get_active() * re.M +
                 objects['s'].get_active() * re.S +
                 objects['x'].get_active() * re.X)
        current_op = self._mod_conf.get_op()
        op_names = self._mod_conf.get_op_names()
        has_new_op_name = op_name not in op_names
        has_new_pattern = pattern != current_op.pattern
        has_new_flags = flags != current_op.flags
        has_changes = (has_new_op_name or 
                       has_new_pattern or
                       has_new_flags)
        is_preserved_op = op_name in self.preserved_ops
        # Update interface
        objects['add'].set_sensitive(has_changes and not is_preserved_op)
    
    def _add_define(self):
        """Add or update the SelectionOp."""
        LOGGER.log()
        # Get objects
        objects = {}
        objects['combobox'] = self.builder.get_object('define_comboboxentry')
        objects['pattern'] = self.builder.get_object('define_regex_entry')
        objects['i'] = self.builder.get_object('define_i_checkbutton')
        objects['m'] = self.builder.get_object('define_m_checkbutton')
        objects['s'] = self.builder.get_object('define_s_checkbutton')
        objects['x'] = self.builder.get_object('define_x_checkbutton')
        # Get circumstance
        op_name = objects['combobox'].get_active_text().strip()
        is_preserved_op = op_name in self.preserved_ops
        pattern = objects['pattern'].get_text()
        flags = (objects['i'].get_active() * re.I +
                 objects['m'].get_active() * re.M +
                 objects['s'].get_active() * re.S +
                 objects['x'].get_active() * re.X)
        is_valid_re = self._is_valid_re(pattern, flags)
        # Record new definition
        if is_valid_re and not is_preserved_op:
            new_op = self._mod_conf.get_op().copy_as(op_name)
            new_op.pattern = pattern
            new_op.flags = flags
            self._mod_conf.add_op(new_op)
            self._mod_conf.current_op_name = op_name
        # Update interface
            self._update_config_display()
            self._update_define_combobox()
            LOGGER.log('SelectionOp added: %s.' % op_name)
    
    def _is_valid_re(self, pattern, flags):
        """
        Check the validity of the regular expression and
        inform the user if it fails.
        """
        LOGGER.log()
        try:
            is_valid = bool(re.compile(pattern, flags))
        except re.error, re_error:
            is_valid = False
            title = "Click_Config: error in input"
            flag_text =  '\n    I (IGNORECASE)' * bool(flags & re.I)
            flag_text += '\n    M (MULTILINE)'  * bool(flags & re.M)
            flag_text += '\n    S (DOTALL)'     * bool(flags & re.S)
            flag_text += '\n    X (VERBOSE)'    * bool(flags & re.X)
            flag_text = flag_text or '\n    (None)'
            message = ("Invalid regular expression pattern."
                       "\n\nError:\n    %s"
                       "\n\nPattern:\n    %s"
                       "\n\nFlags:%s"
                       % (re_error.message, pattern, flag_text))
            self._show_message(title, message, gtk.MESSAGE_ERROR)
        return is_valid
    
    def _show_message(self, title, message, gtk_message_type):
        """Display a simple dialog box with a message and an OK button."""
        LOGGER.log()
        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                   gtk_message_type,
                                   gtk.BUTTONS_OK, message)
        dialog.set_title(title)
        dialog.set_transient_for(self.window)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        dialog.run()
        dialog.destroy()
    
    def _remove_define(self):
        """Select the preceding SelectionOp and remove the current one."""
        LOGGER.log()
        # Get objects
        combobox = self.builder.get_object("define_comboboxentry")
        # Get circumstance
        op_name = combobox.get_active_text().strip()
        is_preserved_op = op_name in self.preserved_ops
        op_names = self._mod_conf.get_op_names()
        op_index = op_names.index(op_name)
        preceding_op_name = op_names[op_index - 1]
        # Remove definition
        if not is_preserved_op:
            # Remove the select operation from configurations
            for configset in self._mod_conf.configsets:
                for i in range(5):
                    if configset.op_names[i] == op_name:
                        configset.op_names[i] = preceding_op_name
            # Remove it from select operations set
            self._mod_conf.remove_op(op_name)
            self._mod_conf.current_op_name = preceding_op_name
        # Update interface
            self._update_config_display()
            self._update_define_combobox()
            LOGGER.log('SelectionOp removed: %s.' % op_name)
    
    ### 5 - Language section
    
    def on_drag_data_get(self, widget, drag_context,
                          selection_data, info, timestamp):
        """Provide list of languages to drag-and-drop operation."""
        LOGGER.log()
        treeview = widget
        treeselection = treeview.get_selection()
        languages = self._get_list_from_treeselection(treeselection)
        selection_data.set('list of languages', 8, repr(languages))
    
    def _get_list_from_treeselection(self, treeselection):
        """Return a list of the selected values."""
        LOGGER.log()
        list_ = []
        treeselection.selected_foreach(self._append_text_from_model, list_)
        return list_
    
    def _append_text_from_model(self, treemodel, path, iter_, list_):
        """Append first-column value of the specified row to the list."""
        LOGGER.log()
        text = treemodel.get_value(iter_, 0)
        list_.append(text)
    
    def on_drag_data_received(self, widget, drag_context, x, y,
                               selection_data, info, timestamp):
        """
        Assign languages from drag-and-drop operation to ConfigSet name of the
        receiving ScrolledWindow.
        """
        LOGGER.log()
        scrolledwindow = widget
        # Get the languages from the drag data
        text = selection_data.data
        if text:
            languages = eval(text)
            # Determine source and destination
            source_configset_name = self._mod_conf.languages[languages[0]]
            dest_configset_name = scrolledwindow.name[3:]
            if source_configset_name == dest_configset_name:
                return
            source_treeview_name = 'tv_' + source_configset_name
            source_treeview = self._get_widget_by_name(
                scrolledwindow.get_parent(), source_treeview_name)
            dest_treeview = scrolledwindow.get_child()
            # Move and re-assign the languages
            for language in languages:
                self._remove_from_treeview(source_treeview, language)
                self._mod_conf.languages[language] = dest_configset_name
                self._add_to_treeview(dest_treeview, language)
            self._select_languages(dest_treeview, languages)
            dest_treeview.grab_focus()
    
    def _get_widget_by_name(self, container, name):
        """Recursively search to return the named child widget."""
        LOGGER.log()
        children = container.get_children()
        for child in children:
            if child.name == name:
                return child
            if isinstance(child, gtk.Container):
                found_child = self._get_widget_by_name(child, name)
                if found_child:
                    return found_child
    
    def _remove_from_treeview(self, treeview, value):
        """Remove the language name from the TreeView."""
        LOGGER.log()
        liststore = treeview.get_model()
        liststore_list = self._get_list_from_liststore(liststore)
        path = liststore_list.index(value)
        iter_ = liststore.get_iter(path)
        liststore.remove(iter_)
        if len(liststore) == 0:
            treeview.set_property('can-focus', False)
    
    def _add_to_treeview(self, treeview, value):
        """Add the language name to the TreeView."""
        LOGGER.log()
        liststore = treeview.get_model()
        liststore_list = self._get_list_from_liststore(liststore)
        liststore_list.append(value)
        liststore_list.sort()
        path = liststore_list.index(value)
        if path == len(liststore):
            liststore.append([value])
        else:
            iter_ = liststore.get_iter(path)
            liststore.insert_before(iter_, row=[value])
        treeview.set_property('can-focus', True)
    
    def _select_languages(self, treeview, languages):
        """Select rows in the treeview corresponding to languages."""
        LOGGER.log()
        liststore = treeview.get_model()
        liststore_list = self._get_list_from_liststore(liststore)
        treeselection = treeview.get_selection()
        for language in languages:
            path = liststore_list.index(language)
            treeselection.select_path(path)
    
    def _get_list_from_liststore(self, liststore):
        """Return a list of the first-column treeview row values."""
        LOGGER.log()
        return [liststore.get_value(liststore.get_iter(i), 0)
                 for i in range(len(liststore))]
    
    def _update_language_frame(self):
        """Show or hide the language frame as appropriate."""
        LOGGER.log()
        # Get objects
        language_frame = self.builder.get_object("frame3")
        # Update interface
        if self._mod_conf.is_set_by_language:
            self._build_lang_table()
            language_frame.show()
        else:
            language_frame.hide()
            self.window.present()
    
    def _build_lang_table(self):
        """Replace the language table with one matching the configuration."""
        LOGGER.log()
        lang_vbox = self.builder.get_object("lang_vbox")
        # Get the old Table
        old_table = lang_vbox.get_children()[1]
        # Make a new Table for the ConfigSets and their assigned languages
        new_table = gtk.Table(
            rows=2,
            columns=len(self._mod_conf.configsets),
            homogeneous=False)
        new_table.set_col_spacings(5)
        # Add to the Table a Label and ScrolledWindow for each ConfigSet
        for index, configset in enumerate(self._mod_conf.configsets):
            # Make a Label of the ConfigSet's name
            label = gtk.Label(configset.name)
            # Add the Label to the Table
            new_table.attach(
                label, 
                left_attach=index,
                right_attach=index+1,
                top_attach=0,
                bottom_attach=1, 
                xoptions=gtk.EXPAND|gtk.FILL,
                yoptions=gtk.FILL,
                xpadding=0,
                ypadding=0)
            # Make a ScrolledWindow of the ConfigSet's assigned languages
            scrolledwindow = self._make_scrolledwindow(configset)
            # Add the ScrolledWindow to the Table
            new_table.attach(
                scrolledwindow, 
                left_attach=index,
                right_attach=index+1,
                top_attach=1,
                bottom_attach=2, 
                xoptions=gtk.EXPAND|gtk.FILL,
                yoptions=gtk.EXPAND|gtk.FILL,
                xpadding=0,
                ypadding=0)
        # Replace the old Table with the new Table
        lang_vbox.remove(old_table)
        lang_vbox.pack_start(new_table, expand=True, fill=True, padding=0)
        lang_vbox.show_all()
    
    def _make_scrolledwindow(self, configset):
        """Return a ScrolledWindow of the ConfigSet's assigned languages."""
        LOGGER.log()
        # Make a TreeView of the ConfigSet's assigned languages
        treeview = self._make_treeview(configset)
        # Configure the TreeView for being dragged from
        treeview.enable_model_drag_source(
            start_button_mask=gtk.gdk.BUTTON1_MASK,
            targets=[('list of languages', gtk.TARGET_SAME_APP, 0)],
            actions=gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY)
        treeview.connect("drag-data-get", self.on_drag_data_get)
        # Make a ScrolledWindow of the TreeView
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                                  vscrollbar_policy=gtk.POLICY_AUTOMATIC)
        scrolledwindow.set_shadow_type(gtk.SHADOW_IN)
        scrolledwindow.add(treeview)
        # Configure the ScrolledWindow for being dropped on
        scrolledwindow.set_name('sw_%s' % configset.name)
        scrolledwindow.drag_dest_set(
            flags=gtk.DEST_DEFAULT_ALL,
            targets=[('list of languages', gtk.TARGET_SAME_APP, 0)],
            actions=gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY)
        scrolledwindow.connect('drag-data-received',
                               self.on_drag_data_received)
        return scrolledwindow
    
    def _make_treeview(self, configset):
        """Return a TreeView of the ConfigSet's assigned languages."""
        LOGGER.log()
        # Make a ListStore of the ConfigSet's assigned languages
        liststore = self._make_liststore(configset)
        # Make a TreeView of the ListStore
        treeview = TreeViewDV(liststore)
        # Configure the TreeView
        tvcolumn = gtk.TreeViewColumn('Languages')
        treeview.append_column(tvcolumn)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'text', 0)
        treeview.set_search_column(0)
        tvcolumn.set_sort_column_id(0)
        treeview.set_reorderable(False)
        treeview.set_headers_visible(False)
        treeview.set_name('tv_%s' % configset.name)
        treeselection = treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_MULTIPLE)
        treeview.set_rubber_banding(True)
        if len(liststore) == 0:
            treeview.set_property('can-focus', False)
        return treeview
    
    def _make_liststore(self, configset):
        """Return a ListStore of the ConfigSet's assigned languages."""
        LOGGER.log()
        liststore = gtk.ListStore(str)
        langauge_assignments = sorted(self._mod_conf.languages.items())
        for language, configset_name in langauge_assignments:
            if configset_name == configset.name:
                liststore.append([language])
        return liststore
    


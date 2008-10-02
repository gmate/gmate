# -*- coding: utf-8 -*-

# Rails Hot Commands Gedit Plugin
#
# Copyright (C) 2007 - Tiago Bastos
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import gtk
import gedit
import vte
import os
import os.path
import gtk.glade
import gconf
from gettext import gettext as _
from terminal import TerminaldWidget

ui_str = """
<ui>
    <menubar name="MenuBar">
        <menu name="ViewMenu" action="View">
            <menuitem name="Rails Hot Commands" action="RailsHotcommands"/>
        </menu>
    </menubar>
</ui>
"""
all_commands_list = [
                    'script/server',
                    'script/console',
                    'script/about',
                    'script/breakpoint',
                    'script/destroy',                                        
                    'script/plugin',
                    'script/server',
                    'script/runner',
                    'rake db:migrate',                    
                    'rake asset:packager:build_all',
                    'rake asset:packager:create_yml',
                    'rake asset:packager:delete_all',
                    'rake db:fixtures:load',
                    'rake db:migrate',
                    'rake db:schema:dump',
                    'rake db:schema:load',
                    'rake db:sessions:clear',
                    'rake db:sessions:create',
                    'rake db:structure:dump',
                    'rake db:test:clone',
                    'rake db:test:clone_structure',
                    'rake db:test:prepare',
                    'rake db:test:purge',
                    'rake doc:app',
                    'rake doc:clobber_app',
                    'rake doc:clobber_plugins',
                    'rake doc:clobber_rails',
                    'rake doc:plugins',
                    'rake doc:rails',
                    'rake doc:reapp',
                    'rake doc:rerails',
                    'rake log:clear',
                    'rake rails:freeze:edge',
                    'rake rails:freeze:gems',
                    'rake rails:unfreeze',
                    'rake rails:update',
                    'rake rails:update:configs',
                    'rake rails:update:javascripts',
                    'rake rails:update:scripts',
                    'rake stats',
                    'rake test',
                    'rake test:functionals',
                    'rake test:integration',
                    'rake test:plugins',
                    'rake test:recent',
                    'rake test:uncommitted',
                    'rake test:units',
                    'rake tmp:cache:clear',
                    'rake tmp:clear',
                    'rake tmp:create',
                    'rake tmp:pids:clear',
                    'rake tmp:sessions:clear',
                    'rake tmp:sockets:clear'
                    ]

GLADE_FILE = os.path.join(os.path.dirname(__file__), "commandrunner.glade")

class RailsHotcommandsPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)

    def activate(self, window):
        self.window = window
        self.dialog = None
        self.bottom = window.get_bottom_panel()

        self.mount_list()

        actions = [
            ('RailsHotcommands', gtk.STOCK_SELECT_COLOR, _('Rails Hot Commands'), '<Control><Alt>c', _("Press Ctrl+Alt+c to run commands"), self.on_open)
        ]

        action_group = gtk.ActionGroup("RailsHotcommandsActions")
        action_group.add_actions(actions, self.window)

        self.manager = self.window.get_ui_manager()
        self.manager.insert_action_group(action_group, -1)
        self.manager.add_ui_from_string(ui_str)

    def run_command(self,command):
        term = TerminaldWidget(self.window)
        term.run(command)

    def on_open(self, *args):
        glade_xml = gtk.glade.XML(GLADE_FILE)

        if self.dialog:
            self.dialog.set_focus(True)
            return

        self.dialog = glade_xml.get_widget('railscommandrunner_dialog')
        self.dialog.connect('delete_event', self.on_close)
        self.dialog.show_all()
        self.dialog.set_transient_for(self.window)

        self.combo = glade_xml.get_widget('command_list')

        self.cancel_button = glade_xml.get_widget('cancel_button')
        self.cancel_button.connect('clicked', self.on_cancel)

        self.apply_button = glade_xml.get_widget('run_button')
        self.apply_button.connect('clicked', self.on_run)

        self.combo.set_model(self.model)
        self.combo.set_text_column(0)

        self.completion = gtk.EntryCompletion()
        self.completion.connect('match-selected', self.on_selected)
        self.completion.set_model(self.model)
        self.completion.set_text_column(0)

        self.entry = self.combo.get_children()[0]
        self.entry.set_completion(self.completion)

    def close_dialog(self):
        self.dialog.destroy()
        self.dialog = None

    def on_selected(self, completion, model, iter):
        c = model.get_value(iter, 0)
        self.run_command(c)

    def on_close(self, *args):
        self.close_dialog()

    def on_cancel(self, *args):
        self.close_dialog()

    def on_run(self, *args):
        c = self.entry.get_text()
        self.run_command(c)

    def deactivate(self, window):
        pass # :|
        
    def mount_list(self):
        self.model = gtk.ListStore(str)
        for command in all_commands_list:
            self.model.append([command])


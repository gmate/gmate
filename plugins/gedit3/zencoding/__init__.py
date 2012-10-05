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

#FIXME debug line remove
#import pydevd; pydevd.settrace()


from gi.repository import GObject, Gedit, Gtk, Gio

import os
from zen_editor import ZenEditor

zencoding_ui_str = """
<ui>
    <menubar name="MenuBar">
        <menu name="EditMenu" action="Edit">
            <placeholder name="EditOps_5">
                <menu action="ZenCodingMenuAction">
                    <menuitem name="ZenCodingExpand" action="ZenCodingExpandAction"/>
                    <menuitem name="ZenCodingExpandW" action="ZenCodingExpandWAction"/>
                    <menuitem name="ZenCodingWrap" action="ZenCodingWrapAction"/>
                    <separator/>
                    <placeholder name="EditOps_5">
                        <menu action="ZenCodingZenifyAction">
                            <menuitem name="ZenCodingZenify0" action="ZenCodingZenify0Action"/>
                            <menuitem name="ZenCodingZenify1" action="ZenCodingZenify1Action"/>
                            <menuitem name="ZenCodingZenify2" action="ZenCodingZenify2Action"/>
                            <menuitem name="ZenCodingZenify3" action="ZenCodingZenify3Action"/>
                        </menu>
                    </placeholder>
                    <separator/>
                    <menuitem name="LoremIpsum" action="LoremIpsumAction"/>
                    <separator/>
                    <menuitem name="ZenCodingInward" action="ZenCodingInwardAction"/>
                    <menuitem name="ZenCodingOutward" action="ZenCodingOutwardAction"/>
                    <separator/>
                    <menuitem name="ZenCodingPTag" action="ZenCodingPTagAction"/>
                    <menuitem name="ZenCodingNTag" action="ZenCodingNTagAction"/>
                    <menuitem name="ZenCodingPNode" action="ZenCodingPNodeAction"/>
                    <menuitem name="ZenCodingNNode" action="ZenCodingNNodeAction"/>
                    <menuitem name="ZenCodingPrev" action="ZenCodingPrevAction"/>
                    <menuitem name="ZenCodingNext" action="ZenCodingNextAction"/>
                    <separator/>
                    <menuitem name="ZenCodingSize" action="ZenCodingSizeAction"/>
                    <menuitem name="ZenCodingData" action="ZenCodingDataAction"/>
                    <separator/>
                    <menuitem name="ZenCodingMerge" action="ZenCodingMergeAction"/>
                    <menuitem name="ZenCodingRemove" action="ZenCodingRemoveAction"/>
                    <menuitem name="ZenCodingSplit" action="ZenCodingSplitAction"/>
                    <menuitem name="ZenCodingComment" action="ZenCodingCommentAction"/>
                    <separator/>
                    <menuitem name="ZenCodingSettings" action="ZenCodingSettingsAction"/>
                </menu>
            </placeholder>
        </menu>
    </menubar>
</ui>
"""

class ZenCodingWindowHelper():

    def __init__(self, window):

        # window
        self.window = window

        # menu items
        actions = [
            ('ZenCodingMenuAction',      None, '_Zen Coding',                   None,                  "Zen Coding tools",                             None),
            ('ZenCodingExpandAction',    None, '_Expand abbreviation',          '<Ctrl>E',             "Expand abbreviation to raw HTML/CSS",          self.expand_abbreviation),
            ('ZenCodingExpandWAction',   None, 'E_xpand with abbreviation...',  '<Ctrl><Alt>E',        "Type in an abbreviation to expand",            self.expand_with_abbreviation),
            ('ZenCodingWrapAction',      None, '_Wrap with abbreviation...',    '<Ctrl><Shift>E',      "Wrap with code expanded from abbreviation",    self.wrap_with_abbreviation),
            ('ZenCodingZenifyAction',    None, '_Zenify',                       None,                  "Reduce to abbreviation",                       None),
            ('ZenCodingZenify0Action',   None, '_Tag names',                    '<Ctrl><Alt>Z',        "Reduce to tag names only",                     self.zenify0),
            ('ZenCodingZenify1Action',   None, '  + _Ids and classes',          None,                  "Reduce with ids and classes",                  self.zenify1),
            ('ZenCodingZenify2Action',   None, '    + All other _attributes',   None,                  "Reduce with all attributes",                   self.zenify2),
            ('ZenCodingZenify3Action',   None, '      + _Values',               None,                  "Reduce with all attributes and values",        self.zenify3),
            ('LoremIpsumAction',         None, '_Lorem ipsum...',               '<Ctrl><Alt>X',        "Insert a lorem ipsum string",                  self.lorem_ipsum),
            ('ZenCodingInwardAction',    None, 'Select _inward',                '<Ctrl><Alt>I',        "Select inner tag's content",                   self.match_pair_inward),
            ('ZenCodingOutwardAction',   None, 'Select _outward',               '<Ctrl><Shift><Alt>O', "Select outer tag's content",                   self.match_pair_outward),
            ('ZenCodingPTagAction',      None, 'Previous tag',                  '<Ctrl><Alt>Up',       "Select the previous tag in HTML code",         self.prev_tag),
            ('ZenCodingNTagAction',      None, 'Next tag',                      '<Ctrl><Alt>Down',     "Select the next tag in HTML code",             self.next_tag),
            ('ZenCodingPNodeAction',     None, 'Previous node',                 '<Ctrl><Alt>Left',     "Select the previous HTML node",                self.prev_node),
            ('ZenCodingNNodeAction',     None, 'Next node',                     '<Ctrl><Alt>Right',    "Select the next HTML node",                    self.next_node),
            ('ZenCodingPrevAction',      None, '_Previous edit point',          '<Alt>Left',           "Place the cursor at the previous edit point",  self.prev_edit_point),
            ('ZenCodingNextAction',      None, '_Next edit point',              '<Alt>Right',          "Place the cursor at the next edit point",      self.next_edit_point),
            ('ZenCodingSizeAction',      None, 'Update image _size',            '<Ctrl><Alt>S',        "Update image size tag from file",              self.update_image_size),
            ('ZenCodingDataAction',      None, 'Toggle image url/da_ta',        '<Ctrl><Alt>A',        "Toggle between image url and data",            self.encode_decode_base64),
            ('ZenCodingMergeAction',     None, '_Merge lines',                  '<Ctrl><Alt>M',        "Merge all lines of the current selection",     self.merge_lines),
            ('ZenCodingRemoveAction',    None, '_Remove tag',                   '<Ctrl><Alt>R',        "Remove a tag",                                 self.remove_tag),
            ('ZenCodingSplitAction',     None, 'Split or _join tag',            '<Ctrl><Alt>J',        "Toggle between single and double tag",         self.split_join_tag),
            ('ZenCodingCommentAction',   None, 'Toggle _comment',               '<Ctrl><Alt>C',        "Toggle an XML or HTML comment",                self.toggle_comment),
            ('ZenCodingSettingsAction',  None, 'E_dit settings...',             None,                  "Customize snippets and abbreviations",         self.edit_settings)
        ]
        windowdata = dict()
        self.window.set_data("ZenCodingPluginDataKey", windowdata)
        windowdata["action_group"] = Gtk.ActionGroup("GeditZenCodingPluginActions")
        windowdata["action_group"].add_actions(actions)
        manager = self.window.get_ui_manager()
        manager.insert_action_group(windowdata["action_group"], -1)
        windowdata["ui_id"] = manager.add_ui_from_string(zencoding_ui_str)
        self.window.set_data("ZenCodingPluginInfo", windowdata)

        # zen coding
        self.modified = None
        self.editor = ZenEditor(self.window)

    def deactivate(self):

        # zen coding
        self.editor = None

        # menu items
        windowdata = self.window.get_data("ZenCodingPluginDataKey")
        manager = self.window.get_ui_manager()
        manager.remove_ui(windowdata["ui_id"])
        manager.remove_action_group(windowdata["action_group"])

        # window
        self.window = None

    def update_ui(self):
    
        # disabled if not editable
        view = self.window.get_active_view()
        windowdata = self.window.get_data("ZenCodingPluginDataKey")
        windowdata["action_group"].set_sensitive(bool(view and view.get_editable()))
        
        # user settings
        modified = os.path.getmtime(os.path.join(os.path.dirname(__file__), 'my_zen_settings.py'))
        if modified != self.modified:
            try:
                import my_zen_settings
                reload(my_zen_settings)
            except Exception as error:
                md = Gtk.MessageDialog(self.window, Gtk.DIALOG_MODAL, Gtk.MESSAGE_ERROR,
                    Gtk.BUTTONS_CLOSE, "An error occured in user settings:")
                message = "{0} on line {1} at character {2}\n\nUser settings will not be available."
                md.set_title("Zen Coding error")
                md.format_secondary_text(message.format(error.msg, error.lineno, error.offset))
                md.run()
                md.destroy()
            else:
                globals()['zen_core'].zen_settings = globals()['stparser'].get_settings(my_zen_settings.my_zen_settings)
            self.modified = modified

        # the content changed
        self.editor.set_context(view)
        
    # Menu handlers

    def expand_abbreviation(self, action):
        self.editor.expand_abbreviation()

    def expand_with_abbreviation(self, action):
        self.editor.expand_with_abbreviation()

    def wrap_with_abbreviation(self, action):
        self.editor.wrap_with_abbreviation()

    def zenify0(self, action):
        self.editor.zenify(0)

    def zenify1(self, action):
        self.editor.zenify(1)

    def zenify2(self, action):
        self.editor.zenify(2)

    def zenify3(self, action):
        self.editor.zenify(3)

    def lorem_ipsum(self, action):
        self.editor.lorem_ipsum()

    def match_pair_inward(self, action):
        self.editor.match_pair_inward()

    def match_pair_outward(self, action):
        self.editor.match_pair_outward()

    def prev_tag(self, action):
        self.editor.prev_tag()

    def next_tag(self, action):
        self.editor.next_tag()

    def prev_node(self, action):
        self.editor.prev_node()

    def next_node(self, action):
        self.editor.next_node()

    def prev_edit_point(self, action):
        self.editor.prev_edit_point()

    def next_edit_point(self, action):
        self.editor.next_edit_point()

    def update_image_size(self, action):
        self.editor.update_image_size()

    def encode_decode_base64(self, action):
        self.editor.encode_decode_base64()

    def merge_lines(self, action):
        self.editor.merge_lines()

    def remove_tag(self, action):
        self.editor.remove_tag()

    def split_join_tag(self, action):
        self.editor.split_join_tag()

    def toggle_comment(self, action):
        self.editor.toggle_comment()

    def edit_settings(self, action):
        uri = 'file://' + os.path.join(os.path.dirname(__file__), 'my_zen_settings.py')
        self.window.create_tab_from_location(Gio.file_new_for_uri(uri), None, 0, 0, True, True)


class ZenCodingPlugin(GObject.Object, Gedit.WindowActivatable):

    __gtype_name__ = "ZenCodingPlugin"
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self.instances = {}

	def deactivate(self, window):
		self.instances[window].deactivate()
		del self.instances[window]

    def do_activate(self):
        self.instances[self.window] = ZenCodingWindowHelper(self.window)

    def do_deactivate(self):
        self.instances[self.window].deactivate()
        del self.instances[self.window]

    def do_update_state(self):
        self.instances[self.window].update_ui()


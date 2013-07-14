# @file plugin.py
#
# Connect Zen Coding to Gedit.
#
# Author Franck Marcia (franck.marcia@gmail.com)
#
from gi.repository import Gedit, GObject, Gtk
import os
from zen_editor import ZenEditor

zencoding_ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="EditMenu" action="Edit">
      <placeholder name="EditOps_5">
        <menu action="ZenCodingMenuAction">
          <menuitem name="ZenCodingExpand"   action="ZenCodingExpandAction"/>
          <menuitem name="ZenCodingExpandW"  action="ZenCodingExpandWAction"/>
          <menuitem name="ZenCodingWrap"     action="ZenCodingWrapAction"/>
          <separator/>
          <menuitem name="ZenCodingInward"   action="ZenCodingInwardAction"/>
          <menuitem name="ZenCodingOutward"  action="ZenCodingOutwardAction"/>
          <menuitem name="ZenCodingMerge"    action="ZenCodingMergeAction"/>
          <separator/>
          <menuitem name="ZenCodingPrev"     action="ZenCodingPrevAction"/>
          <menuitem name="ZenCodingNext"     action="ZenCodingNextAction"/>
          <separator/>
          <menuitem name="ZenCodingRemove"   action="ZenCodingRemoveAction"/>
          <menuitem name="ZenCodingSplit"    action="ZenCodingSplitAction"/>
          <menuitem name="ZenCodingComment"  action="ZenCodingCommentAction"/>
        </menu>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class ZenCodingPlugin(GObject.Object, Gedit.WindowActivatable):
    """A Gedit plugin to implement Zen Coding's HTML and CSS shorthand expander."""

    window = GObject.property(type=Gedit.Window)
    
    def do_activate(self):
        actions = [
          ('ZenCodingMenuAction',     None, '_Zen Coding',                     None,                 "Zen Coding tools",                            None),
          ('ZenCodingExpandAction',   None, '_Expand abbreviation',            '<Ctrl>E',            "Expand abbreviation to raw HTML/CSS",         self.expand_abbreviation),
          ('ZenCodingExpandWAction',  None, '_Expand dynamic abbreviation...', '<Ctrl><Alt>E',       "Dynamically expand abbreviation as you type", self.expand_with_abbreviation),
          ('ZenCodingWrapAction',     None, '_Wrap with abbreviation...',      '<Ctrl><Shift>E',     "Wrap with code expanded from abbreviation",   self.wrap_with_abbreviation),
          ('ZenCodingInwardAction',   None, 'Balance tag _inward',             '<Ctrl><Alt>I',       "Select inner tag's content",                  self.match_pair_inward),
          ('ZenCodingOutwardAction',  None, 'Balance tag _outward',            '<Ctrl><Alt><Shift>O',"Select outer tag's content",                  self.match_pair_outward),
          ('ZenCodingMergeAction',    None, '_Merge lines',                    '<Ctrl><Alt>M',       "Merge all lines of the current selection",    self.merge_lines),
          ('ZenCodingPrevAction',     None, '_Previous edit point',            '<Alt>Left',          "Place the cursor at the previous edit point", self.prev_edit_point),
          ('ZenCodingNextAction',     None, '_Next edit point',                '<Alt>Right',         "Place the cursor at the next edit point",     self.next_edit_point),
          ('ZenCodingRemoveAction',   None, '_Remove tag',                     '<Ctrl><Alt>R',       "Remove a tag",                                self.remove_tag),
          ('ZenCodingSplitAction',    None, 'Split or _join tag',              '<Ctrl><Alt>J',       "Toggle between single and double tag",        self.split_join_tag),
          ('ZenCodingCommentAction',  None, 'Toggle _comment',                 '<Ctrl><Alt>C',       "Toggle an XML or HTML comment",               self.toggle_comment)
        ]
        windowdata = dict()
        self.window.ZenCodingPluginDataKey = windowdata
        windowdata["action_group"] = Gtk.ActionGroup("GeditZenCodingPluginActions")
        windowdata["action_group"].add_actions(actions)
        manager = self.window.get_ui_manager()
        manager.insert_action_group(windowdata["action_group"], -1)
        windowdata["ui_id"] = manager.add_ui_from_string(zencoding_ui_str)
        self.window.ZenCodingPluginInfo = windowdata
        self.editor = ZenEditor()
        error = self.editor.get_user_settings_error()
        if error:
            md = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.CLOSE, "There is an error in user settings:")
            message = "{0} on line {1} at character {2}\n\nUser settings will not be available."
            md.set_title("Zen Coding error")
            md.format_secondary_text(message.format(error['msg'], error['lineno'], error['offset']))
            md.run()
            md.destroy()


    def do_deactivate(self):
        windowdata = self.window.ZenCodingPluginDataKey
        manager = self.window.get_ui_manager()
        manager.remove_ui(windowdata["ui_id"])
        manager.remove_action_group(windowdata["action_group"])

    def do_update_state(self):
        view = self.window.get_active_view()
        windowdata = self.window.ZenCodingPluginDataKey
        windowdata["action_group"].set_sensitive(bool(view and view.get_editable()))

    def expand_abbreviation(self, action):
        self.editor.expand_abbreviation(self.window)
        
    def expand_with_abbreviation(self, action):
        self.editor.expand_with_abbreviation(self.window)

    def wrap_with_abbreviation(self, action):
        self.editor.wrap_with_abbreviation(self.window)

    def match_pair_inward(self, action):
        self.editor.match_pair_inward(self.window)

    def match_pair_outward(self, action):
        self.editor.match_pair_outward(self.window)

    def merge_lines(self, action):
        self.editor.merge_lines(self.window)

    def prev_edit_point(self, action):
        self.editor.prev_edit_point(self.window)

    def next_edit_point(self, action):
        self.editor.next_edit_point(self.window)

    def remove_tag(self, action):
        self.editor.remove_tag(self.window)

    def split_join_tag(self, action):
        self.editor.split_join_tag(self.window)

    def toggle_comment(self, action):
        self.editor.toggle_comment(self.window)

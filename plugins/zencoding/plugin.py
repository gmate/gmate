# @file plugin.py
#
# Connect Zen Coding to Gedit.
#

import gedit, gobject, gtk

from zen_editor import ZenEditor

zencoding_ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="EditMenu" action="Edit">
      <placeholder name="EditOps_5">
        <menu action="ZenCodingMenuAction">
          <menuitem name="ZenCodingExpand"  action="ZenCodingExpandAction"/>
          <menuitem name="ZenCodingWrap"    action="ZenCodingWrapAction"/>
          <separator/>
          <menuitem name="ZenCodingInward"  action="ZenCodingInwardAction"/>
          <menuitem name="ZenCodingOutward" action="ZenCodingOutwardAction"/>
          <menuitem name="ZenCodingMerge"   action="ZenCodingMergeAction"/>
          <separator/>
          <menuitem name="ZenCodingPrev"    action="ZenCodingPrevAction"/>
          <menuitem name="ZenCodingNext"    action="ZenCodingNextAction"/>
          <separator/>
          <menuitem name="ZenCodingSize"    action="ZenCodingSizeAction"/>
          <separator/>
          <menuitem name="ZenCodingRemove"  action="ZenCodingRemoveAction"/>
          <menuitem name="ZenCodingSplit"   action="ZenCodingSplitAction"/>
          <menuitem name="ZenCodingComment" action="ZenCodingCommentAction"/>
        </menu>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class ZenCodingPlugin(gedit.Plugin):
    """A Gedit plugin to implement Zen Coding's HTML and CSS shorthand expander."""

    def activate(self, window):
        actions = [
          ('ZenCodingMenuAction',    None, 'Zen Coding',            None,            "Zen Coding framework",                                None),
          ('ZenCodingExpandAction',  None, 'Expand Zen Code',       '<Ctrl>E',        "Expand Zen code to raw HTML/CSS",                     self.expand_abbreviation),
          ('ZenCodingWrapAction',    None, 'Wrap with Zen Code...', '<Ctrl><Shift>E', "Wrap selection with HTML/CSS expanded from Zen code", self.wrap_with_abbreviation),
          ('ZenCodingInwardAction',  None, 'Balance tag inward',    '<Ctrl><Alt>I',   "Select inner tag's content",                          self.match_pair_inward),
          ('ZenCodingOutwardAction', None, 'Balance tag outward',   '<Ctrl><Alt>O',   "Select outer tag's content",                          self.match_pair_outward),
          ('ZenCodingMergeAction',   None, 'Merge lines',           '<Ctrl><Alt>M',   "Merge all lines of the current selection",            self.merge_lines),
          ('ZenCodingPrevAction',    None, 'Previous edit point',   '<Alt>Left',      "Place the cursor at the previous edit point",         self.prev_edit_point),
          ('ZenCodingNextAction',    None, 'Next edit point',       '<Alt>Right',     "Place the cursor at the next edit point",             self.next_edit_point),
          ('ZenCodingSizeAction',    None, 'Update image size',     '<Ctrl><Alt>S',   "Update image size tag from file",                     self.update_image_size),
          ('ZenCodingRemoveAction',  None, 'Remove tag',            '<Ctrl><Alt>R',   "Remove a tag",                                        self.remove_tag),
          ('ZenCodingSplitAction',   None, 'Split or join tag',     '<Ctrl><Alt>J',   "Toggle between single and double tag",                self.split_join_tag),
          ('ZenCodingCommentAction', None, 'Toggle comment',        '<Ctrl><Alt>C',   "Toggle an XML or HTML comment",                       self.toggle_comment)
        ]
        windowdata = dict()
        window.set_data("ZenCodingPluginDataKey", windowdata)
        windowdata["action_group"] = gtk.ActionGroup("GeditZenCodingPluginActions")
        windowdata["action_group"].add_actions(actions, window)
        manager = window.get_ui_manager()
        manager.insert_action_group(windowdata["action_group"], -1)
        windowdata["ui_id"] = manager.add_ui_from_string(zencoding_ui_str)
        window.set_data("ZenCodingPluginInfo", windowdata)
        self.editor = ZenEditor()

    def deactivate(self, window):
        windowdata = window.get_data("ZenCodingPluginDataKey")
        manager = window.get_ui_manager()
        manager.remove_ui(windowdata["ui_id"])
        manager.remove_action_group(windowdata["action_group"])

    def update_ui(self, window):
        view = window.get_active_view()
        windowdata = window.get_data("ZenCodingPluginDataKey")
        windowdata["action_group"].set_sensitive(bool(view and view.get_editable()))

    def expand_abbreviation(self, action, window):
        self.editor.expand_abbreviation(window)

    def wrap_with_abbreviation(self, action, window):
        self.editor.wrap_with_abbreviation(window)

    def match_pair_inward(self, action, window):
        self.editor.match_pair_inward(window)

    def match_pair_outward(self, action, window):
        self.editor.match_pair_outward(window)

    def merge_lines(self, action, window):
        self.editor.merge_lines(window)

    def prev_edit_point(self, action, window):
        self.editor.prev_edit_point(window)

    def next_edit_point(self, action, window):
        self.editor.next_edit_point(window)

    def update_image_size(self, action, window):
        self.editor.update_image_size(window)

    def remove_tag(self, action, window):
        self.editor.remove_tag(window)

    def split_join_tag(self, action, window):
        self.editor.split_join_tag(window)

    def toggle_comment(self, action, window):
        self.editor.toggle_comment(window)

        return True

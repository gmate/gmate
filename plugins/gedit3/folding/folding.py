# -*- coding: utf-8 -*-
from gi.repository import GObject, Gedit, Gtk

ui_str = """<ui>
    <menubar name="MenuBar">
        <menu name="ToolsMenu" action="Tools">
            <placeholder name="ToolsOps_2">
                <menuitem name="ToggleFold" action="ToggleFold"/>
            </placeholder>
            <placeholder name="ToolsOps_2">
                <menuitem name="FoldDeepest" action="FoldDeepest"/>
            </placeholder>
            <placeholder name="ToolsOps_2">
                <menuitem name="UnFoldAll" action="UnFoldAll"/>
            </placeholder>
        </menu>
    </menubar>
</ui>
"""

class FoldingPyPlugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = 'FoldingPyPlugin'
    window = GObject.property(type=Gedit.Window)
    
    def __init__(self):
        GObject.Object.__init__(self)
    
    def do_activate(self):
        self._insert_menu()
        self.do_update_state()
    
    def do_deactivate(self):
        self._remove_menu()
        self._action_group = None
        #self.fold_off
    
    def do_update_state(self):
        action_group = self._action_group
        action_group.set_sensitive(self.window.get_active_document() != None)
        self.doc = self.window.get_active_document()
        if self.doc:
            self.view = self.window.get_active_view()
            table = self.doc.get_tag_table()
            self.fld = table.lookup('fld')
            if self.fld == None:
                self.fld = self.doc.create_tag('fld', foreground="#333333",
                    paragraph_background="#aadc5c")
            self.inv=table.lookup('inv')
            if self.inv == None:
                self.inv = self.doc.create_tag('inv', invisible=True)
    
    def _insert_menu(self):
        manager = self.window.get_ui_manager()
        self._action_group = Gtk.ActionGroup("FoldingPyPluginActions")
        self._action_group.add_actions([
            ("ToggleFold", None, _("Fold/Unfold"), "<Alt>Z", _("Fold/Unfold"),
                lambda a: self.fold()),
            ("FoldDeepest", None, _("Fold Deepest"), "<Alt>X",
                _("Fold Deepest"), lambda a: self.fold_deepest()),
            ("UnFoldAll", None, _("Un-Fold All"), "<Shift><Alt>X",
                _("Un-Fold All"), lambda a: self.fold_off())
        ])
        manager.insert_action_group(self._action_group, -1)
        self._ui_id = manager.add_ui_from_string(ui_str)
    
    def _remove_menu(self):
        manager = self.window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()
    
    def detect_sps(self,sps):
        sps_lstrip = sps.lstrip()
        i = sps.index(sps_lstrip)
        sps = sps[:i]
        return sps.count(' ') + sps.count('\t') * self.view.get_tab_width()
    
    def fold_deepest(self, action=None):
        deepest = 0
        lines = list()
        s = self.doc.get_iter_at_line(0)
        e = s.copy()
        sg = 0
        eg = 0
        while s.forward_visible_line():
            if s.get_char()!="\n":
                e.set_line(s.get_line())
                e.forward_to_line_end()
                text = s.get_text(e)
                if text.strip()!="":
                    indent = self.detect_sps(text)
                    if indent:
                        if indent > deepest:
                            deepest = indent
                            lines = list()
                            sg = s.get_line()
                            eg = s.get_line()
                        elif indent < deepest and eg:
                            lines.append((sg-1, eg))
                            eg = 0
                        elif indent == deepest:
                            if not eg:
                                sg = s.get_line()
                            eg = s.get_line()
        if eg:
            lines.append((sg-1, eg))
        for (sg, eg) in lines:
            s.set_line(sg)
            e.set_line(eg)
            self.fold(None, s, e)
    def fold_off(self,action=None):
        s , e = self.doc.get_bounds()
        self.doc.remove_tag(self.fld, s, e)
        self.doc.remove_tag(self.inv, s, e)
    def fold(self, action=None, a=None, c=None):
        if a == None:
            a = self.doc.get_iter_at_mark(self.doc.get_insert())
        if a.has_tag(self.fld):
            try:
                a.set_line_offset(0)
                b = a.copy()
                b.forward_line()
                self.doc.remove_tag(self.fld, a, b)
                a.forward_to_tag_toggle(self.inv)
                b.forward_to_tag_toggle(self.inv)
                self.doc.remove_tag(self.inv, a, b)
            except:
                pass
        elif (a != None and c != None) or \
            len(self.doc.get_selection_bounds()) == 2:
            if c == None:
                a, c = self.doc.get_selection_bounds()
            if a.get_line() == c.get_line():
                return
            b = a.copy()
            a.set_line_offset(0)
            b.forward_line()
            c.forward_line()
            self.doc.apply_tag(self.fld,a,b)
            # TODO: Don't remove already folded tags and keep track of nested tags
            self.doc.remove_tag(self.fld, b, c)
            self.doc.remove_tag(self.inv, b, c)
            self.doc.apply_tag(self.inv, b, c)
        else:
            a.set_line_offset(0)
            line = a.get_line()
            sfold = a.copy()
            sfold.forward_line()
            text = a.get_text(sfold)
            if text.strip() != "":
                main_indent = self.detect_sps(text)
                fin = a.copy()
                e = a.copy()
                while 1 == 1:
                    if e.forward_line():
                        if e.get_char() == "\n":
                            continue
                        ne = e.copy()
                        ne.forward_to_line_end()
                        text = e.get_text(ne)
                        if text.strip() == "":
                            continue
                        child_indent = self.detect_sps(text)
                        if child_indent <= main_indent:
                            break
                        else:
                            line = e.get_line()
                        fin.set_line(line)
                        fin.forward_line()
                    else:
                        fin.forward_to_end()
                        line = fin.get_line()
                        break
                if a.get_line() < line:
                    self.doc.apply_tag(self.fld, a, sfold)
                    # TODO: Don't remove already folded tags and
                    # keep track of nested tags
                    self.doc.remove_tag(self.fld, sfold, fin)
                    self.doc.remove_tag(self.inv, sfold, fin)
                    self.doc.apply_tag(self.inv, sfold, fin)

# -*- coding: utf8 -*-
# vim: ts=4 nowrap expandtab textwidth=80
# Rails Extract Partial Plugin
# Copyright © 2008 Alexandre da Silva / Carlos Antonio da Silva
#
# This file is part of Gmate.
#
# See LICENTE.TXT for licence information

import gedit
import gtk
import gnomevfs
import os.path

class ExtractPartialPlugin(gedit.Plugin):

    ui_str = """
    <ui>
      <menubar name="MenuBar">
        <menu name="EditMenu" action="Edit">
          <placeholder name="EditOps_6">
              <menuitem action="ExtractPartial"/>
          </placeholder>
        </menu>
      </menubar>
    </ui>
    """
    #

    bookmarks = {}

    def __init__(self):
        gedit.Plugin.__init__(self)

    def activate(self, window):
        self.__window = window
        actions = [('ExtractPartial', None, 'Extract Partial',
                    '<Alt><Control>p', 'Extract select text to a partial',
                    self.extract_partial)]
        windowdata = dict()
        window.set_data("ExtractPartialPluginWindowDataKey", windowdata)
        windowdata["action_group"] = gtk.ActionGroup("GeditExtractPartialPluginActions")
        windowdata["action_group"].add_actions(actions, window)
        manager = window.get_ui_manager()
        manager.insert_action_group(windowdata["action_group"], -1)
        windowdata["ui_id"] = manager.add_ui_from_string(self.ui_str)
        window.set_data("ExtractPartialPluginInfo", windowdata)

    def deactivate(self, window):
        windowdata = window.get_data("ExtractPartialPluginWindowDataKey")
        manager = window.get_ui_manager()
        manager.remove_ui(windowdata["ui_id"])
        manager.remove_action_group(windowdata["action_group"])

    def update_ui(self, window):
        view = window.get_active_view()

        windowdata = window.get_data("ExtractPartialPluginWindowDataKey")
        windowdata["action_group"].set_sensitive(bool(view and view.get_editable()))

    def create_file(self, window, file_uri, text):
        window.create_tab_from_uri(str(file_uri),
                                        gedit.encoding_get_current(),
                                        0, True, True)
        view = window.get_active_view()
        buf = view.get_buffer()
        doc = window.get_active_document()
        doc.begin_user_action()
        buf.insert_interactive_at_cursor(text, True)
        doc.end_user_action()

    def extract_partial(self, action, window):
        doc = window.get_active_document()
        view = window.get_active_view()
        buf = view.get_buffer()
        language = buf.get_language()
        # Only RHTML
        if language.get_id() != 'rhtml': return
        str_uri = doc.get_uri()
        if buf.get_has_selection():
            if str_uri:
                uri = gnomevfs.URI(str_uri)
                if uri:
                    path = uri.scheme + '://' + uri.dirname
                    dialog = gtk.Dialog("Enter partial Name",
                             window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                             (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
                    dialog.set_alternative_button_order([gtk.RESPONSE_ACCEPT, gtk.RESPONSE_CANCEL])
                    dialog.vbox.pack_start(gtk.Label("Don't use _ nor extension(html.erb/erb/rhtml)"))
                    entry = gtk.Entry()
                    entry.connect('key-press-event', self.__dialog_key_press, dialog)
                    dialog.vbox.pack_start(entry)
                    dialog.show_all()
                    response = dialog.run()
                    if response == gtk.RESPONSE_ACCEPT:
                        partial_name = entry.get_text()
                        doc_name = doc.get_short_name_for_display()
                        extension = self.__get_file_extension(doc_name)
                        itstart, itend = doc.get_selection_bounds()
                        partial_text = doc.get_slice(itstart, itend, True)
                        partial_render = '<%%= render :partial => "%s" %%>' % partial_name
                        doc.begin_user_action()
                        doc.delete(itstart, itend)
                        doc.insert_interactive(itstart, partial_render, True)
                        doc.end_user_action()
                        file_name = "%s/_%s%s" % (path, partial_name, extension)
                        self.create_file(window, file_name, partial_text)
                    dialog.destroy()
        else: return

    def __get_file_extension(self, doc_name):
        name, ext = os.path.splitext(doc_name)
        if ext == '.rhtml':
            return ext
        if ext == '.erb':
            name, ext = os.path.splitext(name)
            return "%s.erb" % ext
        return '.html.erb'

    def __dialog_key_press(self, widget, event, dialog):
        if event.keyval == 65293:
            dialog.response(gtk.RESPONSE_ACCEPT)

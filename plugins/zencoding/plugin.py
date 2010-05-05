#
# @file plugin.py
#
# Connect Zen Coding to Gedit.
#

import gedit, gobject, string, gtk, re, zen_core

class ZenCodingPlugin(gedit.Plugin):
    """A Gedit plugin to implement Zen Coding's HTML and CSS shorthand expander."""

    def activate(self, window):
        """Install the expansion feature upon activation."""

        ui_manager = window.get_ui_manager()
        action_group = gtk.ActionGroup("GeditZenCodingPluginActions")

        # Create the GTK action to be used to connect the key combo
        # to the Zen Coding expansion (i.e., the good stuff).
        complete_action = gtk.Action(name="ZenCodingAction",
                                     label="Expand Zen code",
                                     tooltip="Expand Zen Code in document to raw HTML/CSS",
                                     stock_id=gtk.STOCK_GO_FORWARD)

        # Connect the newly created action with key combo
        complete_action.connect("activate",
                                lambda a: self.expand_zencode(window))
        action_group.add_action_with_accel(complete_action, "<Shift><Ctrl>E")

        ui_manager.insert_action_group(action_group, 0)

        # @TODO: Figure out what these lines do
        ui_merge_id = ui_manager.new_merge_id()
        ui_manager.add_ui(ui_merge_id,
                          "/MenuBar/EditMenu/EditOps_5",
                          "ZenCoding",
                          "ZenCodingAction",
                          gtk.UI_MANAGER_MENUITEM, False)
        ui_manager.__ui_data__ = (action_group, ui_merge_id)

    def deactivate(self, window):
        """Get rid of the expansion feature upon deactivation"""

        ui_manager = window.get_ui_manager()
        (action_group, ui_merge_id) = ui_manager.__ui_data__

        # Remove the UI data, action group, and UI itself from Gedit
        del ui_manager.__ui_data__
        ui_manager.remove_action_group(action_group)
        ui_manager.remove_ui(ui_merge_id)


    def expand_zencode(self, window):
        """Take the shorthand code, expand it, and stick it back in the document."""

        view = window.get_active_view()
        buffer = view.get_buffer()
        cursor_iter = buffer.get_iter_at_mark(buffer.get_insert())
        statusbar = window.get_statusbar()

        # Grab the current line.
        line = self.get_line(buffer, cursor_iter)

        # Get shorthand from selection...
        is_selection = False
        if buffer.get_has_selection():
            insert_iter = buffer.get_iter_at_mark(buffer.get_insert())
            bound_iter = buffer.get_iter_at_mark(buffer.get_selection_bound())
            before = buffer.get_text(bound_iter, insert_iter)
            cursor_iter = (bound_iter if bound_iter.compare(insert_iter) == 1 else insert_iter).copy()
            buffer.place_cursor(cursor_iter)
            is_selection = True

        # ... or from previous word
        else:
            before = self.get_shorthand(line)
            if not before:
                return

        # Generate expanded code from the shorthand code based on the document's language.
        lang = self.get_language(window)
        if lang == 'CSS': lang = 'css'
        elif lang == 'XSLT': lang = 'xsl'
        else: lang = 'html'
        after = zen_core.expand_abbreviation(before, lang, 'xhtml')
        if not after:
            if is_selection:
                buffer.select_range(insert_iter, bound_iter)
            return

        # Indent the expanded code according to editor's preferences.
        after = self.indent_code(line, after, window)

        # Replace the shorthand code with the expanded code.
        if self.replace_with_expanded(cursor_iter, buffer, before, after, window.get_active_document()):
            statusbar.push(statusbar.get_context_id('ZenCodingPlugin'), 'Expanded shorthand code into the real stuff.')
        else:
            statusbar.push(statusbar.get_context_id('ZenCodingPlugin'), 'Code couldn\'t expand. Try checking your syntax for mistakes.')

    def get_line(self, buffer, cursor_iter):
        """Get the full line currently being edited."""

        # Grab the first character in the line.
        line_iter = cursor_iter.copy()
        line_iter.set_line_offset(0)

        # Grab the text from the start of the line to the cursor.
        line = buffer.get_text(line_iter, cursor_iter)

        return line

    def indent_code(self, line, code, editor):
        """Indent the code properly according to the editor's preferences."""

        # Automatically indent the string and replace \t (tab) with the
        # correct number of spaces.
        code = zen_core.pad_string(code, re.match(r"\s*", line).group())
        if editor.get_active_view().get_insert_spaces_instead_of_tabs():
            code = code.replace("\t", " " * editor.get_active_view().get_tab_width())

        return code

    def get_language(self, editor):
        """Get the language of the current document."""

        lang = editor.get_active_document().get_language()
        lang = lang and lang.get_name()

        return lang

    def get_shorthand(self, line):
        """Grab the last word typed (i.e., the shorthand code)."""
        return re.split('\s+', line)[-1]

    def replace_with_expanded(self, cursor_iter, buffer, before, after, document):
        """Replace the shorthand code with the expanded code."""

        # Replace the original caret_placerholder with a nicer one
        after = after.replace(zen_core.caret_placeholder, '[ ]')

        # Save cursor's current location
        offset = cursor_iter.get_offset()

        # Delete the last word in the line (i.e., the 'before' text, aka the
        # Zen un-expanded code), so that we can replace it.
        word_iter = cursor_iter.copy()
        word_iter.set_line_index(cursor_iter.get_line_index() - len(before))
        buffer.delete(word_iter, cursor_iter)

        # Insert the new expanded text.
        buffer.insert_at_cursor(after)

        # Set parameters for search
        end_iter = buffer.get_iter_at_mark(buffer.get_insert())
        buffer.place_cursor(buffer.get_iter_at_offset(offset - len(before)))
        begin_iter = buffer.get_iter_at_mark(buffer.get_insert())
        begin_match = begin_iter.copy()
        end_match = end_iter.copy()

        # Do search
        document.set_search_text('[ ]', 0)
        document.search_forward(begin_iter, end_iter, begin_match, end_match)
        buffer.select_range(begin_match, end_match)

        return True

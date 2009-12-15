"""
    Multi-edit - Gedit plugin
    Copyright (C) 2009 Jonathan Walsh
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import string
import csv

import gtk
import gtk.glade

class WindowInstance:
    """ A window's multi-edit instance """
    
    # ============================================================ Event handlers
    def __init__(self, plugin, window):
        self._plugin = plugin
        self._window = window
        self._tab = None
        # Tab change handler
        self._tab_event = self._window.connect('active-tab-changed', self._tab_change)
        # Load the currently active tab
        self._tab_change(self._window, self._window.get_active_tab())
    
    def deactivate(self):
        """ Handle window deactivation. """
        self._destroy_settings()
        self._window.disconnect(self._tab_event)
    
    def _tab_change(self, window, tab):
        """ Handle tab changes and reassign all references to the new tab. """
        # Destroy previous tab references
        if self._tab is not None:
            self._destroy_settings()
        
        # Note: _tab, _view, _buffer: all refer to different parts of the currently active tab
        self._tab = tab
        if tab is not None:
            self._view = tab.get_view()
            self._buffer = tab.get_document()
            
            # Event handlers
            self._view_event = self._view.connect('event', self._event_wrapper)
            self._text_change = self._buffer.connect('changed', self._text_changed)
            self._mark_move = self._buffer.connect('mark-set', self._mark_moved)
            
            # Mark related
            self._marks = []
            self._mark_i = 0
            self._line_offset_mem = None
            self._vert_mark_mem = None  # Filled format = (line_num, smart_nav)
            
            # Event trackers
            self._mouse_event = {'current':False, 'followup':False}
            self._change_supported = False
            self._cursor_move_supported = [False, False]  # [insert, selection_bound]
    
    def _destroy_settings(self):
        """ Exit multi-edit mode and carefully remove previous tab references. """
        # Remove textbuffer markers
        self._clear_marks()
        
        # Disconnect event handlers
        self._view.disconnect(self._view_event)
        self._buffer.disconnect(self._text_change)
        self._buffer.disconnect(self._mark_move)
        
        # Destroy references to previous tab
        del self._tab
        del self._view
        del self._buffer
    
    def _event_wrapper(self, dont_use, event):
        """ Wrapper for all TextView events.
        
        Used instead of more specific signals, to gain priority over other plugins.
        Appropriate given that Multi-edit will still pass on events if in single-edit mode.
        """
        if event.type == gtk.gdk.KEY_PRESS:
            result = self._keyboard_handler(event)
            # Ensure cursor remains visible during text modifications
            # Only scroll if multi-edit is managing the event
            if result:
                self._view.scroll_mark_onscreen(self._buffer.get_insert())
            return result
        
        if event.type == gtk.gdk.BUTTON_PRESS:
            return self._mouse_handler(event, 'press')
        
        if event.type == gtk.gdk.BUTTON_RELEASE:
            return self._mouse_handler(event, 'release')
        
        return False
    
    def _mark_moved(self, textbuffer, textiter, mark):
        """ Track cursor movement and exit if unsupported. """
        if mark.get_name() == 'insert':
            if self._cursor_move_supported[0]:
                self._cursor_move_supported[0] = False
            else:
                self._clear_marks()
        elif mark.get_name() == 'selection_bound':
            if self._cursor_move_supported[1]:
                self._cursor_move_supported[1] = False
            else:
                self._clear_marks()
        return False
    
    def _text_changed(self, *args):
        """ Check text changes and exit multi-edit mode if unsupported. """
        if self._change_supported:
            self._change_supported = False
        else:
            self._clear_marks()
        return False
    
    def _mouse_handler(self, event, type_):
        """ Handle mouse button events.
        
        Return value: True kills the event, False passes it on
        """
        # Modifier checks
        ctrl_on = event.state & gtk.gdk.CONTROL_MASK
        shift_on = event.state & gtk.gdk.SHIFT_MASK
        alt_on = event.state & gtk.gdk.MOD1_MASK
        
        # Clear line/offset memory
        self._line_offset_mem = None
        self._vert_mark_mem = None
        
        # Requirements
        if (type_ == 'press' and not ctrl_on) or alt_on or event.button not in (1, 3):
            return False
        
        # ---------------------------------------- Mark actions
        
        # Add marks [cursor movement]
        if type_ == 'press':
            self._mouse_event = {'current':False}  # to be safe
            
            # Get pos
            win_type = self._view.get_window_type(event.window)
            pos = self._view.window_to_buffer_coords(win_type, int(event.x), int(event.y))
            pos = self._view.get_iter_at_location(pos[0], pos[1])
            
            # Multiple mark placement
            if shift_on:
                old_pos = self._buffer.get_iter_at_mark(self._buffer.get_insert())
                dif = pos.get_line() - old_pos.get_line()
                down = abs(dif) == dif
                smart_nav = event.button == 3
                for i in range(abs(dif)):
                    self._vertical_cursor_nav(down, smart_nav)
                self._mouse_event = {'current':True, 'followup':False}
                return True
            
            # Single mark placement
            elif event.button == 1:
                self._cursor_move_supported = [True, True]
                self._buffer.place_cursor(pos)
                self._add_remove_mark()
                self._mouse_event = {'current':True, 'followup':True}
                return True
        
        # Finish multi-edit events
        elif self._mouse_event['current']:
            if type_ == 'release':
                #if self._mouse_event['followup']:
                #    pass
                self._mouse_event = {'current':False}
            else:
                # Drag event
                pass
            return True
        
        return False
    
    def _keyboard_handler(self, event):
        """ Handle keyboard events.
        
        Return value: True kills the event, False passes it on
        Note: Unsupported events will exit multi-edit mode (for safety reasons)
        """
        
        # Modifier checks
        ctrl_on = event.state & gtk.gdk.CONTROL_MASK
        shift_on = event.state & gtk.gdk.SHIFT_MASK
        alt_on = event.state & gtk.gdk.MOD1_MASK
        caps_on = event.state & gtk.gdk.LOCK_MASK
        
        # Undo caps lock for shortcuts
        if caps_on and ctrl_on:
            if shift_on:
                event.keyval = int(gtk.gdk.keyval_to_upper(event.keyval))
            else:
                event.keyval = int(gtk.gdk.keyval_to_lower(event.keyval))
        
        #print event.keyval  # dev use
        
        # Ignore safe keys (to prevent them affecting the offset mems)
        # Note: safe keys are keys that do nothing by themselves
        safe_keys = (
            gtk.keysyms.Shift_L,
            gtk.keysyms.Shift_R,
            gtk.keysyms.Control_L,
            gtk.keysyms.Control_R,
            gtk.keysyms.Alt_L,
            gtk.keysyms.Alt_R,
        )
        if event.keyval in safe_keys:
            return False
        
        # ---------------------------------------- Vertical movement memory
        # Reset vertical mark memory
        vert_mark_mem_backup = self._vert_mark_mem
        self._vert_mark_mem = None
        
        # Reset line offset
        line_offset_mem_backup = self._line_offset_mem
        self._line_offset_mem = None
        
        # ---------------------------------------- Mark actions
        if ctrl_on:
            # Add mark
            keyval, shift_req = self._plugin._sc_add_mark
            if event.keyval == keyval and (shift_req is None or shift_req == shift_on):
                self._add_remove_mark()
                return True
            
            # Add marks vertically
            for sc in self._plugin._sc_mark_vert:
                keyval, shift_req = self._plugin._sc_mark_vert[sc]
                if event.keyval == keyval and (shift_req is None or shift_req == shift_on) \
                   and (len(self._marks) != 0 or self._plugin._columns_always_avail):
                    # Recover vertical move mems, regardless if needed
                    # (since _vertical_cursor_nav() will handle it)
                    self._vert_mark_mem = vert_mark_mem_backup
                    self._line_offset_mem = line_offset_mem_backup
                    # Get values based on key
                    down = sc[-2:] != 'up'
                    smart_nav = sc[:2] == 'sm'
                    self._vertical_cursor_nav(down, smart_nav)
                    return True
        
        # ---------------------------------------- Edit actions
        if len(self._marks) != 0:
            
            # Multi-modifier support (so far just tab)
            if not ctrl_on:
                if event.keyval == gtk.keysyms.ISO_Left_Tab and not alt_on:
                    self._multi_edit('left_tab')
                    return True
                if event.keyval == gtk.keysyms.Tab:
                    if self._view.get_insert_spaces_instead_of_tabs() and not alt_on:
                        self._multi_edit('space_tab')
                    else:
                        self._multi_edit('insert', '\t')
                    return True
            
            # Alt support drop
            if alt_on:
                return False
            
            # Shortcuts
            if ctrl_on:
                
                # Temp auto-increment
                keyval, shift_req = self._plugin._sc_temp_incr
                if event.keyval == keyval and (shift_req is None or shift_req == shift_on):
                    self._auto_incr_dialog()
                    return True
                
                # Paste clipboard
                if event.keyval == gtk.keysyms.v:
                    self._multi_edit('insert', gtk.clipboard_get().wait_for_text())
                    return True
                
                # Auto-increment
                if event.keyval in self._plugin._sc_auto_incr:
                    entry = self._plugin._sc_auto_incr[event.keyval]
                    if entry['shift_req'] is None or entry['shift_req'] == shift_on:
                        values = self._auto_increment(entry)
                        self._multi_edit('increment', values)
                        return True
                
                # Level marks
                keyval, shift_req = self._plugin._sc_level_marks
                if event.keyval == keyval and (shift_req is None or shift_req == shift_on):
                        self._multi_edit('level')
                        return True
                
                # Preserve marks
                if event.keyval in (gtk.keysyms.Up, gtk.keysyms.Down):
                    self._line_offset_mem = line_offset_mem_backup  # Recover line offset mem
                    down = event.keyval == gtk.keysyms.Down
                    self._vertical_cursor_nav(down, False, False)
                    return True
                
                if event.keyval in (gtk.keysyms.Left, gtk.keysyms.Right):
                    pos = self._buffer.get_iter_at_mark(self._buffer.get_insert())
                    if event.keyval == gtk.keysyms.Left:
                        pos.backward_cursor_position()
                    else:
                        pos.forward_cursor_position()
                    self._cursor_move_supported = [True, True]
                    self._buffer.place_cursor(pos)
                    return True
            
            # Regular key values
            if not ctrl_on:
                
                # Preserve identation (regular newlines handled below, as printable chars)
                if self._view.get_auto_indent() and event.keyval == gtk.keysyms.Return and \
                  not shift_on:
                    self._multi_edit('indent_nl')
                    return True
                
                if event.keyval == gtk.keysyms.BackSpace:
                    self._multi_edit('delete', -1)
                    return True
                
                if event.keyval == gtk.keysyms.Delete:
                    if not shift_on:  # to be consistent with gedit
                        self._multi_edit('delete', 1)
                        return True
                
                if event.keyval == gtk.keysyms.Escape:
                    # Prevent printing the unicode Escape char
                    return False
                
                # Printable chars
                if event.string != '':
                    self._multi_edit('insert', event.string)
                    return True
                
        return False
    
    # ============================================================ Text modifiers
    
    def _single_edit(self, start, insert, value,  start_is_iter=False):
        """ Insert or delete text at the given position.
        
        Important: Multi-edit text modifications must never occur anywhere but here.
                   And only "_multi_edit" may call this function.
        
        Arguments:
            start: A mark or iter (depending on "start_is_iter")
            insert: True for insert, False for delete
            value: String for insert, length for delete (+: forward deletion, -: backward deletion)
        """
        self._change_supported = True
        if not start_is_iter:
            start = self._buffer.get_iter_at_mark(start)
        if insert:
            self._buffer.insert_interactive(start, str(value), True)
        else:
            end = start.copy()
            if value > 0:
                end.forward_cursor_positions(value)
            else:
                start.forward_cursor_positions(value)
            self._buffer.delete_interactive(start, end, True)
            self._cleanup_marks()
    
    def _multi_edit(self, mode, value=None):
        """ Make mode dependant text modifications at all multi-edit marks.
        
        "value" is mode dependant.
        
        Modes:
            insert: normal text insertion
            delete: normal (backward or forward) text deletion
            increment: incrementing text insertion (numerical or alphabetical)
            tab: emulate gedit (indent)
            shift_tab: emulate gedit (preceding indentation deletion for lines)
        """
        self._buffer.begin_user_action()
        
        if mode == 'insert':
            # value = string
            for mark in self._marks:
                self._single_edit(mark, True, value)
        
        elif mode == 'delete':
            # value = length
            for mark in self._marks:
                self._single_edit(mark, False, value)
        
        elif mode == 'increment' and len(value) != 0:
            # value = list
            i = 0
            for mark in self._marks:
                self._single_edit(mark, True, value[i])
                i += 1
                if not i < len(value):
                    i = 0
        
        elif mode == 'space_tab':
            # value = not used
            tab_width = self._view.get_tab_width()
            for mark in self._marks:
                offset = self._get_physical_line_offset(mark)
                tab_string = ' ' * (tab_width - (offset % tab_width))
                self._single_edit(mark, True, tab_string)
        
        elif mode == 'left_tab':
            # value not used
            for mark in self._marks:
                pos = self._buffer.get_iter_at_mark(mark)
                pos.set_line_offset(0)
                i = 1
                while i < 4:
                    if pos.get_char() == ' ':
                        pass
                    elif pos.get_char() == '\t':
                        break
                    else:
                        i -= 1
                        break
                    pos.forward_char()
                    i += 1
                pos.set_line_offset(0)
                self._single_edit(pos, False, i, True)
        
        elif mode == 'indent_nl':
            # value not used
            for mark in self._marks:
                i = self._buffer.get_iter_at_mark(mark)
                offset = i.get_line_offset()
                i.set_line_offset(0)
                indent_str = '\n'
                while i.get_line_offset() < offset:
                    if i.get_char() in (' ', '\t'):
                        indent_str += i.get_char()
                    else:
                        break
                    i.forward_char()
                self._single_edit(mark, True, indent_str)
        
        elif mode == 'level':
            # value not used
            lines = {}
            max_offsets = {0:0}  # {column:max_offset}
            tabs = not self._view.get_insert_spaces_instead_of_tabs()
            tab_width = self._view.get_tab_width()
            
            # Sort marks into lines
            for mark in self._marks:
                line = self._buffer.get_iter_at_mark(mark).get_line()
                new_item = [mark, self._get_physical_line_offset(mark)]
                if line not in lines:
                    lines[line] = [new_item]
                else:
                    for i, item in enumerate(lines[line]):
                        if new_item[1] <= item[1]:
                            lines[line].insert(i, new_item)
                            break
                        elif i == len(lines[line]) - 1:
                            lines[line].append(new_item)
                            break
                    if len(lines[line]) > len(max_offsets):
                        # New column detected
                        max_offsets[len(max_offsets)] = 0
            
            # Get first column's max offset
            # Note: Succeeding columns' max offsets are detected during their
            # preceding column's process
            for line in lines:
                if lines[line][0][1] > max_offsets[0]:
                    max_offsets[0] = lines[line][0][1]
            
            # Process
            for column in max_offsets:
                next_column = column + 1
                
                # Tabs
                if tabs:
                    remainder = max_offsets[column] % tab_width
                    if remainder != 0:
                        max_offsets[column] += tab_width - remainder
                    
                for line in lines:
                    if len(lines[line]) - 1 < column:
                        continue
                    dif = max_offsets[column] - lines[line][column][1]
                    if dif > 0:
                        if tabs:
                            insert = '\t' * (dif / tab_width)
                            if dif % tab_width != 0:
                                insert += '\t'
                        else:
                            insert = ' ' * dif
                        self._single_edit(lines[line][column][0], True, insert)
                        # Update succeeding offets in same line
                        for i in range(len(lines[line]) - next_column):
                            lines[line][next_column + i][1] += dif
                    # Update the succeeding max offset
                    if len(lines[line]) > next_column and \
                      lines[line][next_column][1] > max_offsets[next_column]:
                        max_offsets[next_column] = lines[line][next_column][1]
        
        self._buffer.end_user_action()
    
    def _get_physical_line_offset(self, mark):
        """ Get the physical line offset of a mark.
        
        Basically just the character offset with tab support.
        Physical, in the sense that it corresponds with a physical width (e.g. pixels),
        rather than a logical one (bytes or chars).
        """
        pos = self._buffer.get_iter_at_mark(mark)
        i = pos.copy()
        i.set_line_offset(0)
        offset = 0
        tab_width = self._view.get_tab_width()
        while not i.equal(pos):
            if i.get_char() == '\t':
                offset += tab_width - (offset % tab_width)
            else:
                offset += 1
            i.forward_char()
        return offset
    
    def _get_logical_line_offset(self, pos, phy_offset):
        """ Convert a physical line offset to a logical one. """
        # pos is simply a text iter in the line
        # (does not mark the actual offset which is phy_offset)
        pos = pos.copy()
        pos.set_line_offset(0)
        phy_i = 0
        tab_width = self._view.get_tab_width()
        phy_amount = 0
        while phy_i < phy_offset and not pos.ends_line():
            if pos.get_char() == '\t':
                phy_amount = tab_width - (phy_i % tab_width)
            else:
                phy_amount = 1
            phy_i += phy_amount
            pos.forward_char()
        # Round mid-tab offset
        if phy_i != phy_offset and phy_i - phy_offset > phy_amount / 2:
            pos.backward_char()
        return pos.get_line_offset()
    
    def _auto_increment(self, entry):
        """ Parse an auto-incr command and return the list of values. """
        
        # Number
        if entry['type'] == 'num' and len(entry['args']) == 2:
            i = float(entry['args'][0])
            result = []
            for mark in self._marks:
                str_i = str(i)
                if str_i[-2:] == '.0':
                    str_i = str_i[:-2]
                result.append(str_i)
                i += float(entry['args'][1])
            return result
        
        # Alphabet
        elif entry['type'] == 'abc' and len(entry['args']) == 1:
            start = entry['args'][0]
            if start not in ('a', 'A', 'z', 'Z'):
                return ()
            if start.islower():
                letters = list(string.ascii_lowercase)
            else:
                letters = list(string.ascii_uppercase)
            if start.lower() == 'z':
                letters.reverse()
            return letters
        
        # Custom list
        elif entry['type'] == 'list':
            return entry['args']
        
        # Invalid type
        return ()
    
    def _auto_incr_dialog(self):
        """ One-time auto-incr dialog """
        glade_file = os.path.join(os.path.dirname(__file__), 'auto_incr.glade')
        ui = gtk.glade.XML(glade_file, 'auto_incr_dialog')
        dialog = ui.get_widget('auto_incr_dialog')
        dialog.set_transient_for(self._window)
        
        type_field = ui.get_widget('type')
        type_field.set_active(0)
        args_field = ui.get_widget('arguments')
        apply_btn = ui.get_widget('apply')
        
        def apply_command(button):
            args = args_field.get_text()
            args = csv.reader([args]).next()
            incr_cmd = {
                'type': type_field.get_active_text(),
                'args': args,
            }
            self._multi_edit('increment', self._auto_increment(incr_cmd))
            dialog.destroy()
        
        apply_btn.connect('clicked', apply_command)
        args_field.connect('activate', apply_command)
    
    # ============================================================ Multi-edit Marks

    def _add_remove_mark(self, dont_remove=False):
        """ Add or remove a mark at the cursors position. """
        pos = self._buffer.get_iter_at_mark(self._buffer.get_insert())
        pos_marks = pos.get_marks()
        deleted = 0
        
        # Deselect the current selection (if there is one)
        self._cursor_move_supported = [False, True]
        self._buffer.move_mark_by_name('selection_bound', pos)
        
        for mark in pos_marks:
            # Note: Marks may be present that are not associated with multi-edit
            if mark in self._marks:
                mark.set_visible(False)
                self._buffer.delete_mark_by_name(mark.get_name())
                self._marks.remove(mark)
                deleted += 1
        
        # Check included to watch for "mark leaking"
        if deleted > 1:
            print 'Multi-edit plugin: Mark leak detected'
        
        if deleted != 0 and not dont_remove:
            return
        
        # Add the mark
        self._marks.append(self._buffer.create_mark('multi-edit' + str(self._mark_i), pos, False))
        self._marks[len(self._marks) - 1].set_visible(True)
        self._mark_i += 1
    
    def _vertical_cursor_nav(self, down, smart_nav=False, edit_marks=True):
        """ Emulate normal vertical cursor movement.
        
        Main role is to overide the default action created by shift or ctrl.
        Marks are placed by default.
        
        Smart Nav: Navigates lines based on words instead of chars,
            but also sticks to end-of-lines when met.
        """
        pos = self._buffer.get_iter_at_mark(self._buffer.get_insert())
        start_of_line = pos.starts_line()
        end_of_line = pos.ends_line()
        seperators = string.whitespace + string.punctuation.replace('_', '')
        
        # Vertical mark memory (vertical)
        if edit_marks and (self._vert_mark_mem is None or self._vert_mark_mem[1] != smart_nav):
            self._vert_mark_mem = (pos.get_line(), smart_nav)
        
        # Initial mark edit
        if edit_marks:
            if (down and self._vert_mark_mem[0] > pos.get_line()) or \
               (not down and self._vert_mark_mem[0] < pos.get_line()):
                self._add_remove_mark()
            else:
                self._add_remove_mark(True)
        
        # Line offset memory (horizontal)
        if self._line_offset_mem is None or smart_nav != self._line_offset_mem["smart_nav"]:
            if not smart_nav:
                self._line_offset_mem = {
                    "smart_nav": False,
                    "data": self._get_physical_line_offset(self._buffer.get_insert()),
                }
            else:
                # Smart nav placement calculation
                if start_of_line or end_of_line:
                    word_offset = 0
                    char_offset = 0
                    end_gravity = None
                    mid_seperators = None
                else:
                    start_iter = pos.copy()
                    start_iter.set_line_offset(0)
                    text = start_iter.get_text(pos)
                    
                    end_gravity = text[-1:] not in seperators and pos.get_char() in seperators
                    mid_seperators = text[-1:] in seperators and pos.get_char() in seperators
                    end_gravity = end_gravity or mid_seperators
                    mid_word = text[-1:] not in seperators and pos.get_char() not in seperators
                    
                    # Convert seperators to spaces (to use split())
                    words = ''
                    for i, char in enumerate(text):
                        if char in seperators:
                            words += ' '
                        else:
                            words += char
                    words = words.split()
                    word_offset = len(words)
                    
                    # Account for leading seperators
                    if text[0] in seperators and not (mid_seperators and word_offset == 0):
                        word_offset += 1
                    
                    # Account for mid word
                    if mid_word:
                        word_offset -= 1
                    
                    char_offset = 0
                    if mid_word:
                        char_offset = len(words[-1])
                    elif mid_seperators:
                        text_iter = pos.copy()
                        text_iter.backward_char()
                        while text_iter.get_char() in seperators:
                            char_offset += 1
                            if text_iter.starts_line():
                                break
                            text_iter.backward_char()
                
                # Save values
                self._line_offset_mem = {
                    "smart_nav": True,
                    "data": {
                        "word_offset": word_offset,
                        "char_offset": char_offset,
                        "end_gravity": end_gravity,
                        "mid_seperators": mid_seperators,
                        "end_of_line": end_of_line,
                    },
                }
        
        # Line change
        if down:
            pos.forward_line()
        else:
            pos.backward_line()
        
        # Handle positioning for the new line
        if smart_nav:
            data = self._line_offset_mem["data"]
            if not pos.ends_line():
                if data["end_of_line"]:
                    pos.forward_to_line_end()
                else:
                    # Word offset
                    for i in range(data["word_offset"]):
                        # Forward till end of word
                        while pos.get_char() not in seperators and not pos.ends_line():
                            pos.forward_char()
                        # Stop at the word end if end_gravity and the last word offset
                        if data["end_gravity"] and i == data["word_offset"] - 1:
                            break
                        # Forward till next word
                        while pos.get_char() in seperators and not pos.ends_line():
                            pos.forward_char()
                    # Char offset
                    for i in range(data["char_offset"]):
                        # Stop if EOL or end of seperators if mid_seperators
                        if pos.ends_line() or (data["mid_seperators"] and \
                          pos.get_char() not in seperators):
                            break
                        pos.forward_char()
        else:
            log_offset = self._get_logical_line_offset(pos, self._line_offset_mem["data"])
            if pos.get_chars_in_line() <= log_offset:
                if not pos.ends_line():
                    pos.forward_to_line_end()
            else:
                pos.set_visible_line_offset(log_offset)
        
        # Place the cursor/mark
        self._cursor_move_supported = [True, True]
        self._buffer.place_cursor(pos)
        if edit_marks:
            self._add_remove_mark(True)
        else:
            # Reset the vert_mark_mem since it will now be invalid
            self._vert_mark_mem = None
    
    def _cleanup_marks(self):
        """ Remove any duplicate marks caused by text deletion. """
        offsets = []
        for mark in self._marks[:]:
            offset = self._buffer.get_iter_at_mark(mark).get_offset()
            if offset in offsets:
                self._buffer.delete_mark(mark)
                self._marks.remove(mark)
            else:
                offsets.append(offset)
    
    def _clear_marks(self):
        """ Exit multi-edit mode by removing any marks. """
        for mark in self._marks:
            mark.set_visible(False)  # Convenient way of redrawing just that mark's area
            self._buffer.delete_mark(mark)
        self._marks = []
        self._mark_i = 0


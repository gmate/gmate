from gi.repository import Gtk, Gio, GObject, Gedit
import os


class ResultsView(Gtk.VBox):
    def __init__(self, geditwindow):
        GObject.GObject.__init__(self)

        # We have to use .geditwindow specifically here
        #(self.window won't work)
        self.window = geditwindow

        # Save the document's encoding in a variable for later use
        #(when opening new tabs)
        try:
            self.encoding = Gedit.encoding_get_current()
        except:
            self.encoding = Gedit.gedit_encoding_get_current()

        # Preferences (we'll control them with toggled checkboxes)
        self.ignore_comments = False
        self.case_sensitive = False
        self.scan_logs = False

        # We save the grep search result data in a ListStore
        # Format:  ID (COUNT)  |  FILE (without path)
        # |  LINE  |  FILE (with path)
        #    Note: We use the full-path version when opening new tabs
        #(when necessary)
        self.search_data = Gtk.ListStore(str, str, str, str)

        # Create a list (a "tree view" without children) to display the results
        self.results_list = Gtk.TreeView(self.search_data)

        # Get the selection attribute of the results_list and assign
        # a couple of properties
        tree_selection = self.results_list.get_selection()

        # Properties...
        tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        tree_selection.connect("changed", self.view_result)

        # Create the cells for our results list treeview
        #   Note:  We don't need to create a cell or text renderer
        #          for the full-path filename variable because we
        #          won't actually be displaying that information.
        cell_id = Gtk.TreeViewColumn("#")
        cell_line_number = Gtk.TreeViewColumn("Line")
        cell_filename = Gtk.TreeViewColumn("File")

        # Now add the cell objects to the results_list treeview object
        self.results_list.append_column(cell_id)
        self.results_list.append_column(cell_line_number)
        self.results_list.append_column(cell_filename)

        # Create text-rendering objects so that we can actually
        # see the data that we'll put into the objects
        text_renderer_id = Gtk.CellRendererText()
        text_renderer_filename = Gtk.CellRendererText()
        text_renderer_line_number = Gtk.CellRendererText()

        # Pack the text renderer objects into the cell objects we created
        cell_id.pack_start(text_renderer_id, True)
        cell_filename.pack_start(text_renderer_filename, True)
        cell_line_number.pack_start(text_renderer_line_number, True)

        # Now set the IDs to each of the text renderer objects and
        # set them to "text" mode
        cell_id.add_attribute(text_renderer_id, "text", 0)
        cell_filename.add_attribute(text_renderer_filename, "text", 1)
        cell_line_number.add_attribute(text_renderer_line_number, "text", 2)

        # Create a scrolling window object and add
        # our results_list treeview object to it
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.results_list)

        # Pack in the scrolled window object
        self.pack_start(scrolled_window, True, True, 0)

        # Create a "Find" button; we'll pack it into an HBox in a moment...
        button_find = Gtk.Button("Find")
        button_find.connect("clicked", self.button_press)
        # Create a "search bar" to type the search string into; we'll pack it
        # into the HBox as well...
        self.search_form = Gtk.Entry()
        self.search_form.connect("activate", self.button_press)

        # Here's the HBox I mentioned...
        search_box = Gtk.HBox(False, 0)
        search_box.pack_start(self.search_form, False, False, 0)
        search_box.pack_start(button_find, False, False, 0)

        # Pack the search box (search bar + Find button) into the side panel
        self.pack_start(search_box, False, False, 0)

        # Create a check box to decide whether or not to ignore comments
        self.check_ignore = Gtk.CheckButton("Ignore comments")
        self.check_ignore.connect("toggled", self.toggle_ignore)
        # Pack it in...
        self.pack_start(self.check_ignore, False, False, 0)

        # Create a check box to determine whether to pay attention to case
        self.check_case = Gtk.CheckButton("Case Sensitive")
        self.check_case.connect("toggled", self.toggle_case)
        # Pack it in...
        self.pack_start(self.check_case, False, False, 0)

        # Create a check box to determine whether to pay attention to case
        self.check_logs = Gtk.CheckButton("Scan log/bak files")
        self.check_logs.connect("toggled", self.toggle_logs)
        # Pack it in...
        self.pack_start(self.check_logs, False, False, 0)

        # Show all UI elements
        self.show_all()

    # A click of the "Ignore comments" check box calls to this function
    def toggle_ignore(self, widget):
        self.ignore_comments = not self.ignore_comments

    # A click of the "Case sensitive" check box calls to this function
    def toggle_case(self, widget):
        self.case_sensitive = not self.case_sensitive

    # A click of the "Scan log/bak files" check box calls to this function
    def toggle_logs(self, widget):
        self.scan_logs = not self.scan_logs

    # A call goes to view_result whenever the user clicks on
    # one of the results after a search.  In response to the
    # click, we'll go to that file's tab (or open it in a
    # new tab if they since closed that tab) and scroll to
    # the line that the result appears in.
    def view_result(self, widget):
        # Get the selection object
        tree_selection = self.results_list.get_selection()

        # Get the model and iterator for the row selected
        (model, iterator) = tree_selection.get_selected()

        if (iterator):
            # Get the absolute path of the file
            absolute_path = model.get_value(iterator, 3)

            # Get the line number
            line_number = int(model.get_value(iterator, 2)) - 1

            # Get all open tabs
            documents = self.window.get_documents()

            # Loop through the tabs until we find which one matches the file
            # If we don't find it, we'll create it in a new tab afterwards.
            for each in documents:
                doc = each.get_uri_for_display()

                if (doc.replace("file://", "") == absolute_path):
                         # This sets the active tab to "each"
                    (self.window.set_active_tab
                        (Gedit.Tab.get_from_document(each)))
                    each.goto_line(line_number)

                    # Get the bounds of the document
#                    (start, end) = each.get_bounds()

                    self.window.get_active_view().scroll_to_cursor()

                    return

            # If we got this far, then we didn't find the file open in a tab.
            # Thus, we'll want to go ahead and open it...
            self.window.create_tab_from_location(Gio.File.new_for_path(absolute_path), self.encoding, int(model.get_value(iterator, 2)), 0, False, True)

    # Clicking the "Find" button or hitting return in the search area
    # calls button_press.
    # This function, of course, searches each open document for
    # the search query and
    # displays the results in the side panel.
    def button_press(self, widget):
        # Get all open tabs
        documents = self.window.get_documents()

        # Make sure there are documents to search...
        if (len(documents) == 0):
            return  # Can't search nothing.  :P

        # Let's also make sure the user entered a search string
        if (len(self.search_form.get_text()) <= 0):
            return

        # Create a string that will hold all of the filenames;
        # we'll append it to the grep command string.
        string = ""

        fbroot = self.get_filebrowser_root()
        if fbroot != "" and fbroot is not None:
            location = fbroot.replace("file://", "")
            location = location.replace("%20", "\\ ")
        else:
            return

        #if (not)
        #" -type f -not -regex '.*/.svn.*'"
        #" -type f -not -regex '.*/(.svn|.log|.bak).*'"
        search_filter = ' -type f | egrep -v ".*(\.svn.*|\.git.*)"'
        if (not self.scan_logs):
            search_filter = ' -type f | egrep -v ".*(\.svn.*|\.git.*|\.log|\.bak)"'

        hooray = os.popen("find " + location + search_filter).readlines()
        for hip in hooray:
            string += " \"%s\"" % hip[:-1]

        # str_case_operator will hold the "case insensitive"
        # command if necessary
        str_case_operator = ""
        if (not self.case_sensitive):
            str_case_operator = " -i"

       # Create a pipe and call the grep command, then read it
        pipe = os.popen("grep -n -H" + str_case_operator + " %s %s" % (self.search_form.get_text(), string))
        data = pipe.readlines()

        results = data

        # Clear any current results from the side panel
        self.search_data.clear()

        # Process each result...
        for each in results:
            # Each result will look like this:
            #   FILE (absolute path):Line number:string
            #
            #   ... where string is the line that the search data was found in.
            pieces = each.split(":", 2)

            if (len(pieces) == 3):
                line_number = pieces[1]
                # We just want the filename, not the path
                filename = os.path.basename(pieces[0])
                string = pieces[2].lstrip(" ")  # Remove leading whitespace

                # If we want to ignore comments,
                # then we'll make sure it doesn't start with # or //
                if (self.ignore_comments):
                    if (not string.startswith("#") and
                        not string.startswith("//")):
                        self.search_data.append(("%d" % (len(self.search_data)
                         + 1), filename, line_number, pieces[0]))
                else:
                    self.search_data.append(("%d" % (len(self.search_data) +
                     1), filename, line_number, pieces[0]))

    def get_filebrowser_root(self):
        base = u'org.gnome.gedit.plugins.filebrowser'
        client = Gio.Settings.new(base)
#        client.add_dir(base, GConf.ClientPreloadType.PRELOAD_NONE)
#        path = os.path.join(base, u'virtual_root')
        val = client.get_string('virtual-root')
        if val is not None:
          #also read hidden files setting
#            base = u'org.gnome.gedit.plugins.filebrowser'
#            client = Gio.Settings.new(base)
#            client.add_dir(base, GConf.ClientPreloadType.PRELOAD_NONE)
#            path = os.path.join(base, u'filter_mode')
            try:
                fbfilter = client.get_strv('filter-mode')
            except AttributeError:
                fbfilter = "hidden"
            if 'hide-hidden' in fbfilter:
                self._show_hidden = True
            else:
                self._show_hidden = False
        return val


class PluginHelper:
    def __init__(self, plugin, window):
        self.window = window
        self.plugin = plugin

        self.ui_id = None

        self.add_panel(window)

    def deactivate(self):
        self.remove_menu_item()

        self.window = None
        self.plugin = None

#    def update_ui(self):
#        pass

    def add_panel(self, window):
        panel = self.window.get_side_panel()

        self.results_view = ResultsView(self.window)

        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_DND_MULTIPLE, Gtk.IconSize.BUTTON)
        self.ui_id = panel.add_item(self.results_view,
            "FindInDocumentsPanel", "Find in Open Documents", image)

    def remove_menu_item(self):
        panel = self.window.get_side_panel()

        panel.remove_item(self.results_view)


class FindInDocumentsPlugin(GObject.Object, Gedit.WindowActivatable):
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self.instances = {}

    def do_activate(self):
        self.instances[self.window] = PluginHelper(self, self.window)

    def do_deactivate(self):
        self.instances[self.window].deactivate()

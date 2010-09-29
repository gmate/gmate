import gtk, gedit
import gobject
import webkit
import pygtk
import os
import re
from urllib import url2pathname
from FindInProjectParser import FindInProjectParser
from FindInProjectUtil import filebrowser_root

style_str="""<style>
.match {
  color: black;
}
tbody {
  font-family: Consolas, Monospace,"Courier New", courier, monospace;
  color: #a0a0a0;
}
table {
  margin: 10px;
  width: 97%;
  table-layout: fixed;
  word-wrap: break-word;
  border-collapse: collapse;
}
.filename {
  background-color: #D2D2D2;
  font-weight: bold;
}
.highlight {
  background-color: #yellow;
}
thead td {
  padding: 6px 10px;
}
tbody tr, thead {
  cursor: hand;
}
.line-number{
  width: 43px;
  background: #D2D2D2;
  text-align:right;
  padding: 4px 6px;
}
tbody tr:nth-child(even) td:nth-child(2){
  background: #efefef;
}
</style>
<script type="text/javascript">
function goto(file, line) {
  window.location = "gedit:///" + file + "?line=" + line;
}
function toggle(dom) {
  triangle = dom.getElementsByTagName('span')[0];
  if(triangle.className == 'open') {
    dom.parentNode.tBodies[0].style.display = 'none';
    triangle.innerHTML = '&#9654;';
    triangle.className = 'close';
  } else {
    dom.parentNode.tBodies[0].style.display = '';
    triangle.innerHTML = '&#9660;';
    triangle.className = 'open';
  }
}
</script>"""

class FindInProjectBrowser(webkit.WebView):
    def __init__(self):
        webkit.WebView.__init__(self)

class FindInProjectWindow:
    protocol = re.compile(r'(?P<protocol>^gedit:\/\/)(?P<file>.*?)\?line=(?P<line>.*?)$')

    def __init__(self, gedit_window):
        self._gedit_window = gedit_window
        self._builder = gtk.Builder()
        self._builder.add_from_file(os.path.join(os.path.dirname( __file__ ), "window.glade"))
        self._window = self._builder.get_object("find-in-project")
        self._browser = FindInProjectBrowser()
        self._browser.connect("navigation-requested", self.goto_file)
        self._window.connect("delete_event", self._window.hide_on_delete)
        self._window.connect("key-release-event", self.window_key)
        self._searchbox = self._builder.get_object("searchbox")
        self._searchbox.connect("key-release-event", self.searchbox_key)
        self._searchbox.connect("icon-release", self.searchbox_clear)
        self._builder.get_object("search-button").connect("clicked", self.search)
        self._builder.get_object("placeholder").add(self._browser)
        self._history = gtk.ListStore(gobject.TYPE_STRING)
        self._completion = gtk.EntryCompletion()
        self._completion.set_model(self._history)
        self._searchbox.set_completion(self._completion)
        self._completion.set_text_column(0)

    def init(self):
        self._window.deiconify()
        self._window.show_all()
        self._searchbox.grab_focus()

    def goto_file(self, page, frame, request):
        match = self.protocol.search(request.get_uri())
        if match:
            file_uri = self._path + match.group('file')
            line_number = match.group('line')
            gedit.commands.load_uri(self._gedit_window, file_uri, gedit.encoding_get_current(), int(line_number))
            self._window.hide()
            return True

    def window_key(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self._window.hide()

    def searchbox_clear(self, widget, event, nid):
        self._searchbox.set_text('')
        self._searchbox.grab_focus()

    def searchbox_key(self, widget, event):
        if event.keyval == gtk.keysyms.Return:
            self._builder.get_object("search-button").grab_focus()
            self.search(event)

    def search(self, event):
        self._path = filebrowser_root()
        query = self._searchbox.get_text()
        self._history.set(self._history.append(), 0, query)
        html = FindInProjectParser(query, url2pathname(self._path)[7:]).html()
        self._browser.load_string(style_str + html, "text/html", "utf-8", "about:")


import gtk
import gconf
import gedit
import copy

version = "0.1"

Xpm_Data = [
  "16 16 2 1",
  "       c None",
  "X      c %s",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     ",
  "          XX     "
  ]

CONFROOT = '/apps/gedit-2/plugins/highlight_edited_lines/'

PREFS = {
  'show_line_marks': True,
  'line_marks_color': '#ff0000',
  'highlight': True,
  'highlight_bg_color': '#282828',
}

def new_pixbuf(color):
  xpm = copy.copy(Xpm_Data)
  xpm[2] = xpm[2]%color
  return gtk.gdk.pixbuf_new_from_xpm_data(xpm)
  
def colorstr_from_gdkcolor(c):
  s = c.to_string()
  return '#'+s[1:3]+s[5:7]+s[9:11]
  
class PreferencesDialog(gtk.Dialog):

  def __init__(M, window):
    gtk.Dialog.__init__(M, parent=window)
    M.view = window.get_active_view()
    M.init_dialog(window)
    
    M.conf = gconf.client_get_default()

    T = gtk.Table(2,3)
    T.set_row_spacings(3)
    T.set_col_spacings(3)
    
    # line marks
    if 1:
    
      # label
      if 1:
        T.attach(gtk.Label("Line Marks:"),0,1,0,1)
      
      # checkbox
      if 1:
        cbut = gtk.CheckButton()
        cbut.set_active(PREFS['show_line_marks'])
        cbut.show()
        cbut.connect("toggled", M.on_show_line_marks_toggled)
        T.attach(cbut,1,2,0,1)
        
      # color button
      if 1:
        M.line_marks_WDGT = gtk.ColorButton(gtk.gdk.Color(PREFS['line_marks_color']))
        M.line_marks_WDGT.set_sensitive(PREFS['show_line_marks'])
        M.line_marks_WDGT.connect("color-set",M.on_line_marks_color_set)
        T.attach(M.line_marks_WDGT,2,3,0,1)
        
    # highlight
    if 1:
      
      # label
      if 1:
        al = gtk.Alignment(1,.5,0,0)
        al.add(gtk.Label("Background:"))
        T.attach(al,0,1,1,2)
        
      # checkbox
      if 1:
        w = gtk.CheckButton()
        w.set_active(PREFS['highlight'])
        w.show()
        w.connect('toggled', M.on_highlight_bg_toggled)
        T.attach(w,1,2,1,2)
        
      # color button
      if 1:
        M.highlight_bg_WDGT = gtk.ColorButton(gtk.gdk.Color(PREFS['highlight_bg_color']))
        M.highlight_bg_WDGT.set_sensitive(PREFS['highlight'])
        M.highlight_bg_WDGT.connect('color-set',M.on_highlight_bg_color_set)
        T.attach(M.highlight_bg_WDGT,2,3,1,2)
        
    vbox = M.get_child()
    vbox.add(T)
    vbox.show_all()
  
  def on_highlight_bg_color_set(M, widget):
    color = widget.get_color()
    M.conf.set_string(CONFROOT+'highlight_bg_color',colorstr_from_gdkcolor(color))

  def on_highlight_bg_toggled(M, widget):
    flag = widget.get_active()
    M.conf.set_bool(CONFROOT+'highlight',flag)
    M.highlight_bg_WDGT.set_sensitive(flag)
    
  def on_line_marks_color_set(M, widget):
    color = widget.get_color()
    M.conf.set_string(CONFROOT+'line_marks_color',colorstr_from_gdkcolor(color))
    
  def on_show_line_marks_toggled(M,cbut):
    flag = cbut.get_active()
    M.conf.set_bool(CONFROOT+'show_line_marks',flag)
    M.line_marks_WDGT.set_sensitive(flag)
    
  def init_dialog(M, window):
    M.set_title("Highlight Edited Lines Preferences")
    M.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
    M.set_default_response(gtk.RESPONSE_CLOSE)
    M.set_has_separator(False)
    M.set_transient_for(window)
    M.set_resizable(False)
    M.set_border_width(6)
    M.set_modal(True)
    on_response = lambda M, response: M.destroy()
    M.connect("response", on_response)
    
class WinAttachedObject:
  def __init__(M, win):
    M.win            = win
    M.connected_docs = []
    M.win.connect("tab-added",M.on_win_tab_added)
    
  def getdoc(M):
    tab = M.win.get_active_tab()
    if not tab:
      return
    return tab.get_document()
    
  def getview(M): return M.win.get_active_view()
        
  def on_win_tab_added(M, win, tab):
    #print 'tab added'
    view = tab.get_view()
    # create mark
    view.set_mark_category_priority('EDITED',10)
    # line mark
    if PREFS['show_line_marks']:
      view.set_show_line_marks(True)
      view.set_mark_category_icon_from_pixbuf('EDITED',new_pixbuf(PREFS['line_marks_color']))
    if PREFS['highlight']:
      map = view.get_colormap()
      view.set_mark_category_background('EDITED',map.alloc_color(PREFS['highlight_bg_color']))
  def on_doc_loaded(M, doc, unused):
    # the initial insertion of the entire text left a spurious mark
    doc.remove_source_marks(doc.get_start_iter(),doc.get_end_iter())

  def on_doc_insert_text(M, doc, loc, text, N):
    N        = text.count('\n') + 1
    nextchar = loc.get_char()
    itr      = loc.copy()
    if text[0]=='\n' and nextchar=='\n':
      # we inserted a \n at end of line, leave that line alone
      N -= 1
    for i in range(N):
      doc.create_source_mark(None,'EDITED',itr)
      itr.backward_line()
      
  def on_doc_delete_range(M, doc, start, end):
    if not start.ends_line():
      doc.create_source_mark(None,'EDITED',start)
    else:
      doc.remove_source_marks(start, end, 'EDITED')

  def update_ui(M):
    doc = M.getdoc()
    if not doc:
      return
    if id(doc) in M.connected_docs:
      return
    
    # insert id() so that the doc is not kept alive by this list
    M.connected_docs.append(id(doc)) 
    
    doc.connect("loaded", M.on_doc_loaded)
    doc.connect_after("insert-text", M.on_doc_insert_text)
    doc.connect("delete-range", M.on_doc_delete_range)
    
  def deactivate(M):
    #print 'deactivate called'
    # ?? turn off EDITED line mark
    M.win.disconnect_by_func(M.on_win_tab_added)
    for doc in M.win.get_documents():
      if id(doc) in M.connected_docs:
        doc.disconnect_by_func(M.on_doc_loaded)
        doc.disconnect_by_func(M.on_doc_insert_text)
      doc.disconnect_by_func(M.on_doc_delete_range)
    M.connected_docs = []
    

class HighlightEditedLinesPlugin(gedit.Plugin):
  def __init__(M):
    gedit.Plugin.__init__(M)
    conf=gconf.client_get_default()
    
    M.children = {}
    
    # read in preferences. if absent, set them
    # register handler for their change
    for key,get,set in (('show_line_marks',    conf.get_bool,   conf.set_bool),
                        ('line_marks_color',   conf.get_string, conf.set_string),
                        ('highlight',          conf.get_bool,   conf.set_bool),
                        ('highlight_bg_color', conf.get_string, conf.set_string),):
      if conf.get(CONFROOT+key) is None:
        set(CONFROOT+key,PREFS[key])
      else:
        PREFS[key]=get(CONFROOT+key)
      # ?? disconnect notification somewhere
      conf.notify_add(CONFROOT+key, M.on_gconf_client_notify)
    
  def on_gconf_client_notify(M, conf, gconf_id, entry, data):
    
    key = entry.get_key().rsplit('/')[-1]
    
    if key == 'show_line_marks':
    
      PREFS['show_line_marks']=conf.get_bool(CONFROOT+key)
      if PREFS['show_line_marks']:
        pixbuf = new_pixbuf(PREFS['line_marks_color'])
      else:
        pixbuf = None
      for win in M.children.keys():
        for view in win.get_views():
          if pixbuf:
            view.set_show_line_marks(True)
          view.set_mark_category_icon_from_pixbuf('EDITED',pixbuf)
          
    elif key == 'line_marks_color':
    
      PREFS['line_marks_color']=conf.get_string(CONFROOT+key)
      # not showing line marks anyway, doesn't matter if the color changed
      if not PREFS['show_line_marks']:
        return
      for win in M.children.keys():
        for view in win.get_views():
          view.set_mark_category_icon_from_pixbuf('EDITED',new_pixbuf(PREFS['line_marks_color']))
    
    elif key == 'highlight':
    
      PREFS['highlight'] = conf.get_bool(CONFROOT+key)        
      for win in M.children:
        for view in win.get_views():   
          if PREFS['highlight']:
            map = view.get_colormap()           
            view.set_mark_category_background('EDITED',map.alloc_color(PREFS['highlight_bg_color']))
          else:
            view.set_mark_category_background('EDITED',None)
            
    elif key == 'highlight_bg_color':

      PREFS['highlight_bg_color']=conf.get_string(CONFROOT+key)
      if not PREFS['highlight']:
        return
      for win in M.children:
        for view in win.get_views():
          map = view.get_colormap()
          view.set_mark_category_background('EDITED',map.alloc_color(PREFS['highlight_bg_color']))
                  
  def activate(M, win):
    M.children[win] = WinAttachedObject(win)

  def create_configure_dialog(M):
    window = gedit.app_get_default().get_active_window()
    return PreferencesDialog(window)
        
  def deactivate(M, win):
    M.children[win].deactivate()

  def update_ui(M, win):
    # Called whenever the win has been updated (active tab changed, etc.)
    M.children[win].update_ui()
  

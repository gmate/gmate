import gconf
import pygtk, gtk, os
import util
pygtk.require('2.0')

class FuzzyOpenConfigWindow:
  def __init__(self):
    self._builder = gtk.Builder()
    self._builder.add_from_file(os.path.join(os.path.dirname( __file__ ), "config.glade"))
    self._window = self._builder.get_object('configwindow')
    self._use_git = self._builder.get_object('use-git')
    self._ignore_ext = self._builder.get_object('ignore-ext')
    self._ignore_case = self._builder.get_object('ignore-case')
    self._ignore_space = self._builder.get_object('ignore-space')
    self._ignore_ext.set_text(util.config('ignore_ext'))
    self._use_git.set_active(util.config('use_git'))
    self._ignore_case.set_active(util.config('ignore_case'))
    self._ignore_space.set_active(util.config('ignore_space'))
    self._ignore_ext.connect('key-release-event', self.on_ignore_ext)
    self._use_git.connect('toggled', self.on_use_git)
    self._ignore_case.connect('toggled', self.on_ignore_case)
    self._ignore_space.connect('toggled', self.on_ignore_space)
    self._builder.get_object('done').connect('clicked', self.on_click)
    self._window.show_all()

  def on_click(self, widget):
    self._window.emit('destroy')

  def on_ignore_ext(self, widget, event):
    util.config('ignore_ext', self._ignore_ext.get_text())

  def on_use_git(self, widget):
    util.config('use_git', self._use_git.get_active())

  def on_ignore_case(self, widget):
    util.config('ignore_case', self._ignore_case.get_active())

  def on_ignore_space(self, widget):
    util.config('ignore_space', self._ignore_space.get_active())


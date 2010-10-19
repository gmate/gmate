import gedit
from fuzzyopen import FuzzyOpenPluginInstance
from config import FuzzyOpenConfigWindow

# STANDARD PLUMMING
class FuzzyOpenPlugin( gedit.Plugin ):
  DATA_TAG = "FuzzyOpenPluginInstance"

  def __init__( self ):
    gedit.Plugin.__init__( self )

  def _get_instance( self, window ):
    return window.get_data( self.DATA_TAG )

  def _set_instance( self, window, instance ):
    window.set_data( self.DATA_TAG, instance )

  def is_configurable( self ):
    return True

  def create_configure_dialog( self ):
    return FuzzyOpenConfigWindow()._window

  def activate( self, window ):
    self._set_instance( window, FuzzyOpenPluginInstance( self, window ) )

  def deactivate( self, window ):
    self._get_instance( window ).deactivate()
    self._set_instance( window, None )

  def update_ui( self, window ):
    self._get_instance( window ).update_ui()


from gedit import Plugin

from gedit_open_files_ui import GeditOpenFilesUi
from configuration import Configuration
from filesystem_searcher import FilesystemSearcher

class GeditOpenFiles(Plugin):
    def __init__(self):
        super(GeditOpenFiles, self).__init__()

        # Get the configuration, this is global for the entire application
        self._configuration = Configuration()

    def activate(self, window):
        """
        Called when a new window is created.
        """
        window.searcher = FilesystemSearcher(self, window)

        # Setup UI for the plugin
        GeditOpenFilesUi(window)

    def deactivate(self, window):
        window.searcher.cleanup()

    @property
    def configuration(self):
        return self._configuration

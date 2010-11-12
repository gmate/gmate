import urllib

from db_wrapper import DBWrapper
from filesystem_monitor import FilesystemMonitor
from file_wrapper import FileWrapper
from logger import log


class FilesystemSearcher(object):
    """
    Public API to be used by the UI to ask for files.

    TODO: Do we want to include hidden files should ask the file browserstop
    """

    def __init__(self, plugin, window):
        """
        Window handle setting up the database and file system monitor.
        """
        # defaults
        self._root = "."

        # Setup
        self._window = window
        self._plugin = plugin
        self._message_bus = self._window.get_message_bus()

        self._db = DBWrapper()
        self._monitor = None

        self._message_bus.connect('/plugins/filebrowser', 'root_changed', self.root_changed)

    def root_changed(self, *args, **kwargs):
        root = kwargs.get('root', None)
        previous_root = self._root

        if not root:
            if len(args) == 2:
                msg = args[1]
                root = self._get_uri_from_msg(msg)
        self._root = root.replace("file://", "") # FIXME: HACK

        if not self._monitor:
            self._monitor = FilesystemMonitor(self)
        self._monitor.change_root(previous_root)

        log.debug("changing root from %s -> %s" % (previous_root, self._root))


    @property
    def current_root(self):
        """
        Returns the current root location of the window.
        """
        if self.configuration.use_filebrowser:
            return urllib.unquote(self._root)
        else:
            return urllib.unquote(self.configuration.static_root_path)

    @property
    def filebrowser_current_root(self):
        return self._get_uri_from_msg(self._message_bus.send_sync('/plugins/filebrowser', 'get_root'))

    @property
    def configuration(self):
        return self._plugin._configuration

    def add_file(self, path, file_name):
        self._db.add_file(path, file_name)

    def remove_directory(self, path):
        self._db.remove_directory(path)

    def remove_file(self, path, name):
        self._db.remove_file(path, name)

    def increment_uri_open_count(self, uri):
        self._db.increment_file_open_count(uri.replace("file://", ""))

    def clear_database(self):
        self._db.clear_database()

    def build_exclude_list(self):
        self._monitor._build_exclude_list()

    def search(self, input):
        query = self.current_root + "%" + input
        filewrappers = []
        for row in self._db.search(query):
            # FIXME: Set data in variables so you can tell what data is returned.
            filewrappers.append(FileWrapper(input, self.current_root, row[0], row[1]))
        return filewrappers

    def cleanup(self):
        if self._monitor:
            self._monitor.finish()
        self._db.close() # FIXME: Fix db clean up

    def _get_uri_from_msg(self, msg):
        if hasattr(msg, 'uri'):
            return msg.uri
        else:
            return msg.get_value('uri')


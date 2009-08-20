"""
File Monitor Contains
- FileMonitor Class
-- Keeps track of files with in a give tree

- WalkDirectoryThread
-- Thread to walk through the tree and store the file paths to a DBWrapper
"""
import os
import stat
import re
import urllib
from Logger import log
from pyinotify import WatchManager, Notifier, ThreadedNotifier, \
EventsCodes, ProcessEvent
from threading import Thread

EVENT_MASK = EventsCodes.IN_DELETE | EventsCodes.IN_CREATE | \
EventsCodes.IN_MOVED_TO | EventsCodes.IN_MOVED_FROM # watched events


class FileMonitor(object):
    """
    FileMonitor Class keeps track of all files down a tree starting at the root
    """

    def __init__(self, db_wrapper, root, config):
        self._file_count = 0
        self._db_wrapper = db_wrapper
        self._root = os.path.realpath(root)
        self._walk_thread = None
        self._config = config
        self._ignore_regexs = []
        self._set_ignore_list()

        # Add a watch to the root of the dir
        self._watch_manager = WatchManager()
        self._notifier = ThreadedNotifier(self._watch_manager,
            FileProcessEvent(self)).start()

        # initial walk
        self.add_dir(self._root)

    def _set_ignore_list(self):
        log.info("[FileMonitor] Set Regexs for Ignore List")

        ignore_res = []
        # Complie Ignore list in to a list of regexs
        for ignore in self._config.get_value("IGNORE_FILE_FILETYPES"):
            ignore = ignore.replace(".", "\.")
            ignore = ignore.replace("*", ".*")
            ignore = "^"+ignore+"$"
            log.debug("[FileMonitor] Ignore Regex = %s" % ignore)
            self._ignore_regexs.append(re.compile(ignore))

    def add_dir(self, path):
        """
        Starts a WalkDirectoryThread to add the directory
        """
        if self.validate(path):
            self._watch_manager.add_watch(path, EVENT_MASK, rec=True)
            self._walk_thread = WalkDirectoryThread(self, path,
                self._ignore_regexs)

    def add_file(self, path, name):
        if self.validate(name):
            self._db_wrapper.add_file(path, name)
            self._file_count = self._file_count + 1

    def validate(self, name):
         # Check to make sure the file not in the ignore list
        for ignore_re in self._ignore_regexs:
            if ignore_re.match(name):
                log.debug("[WalkDirectoryThread] ##### Ignored %s #####", name)
                return False
        return True

    def remove_file(self, path, name):
        self._db_wrapper.remove_file(path, name)

    def remove_dir(self, path):
        self._db_wrapper.remove_dir(path)

    def _validate_file_query_input(self, name):
        if name.find("%") > -1:
            return False
        return True

    def set_root_path(self, root):
        self._root = root

    def change_root(self, root):
        if self._root != root:
            self._root = root
            self._db_wrapper.clear_database()
            self.add_dir(self._root)

    def refresh_database(self):
        self._db_wrapper.clear_database()
        self.add_dir(self._root)

    def search_for_files(self, name):
        res_filewrappers = []
        if self._validate_file_query_input(name):
            path_name = self._root + "%" + name
            for row in self._db_wrapper.select_on_filename(path_name):
                res_filewrappers.append(FileWrapper(name, self._root,
                    row[0], row[1]))
        return res_filewrappers


class WalkDirectoryThread(Thread):
    """
    Thread that will take a DBWrapper and a root directory and add ever file
    to the database.
    """

    def __init__(self, file_monitor, root, ignore_regexs):
        log.debug("[FileMonitor] WalkDirectoryThread Root: %s" % root)
        Thread.__init__(self)
        self._file_monitor = file_monitor
        self._root = root
        self._ignore_regexs = ignore_regexs
        self.start()

    def run(self):
        """
        Runs the Thread
        """
        if os.path.isdir(self._root):
            for (path, names) in self._walk_file_system(self._root):
                log.debug("[WalkDirectoryThread] Path: %s" % path)
                log.debug("[WalkDirectoryThread] Names: %s" % names)
                for name in names:
                    # Check to see if it is a dir
                    if not os.path.isdir(os.path.join(path, name)):
                        self._file_monitor.add_file(path, name)
        print "***** Total files %s *****" % (self._file_monitor._file_count, )

    def _walk_file_system(self, root):
        """
        From a give root of a tree this method will walk through ever branch
        and return a generator.
        """
        names = os.listdir(root)
        for name in names:
            try:
                file_stat = os.lstat(os.path.join(root, name))
            except os.error:
                continue

            if stat.S_ISDIR(file_stat.st_mode):
                # Check to make sure the file not in the ignore list
                ignore = False
                for ignore_re in self._ignore_regexs:
                    if ignore_re.match(name):
                        log.debug("[WalkDirectoryThread] ### Ignored %s ####",
                            name)
                        ignore = True
                        break
                if ignore:
                    continue
                for (newroot, children) in self._walk_file_system(
                    os.path.join(root, name)):
                    yield newroot, children
        yield root, names


class FileProcessEvent(ProcessEvent):

    def __init__(self, file_monitor):
        self._file_monitor = file_monitor

    def process_IN_CREATE(self, event):
        path = os.path.join(event.path, event.name)
        if event.is_dir:
            log.info("[FileProcessEvent] CREATED DIRECTORY: " + path)
            self._file_monitor.add_dir(path)
        else:
            log.info("[FileProcessEvent] CREATED FILE: " + path)
            self._file_monitor.add_file(event.path, event.name)

    def process_IN_DELETE(self, event):
        path = os.path.join(event.path, event.name)
        if event.is_dir:
            log.info("[FileProcessEvent] DELETED DIRECTORY: " + path)
            self._file_monitor.remove_dir(path)
        else:
            log.info("[FileProcessEvent] DELETED FILE: " + path)
            self._file_monitor.remove_file(event.path, event.name)

    def process_IN_MOVED_FROM(self, event):
        path = os.path.join(event.path, event.name)
        log.info("[FileProcessEvent] MOVED_FROM: " + path)
        self.process_IN_DELETE(event)

    def process_IN_MOVED_TO(self, event):
        path = os.path.join(event.path, event.name)
        log.info("[FileProcessEvent] MOVED_TO: " + path)
        self.process_IN_CREATE(event)


class FileWrapper(object):

    def __init__(self, query_input, root, name, path):
        self._path = path
        self._name = name
        self._query_input = query_input
        self._root = root

    def _get_path(self):
        return self._path
    path = property(_get_path)

    def _get_uri(self):
        uri = "file://" + urllib.quote(self._path)
        return uri
    uri = property(_get_uri)

    def _get_display_path(self):
        return self.highlight_pattern(self.path)
    display_path = property(_get_display_path)

    def highlight_pattern(self, path):
        path = path.replace(self._root + "/", "") # Relative path
        log.debug("[FileWrapper] path = " + path)
        query_list = self._query_input.lower().split(" ")

        last_postion = 0
        for word in query_list:
            location = path.lower().find(word, last_postion)
            log.debug("[FileWrapper] Found Postion = " + str(location))
            if location > -1:
                last_postion = (location + len(word) + 3)
                a_path = list(path)
                a_path.insert(location, "<b>")
                a_path.insert(location + len(word) + 1, "</b>")
                path = "".join(a_path)

        log.debug("[FileWrapper] Markup Path = " + path)
        return path

if __name__ == '__main__':
    from DBWrapper import DBWrapper
    db = DBWrapper()
    file_mon = FileMonitor(db, ".")

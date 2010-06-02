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
from logger import log
from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent
from threading import Thread
from threadpool import ThreadPool

THREAD_POOL_WORKS = 4

try:
    # Supports < pyinotify 0.8.6
    EVENT_MASK = EventsCodes.IN_DELETE | EventsCodes.IN_CREATE | EventsCodes.IN_MOVED_TO | EventsCodes.IN_MOVED_FROM # watched events
except AttributeError:
    # Support for pyinotify 0.8.6
    from pyinotify import IN_DELETE, IN_CREATE, IN_MOVED_FROM, IN_MOVED_TO
    EVENT_MASK = IN_DELETE | IN_CREATE | IN_MOVED_TO | IN_MOVED_FROM


class FileProcessEvent(ProcessEvent):

    def __init__(self, file_monitor):
        self._file_monitor = file_monitor

    def is_dir(self, event):
        if hasattr(event, "dir"):
            return event.dir
        else:
            return event.is_dir

    def process_IN_CREATE(self, event):
        path = os.path.join(event.path, event.name)

        if self.is_dir(event):
            log.info("[FileProcessEvent] CREATED DIRECTORY: " + path)
            self._file_monitor.add_directory(path)
        else:
            log.info("[FileProcessEvent] CREATED FILE: " + path)
            self._file_monitor.add_file(event.path, event.name)

    def process_IN_DELETE(self, event):
        path = os.path.join(event.path, event.name)
        if self.is_dir(event):
            log.info("[FileProcessEvent] DELETED DIRECTORY: " + path)
            self._file_monitor.remove_directory(path)
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


class FilesystemMonitor(object):
    """
    FileMonitor Class keeps track of all files down a tree starting at the root
    """

    def __init__(self, searcher):
        self.searcher = searcher

        self._thread_pool = ThreadPool(THREAD_POOL_WORKS)

        # Add a watch to the root of the dir
        self.watch_manager = WatchManager()
        self.notifier = ThreadedNotifier(self.watch_manager, FileProcessEvent(self))
        self.notifier.start()

        self._build_exclude_list()


    def _build_exclude_list(self):
        log.info("[FileMonitor] Set Regexs for Ignore List")

        self._exclude_regexs = []
        # Complie Ignore list in to a list of regexs
        for ignore in self.searcher.configuration.exclude_list:
            ignore = ignore.strip()
            ignore = ignore.replace(".", "\.")
            ignore = ignore.replace("*", ".*")
            ignore = "^"+ignore+"$"
            log.debug("[FileMonitor] Ignore Regex = %s" % ignore)
            self._exclude_regexs.append(re.compile(ignore))

    def change_root(self, previous_root):
        self._thread_pool.clearTasks()

        wd = self.watch_manager.get_wd(previous_root)
        if wd:
          self.watch_manager.rm_watch(wd, rec=True)

        self.searcher.clear_database()
        self.add_directory(self.searcher.current_root)

    def add_directory(self, path):
        """
        Starts a WalkDirectoryThread to add the directory
        """
        basename = os.path.basename(path)
        if self.validate(basename):
            self.watch_manager.add_watch(path, EVENT_MASK)
            self._thread_pool.queueTask(self.walk_directory, path)

    def add_file(self, path, name):
        """
        Add a single file to the databse
        """
        if self.validate(name):
            self.searcher.add_file(path, name)

    def remove_file(self, path, name):
        self.searcher.remove_file(path, name)

    def remove_directory(self, path):
        self.searcher.remove_directory(path)

    def walk_directory(self, root):
        """
        From a give root of a tree this method will walk through ever branch
        and return a generator.
        """
        if os.path.isdir(root):
            names = os.listdir(root)
            for name in names:
                try:
                    file_stat = os.lstat(os.path.join(root, name))
                except os.error:
                    continue

                if stat.S_ISDIR(file_stat.st_mode):
                    self.add_directory(os.path.join(root, name))
                else:
                    if not stat.S_ISLNK(file_stat.st_mode):
                        self.add_file(root, name)
    def finish(self):
        wd = self.watch_manager.get_wd(self.searcher.current_root)
        self.watch_manager.rm_watch(wd, rec=True)
        self.notifier.stop()
        self._thread_pool.joinAll(waitForTasks=False)

    def validate(self, name):
         # Check to make sure the file not in the ignore list
        for ignore_re in self._exclude_regexs:
            if ignore_re.match(name):
                log.debug("[WalkDirectoryThread] ##### Ignored %s #####", name)
                return False
        log.debug("[WalkDirectoryThread] # Passed %s", name)
        return True


"""
Provides the DBWrapper Class which currently wraps sqlite in order to provide
some abstractions an multithreading support.
"""
import os
import sqlite3
from logger import log
from threading import Thread
from Queue import Queue

# Register string handler
def adapt_str(s):
    return s.decode("iso-8859-1")

sqlite3.register_adapter(str, adapt_str)

class DBWrapper(Thread):
    """
    Class to wrap the python sqlite3 module to support multithreading
    """

    def __init__(self):
        # Create Database and a queue
        Thread.__init__(self)
        self._queue = Queue()
        self.start()

    def run(self):
        self._create_db()
        while True:
            try:
                sql, params, result = self._queue.get()
                if sql == '__CLOSE__':
                    self._db.close()
                    break
                log.info("[DBWrapper] QUERY: %s" % sql)
                log.info("[DBWrapper] PARAMS: %s" % str(params))
                log.info("[DBWrapper] RESULT: " + str(result))
                cursor = self._db.cursor()
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
            except sqlite3.OperationalError, e:
                log.error("[DBWrapper] OperationalError : %s" % e)

            if result:
                log.info("[DBWrapper] Putting Results")
                for row in cursor.fetchall():
                    result.put(row)
                result.put("__END__")

            self._db.commit()

    def execute(self, sql, params=None, result=None):
        self._queue.put((sql, params, result))

    def select(self, sql, params=None):
        list_result = []
        result = Queue()
        self.execute(sql, params, result=result)

        while True:
            row = result.get()
            if row == '__END__':
                break
            list_result.append(row)
        log.info("[DBWrapper] SELECT RESULT COUNT: " + str(len(list_result)))
        return list_result

    def search(self, input):
        log.info("[DBWrapper] select_on_filename method")
        params = input.replace(" ", "%")+"%"
        result = self.select("SELECT DISTINCT name, path FROM files " +
            "WHERE path LIKE ? ORDER BY open_count DESC, path ASC LIMIT 20", (params, ))
        return result

    def add_file(self, path, name):
        path = os.path.join(path, name)
        log.debug("[DBWrapper] Adding File: " + path)
        self.execute("INSERT INTO files (name, path) VALUES (?, ?)",
            (name, path))

    def remove_file(self, path, name):
        path = os.path.join(path, name)
        log.debug("[DBWrapper] Removing File: " + path)
        self.execute("DELETE FROM files where path = ?", (path, ))

    def remove_directory(self, path):
        log.debug("[DBWrapper] Remove Directory: " + path)
        self.execute("DELETE FROM files WHERE path like ?", (path+"%", ))

    def increment_file_open_count(self, path):
        log.debug("[DBWrapper] increment_file_open_count: " + path)
        self.execute("UPDATE files SET open_count =(open_count + 1) WHERE path = ?", (path, ))

    def close(self):
        self._queue.put(("__CLOSE__", "__CLOSE__", "__CLOSE__"))

    def clear_database(self):
        log.debug("[DBWrapper] Clearing Databases")
        self.execute("DELETE FROM files")

    @property
    def count(self):
        res = self.select("SELECT COUNT(*) FROM files")
        return res[0][0]

    def _create_db(self):
        self._db = sqlite3.connect(":memory:")
        self.execute("CREATE TABLE files ( id AUTO_INCREMENT PRIMARY KEY, " +
            "path VARCHAR(255), name VARCHAR(255), " +
            "open_count INTEGER DEFAULT 0)")



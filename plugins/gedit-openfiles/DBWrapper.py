"""
Provides the DBWrapper Class which currently wraps sqlite in order to provide
some abstractions an multithreading support.
"""
import os
import sqlite3
from Logger import log
from threading import Thread
from Queue import Queue


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
            if not self._queue.empty():
                try:
                    sql, params, result = self._queue.get()
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

    def select_on_filename(self, query_input):
        log.info("[DBWrapper] select_on_filename method")
        query_param = query_input.replace(" ", "%")+"%"
        res = self.select("SELECT DISTINCT name, path FROM files " +
            "WHERE path LIKE ? ORDER BY path LIMIT 51", (query_param, ))
        for row in res:
            yield row

    def close(self):
        self._queue.put("__CLOSE__")

    def _create_db(self):
        self._db = sqlite3.connect(":memory:")
        self.execute("CREATE TABLE files ( id AUTO_INCREMENT PRIMARY KEY, " +
            "path VARCHAR(255), name VARCHAR(255), " +
            "open_count INTEGER DEFAULT 0)")

    def add_file(self, path, name):
        path = os.path.join(path, name)
        log.debug("[DBWrapper] Adding File: " + path)
        self.execute("INSERT INTO files (name, path) VALUES (?, ?)",
            (name, path))

    def remove_file(self, path, name):
        path = os.path.join(path, name)
        log.debug("[DBWrapper] Removing File: " + path)
        self.execute("DELETE FROM files where path = ?", (path, ))

    def remove_dir(self, path):
        log.debug("[DBWrapper] Remove Dir: " + path)
        self.execute("DELETE FROM files WHERE path like ?", (path+"%", ))

    def clear_database(self):
        log.debug("[DBWrapper] Clearing Databases")
        self.execute("DELETE FROM files")

    def file_count(self):
        res = self.select("SELECT COUNT(*) FROM files")
        return res[0][0]

if __name__ == '__main__':
    db = DBWrapper()
    db.execute("INSERT INTO files (path, name) VALUES (?, ?)",
         ("vbabiy", "/home/vbabiy"))
    print (db.select("SELECT * FROM files"))

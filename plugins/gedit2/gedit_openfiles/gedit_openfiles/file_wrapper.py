import urllib

from logger import log


class FileWrapper(object):
    """
    A file wrapper.
    """
    def __init__(self, query_input, root, name, path):
        self._path = path
        self._name = name
        self._query_input = query_input
        self._root = root

    @property
    def path(self):
        return self._path

    @property
    def uri(self):
        uri = "file://" + urllib.quote(self._path)
        return uri

    @property
    def display_path(self):
        return self.highlight_pattern(self.path)

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

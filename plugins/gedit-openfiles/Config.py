from Logger import log
import os
import gconf
import urllib


class Config(object):

    def __init__(self):
        self._config = {}
        self._file_path = os.path.join(os.path.dirname(__file__), 'config',
            'config.ini')

        # Read Files
        self._read_file()

    def get_value(self, key):
        if key in self._config:
            log.debug("[Config] Getting Value for %s" % key)
            value = self._config[key]
            if value == "True":
                return True
            elif value == "False":
                return False
            return value
        else:
            return None

    def set_value(self, key, value):
        self._config[key] = value
        self._write_file()

    def _write_file(self):
        f = file(self._file_path, "wb")
        config_list = [("%s=%s\n" % (key, value)) for key,
            value in self._config.iteritems()]
        f.writelines(config_list)
        f.close()

    def _read_file(self):
        f = file(self._file_path, "rb")
        file_list = f.readlines()
        f.close()
        self._config = {} # reset config
        for line in file_list:
            line = line.strip()
            if len(line) > 0:
                name, value = line.split("=")

                value = value.strip()

                value = value.replace("[", "")
                value = value.replace("]", "")
                value = value.replace("'", "")

                if value.find(",") > -1:
                    self.set_value(name, [v.strip() for v in value.split(',')])
                else:
                    self.set_value(name, value)
        log.info("[Config] Config Map = %s", self._config)

    def root_path(self):
        root = "."
        if self.get_value("USE_FILEBROWSER"):
            root = self._get_root_from_filebrowser()
        else:
            root = self.get_value("ROOT_PATH")
        log.debug("[Config] ROOT: %s" % root)
        return urllib.unquote(root)

    def _get_root_from_filebrowser(self):
        base = u'/apps/gedit-2/plugins/filebrowser/on_load'
        client = gconf.client_get_default()
        client.add_dir(base, gconf.CLIENT_PRELOAD_NONE)
        path = os.path.join(base, u'virtual_root')
        val = client.get(path)
        if val is not None:
            #also read hidden files setting
            base = u'/apps/gedit-2/plugins/filebrowser'
            client = gconf.client_get_default()
            client.add_dir(base, gconf.CLIENT_PRELOAD_NONE)
            path = os.path.join(base, u'filter_mode')
            try:
                fbfilter = client.get(path).get_string()
            except AttributeError:
                fbfilter = "hidden"
            if fbfilter.find("hidden") == -1:
                self._show_hidden = True
            else:
                self._show_hidden = False

            #strip file://
            root = val.get_string().replace("file://", "")
            return root

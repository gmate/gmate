"""
    Utility functions for find in project
"""

import gconf
import os

def filebrowser_root():
    base = u'/apps/gedit-2/plugins/filebrowser/on_load'
    client = gconf.client_get_default()
    client.add_dir(base, gconf.CLIENT_PRELOAD_NONE)
    path = os.path.join(base, u'virtual_root')
    val = client.get(path)
    if val is not None:
        return val.get_string()


#!/usr/bin/env python
# This program is part of GMATE package
# Gmate script
# Author: Alexandre da Silva
# This scripts whants to allow users to use the gmate command (instead of gedit)
# command from a terminal and pass a directory as the first param.
# passign the directory as a parameter, gedit will open with filebrowser root
# directory pointing that
import gconf
import sys
import urllib
import os
#from optparse import OptionParser

# GConf directory for filebrowser
base = '/apps/gedit-2/plugins/filebrowser/on_load'
config = gconf.client_get_default()
config.add_dir(base, gconf.CLIENT_PRELOAD_NONE)

# Get the last option as file
path = os.path.abspath(sys.argv[-1:][0])

if len(sys.argv) > 1:
    parameters = ' '.join(sys.argv[1:-1])
    if os.path.isdir(path):
        url = "file://%s" % urllib.quote(path)
        config.set_string(os.path.join(base,'virtual_root'), url)
    else:
        parameters += ' "%s"' % path
    os.system('nohup gedit ' + parameters + ' > /dev/null 2>&1 &')
else:
    os.system('nohup gedit > /dev/null 2>&1 &')


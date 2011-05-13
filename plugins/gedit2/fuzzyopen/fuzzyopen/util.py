"""
    Utility functions
"""

from datetime import datetime
import gconf
import os

def config(name, value=None):
  base = lambda x: u'/apps/gedit-2/plugins/fuzzyopen/%s' % x
  client = gconf.client_get_default()
  key = ['use_git', 'ignore_case', 'ignore_space', 'ignore_ext']
  lambda_set = [client.set_bool, client.set_bool, client.set_bool, client.set_string]
  lambda_get = [client.get_bool, client.get_bool, client.get_bool, client.get_string]
  default = [True, True, True, "jpg,jpeg,gif,png,tif,psd,pyc"]

  val = client.get(base(name))
  index = key.index(name)
  if value != None:
    lambda_set[index](base(name), value)
  if val == None:
    lambda_set[index](base(name), default[index])
  return lambda_get[index](base(name))

# EDDT integration
def eddt_root():
  base = u'/apps/gedit-2/plugins/eddt'
  client = gconf.client_get_default()
  client.add_dir(base, gconf.CLIENT_PRELOAD_NONE)
  path = os.path.join(base, u'repository')
  val = client.get(path)
  if val is not None:
    return val.get_string()

# FILEBROWSER integration
def filebrowser_root():
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
    return (val.get_string(), (fbfilter.find("hidden") == -1))

def debug(string):
    #print "[DEBUG]: " + string
    pass

# from http://odondo.wordpress.com/2007/07/05/python-relative-datetime-formatting/
def relative_time(date, now = None):
  if not now:
    now = datetime.now()
  date = datetime.fromtimestamp(date)
  diff = date.date() - now.date()
  if diff.days == 0:                                        # Today
    return 'at ' + date.strftime("%I:%M %p")                ## at 05:45 PM
  elif diff.days == 1:                                      # Yesterday
    return 'at ' + date.strftime("%I:%M %p") + ' Yesterday' ## at 05:45 PM Yesterday
  elif diff.days == 1:                                      # Tomorrow
    return 'at ' + date.strftime("%I:%M %p") + ' Tomorrow'  ## at 05:45 PM Tomorrow
  elif diff.days < 7:                                       # Within one week back
    return 'at ' + date.strftime("%I:%M %p %A")             ## at 05:45 PM Tuesday
  else:
    return 'on ' + date.strftime("%b, %d, %Y")              ## on Jan, 3, 2010


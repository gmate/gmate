# -*- coding: utf-8 -*-

import os
import gconf

class Option(object):

    def __init__(self, key, default_value=None):
        self.key = key
        self.default_value = default_value

    def __get__(self, instance, owner=None):
        key = os.path.join(instance.gconfDir, self.key)
        value = instance.client.get(key)
        if value is None and self.default_value is not None:
            self.__set__(instance, self.default_value)
            return self.default_value

        return value

    def __set__(self, instance, value):
        key = os.path.join(instance.gconfDir, self.key)
        instance.client.set(key, value)

    def __delete__(self, instance):
        instance.client.unset(self.key)

class SimpleOption(Option):
    def __get__(self, instance, owner=None):
        gconf_value = super(SimpleOption, self).__get__(instance, owner)
        if gconf_value is None:
            return None
        return self.getter(gconf_value)

    def __set__(self, instance, value):
        gconf_value = gconf.Value(gconf.VALUE_STRING)
        self.setter(gconf_value, value)
        super(SimpleOption, self).__set__(instance, gconf_value)

class StringOption(SimpleOption):
    getter = lambda self, o: gconf.Value.get_string(o)
    setter = lambda self, o, v: gconf.Value.set_string(o, v)

class Options(object):
    def __init__(self, gconfDir):
        self.gconfDir = gconfDir
        self.client = gconf.client_get_default()
        # create gconf directory if not set yet
        if not self.client.dir_exists(self.gconfDir):
            self.client.add_dir(self.gconfDir, gconf.CLIENT_PRELOAD_NONE)


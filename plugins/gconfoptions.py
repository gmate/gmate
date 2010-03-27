# -*- coding: utf-8 -*-
"""
  Simple interface to access gconf options.
  Usage:

  class KeyOptions(Options):
    key_to_right = StringOption('Tab')
    key_to_left = StringOption('ISO_Left_Tab')
    key_to_1 = StringOption()
  ...
    options = KeyOptions("/apps/gedit-2/plugins/tabswitch")
    print options.key_to_right

"""
import os
import gconf

GCONF_TYPES = (
    gconf.VALUE_STRING,
    gconf.VALUE_INT,
    gconf.VALUE_BOOL,
    gconf.VALUE_LIST,
    gconf.VALUE_FLOAT,
    gconf.VALUE_SCHEMA
)

class OptionsType(type):
    """
       Metaclass for options class.
       Add capability for get all options list.
    """
    def __new__(cls, base, name, attrs):
        attrs['options'] = {}
        for key, attr in attrs.iteritems():
            if isinstance(attr, Option):
                attrs['options'][key] = attr
                attr.default_key = key
        new_class = super(OptionsType, cls).__new__(cls, base, name, attrs)
        return new_class


class Option(object):
    """
    Base class for option. Here mostly nothing known about gconf.
    """
    def __init__(self, default_value=None, **kwargs):
        self.key = kwargs.get('key', None)
        self.default_value = default_value

    def get_key(self, path):
        if self.key is None:
            self.key = self.default_key
        if not hasattr(self, '_full_key'):
            self._full_key = os.path.join(path, self.key)
        return self._full_key

    def __get__(self, instance, owner=None):
        if instance is None:
            raise ValueError("Can't access to field without instance")
        key = self.get_key(instance.gconfDir)
        value = instance.client.get(key)
        if value is None and self.default_value is not None:
            self.__set__(instance, self.default_value)
            return self.default_value

        return value

    def __set__(self, instance, value):
        key = self.get_key(instance.gconfDir)
        instance.client.set(key, value)

    def __delete__(self, instance):
        instance.client.unset(self.get_key(instance.gconfDir))


class SimpleOption(Option):
    """
            Base class for all types in gconf.
    """
    gconf_type = gconf.VALUE_INVALID

    def __init__(self, *args, **kwargs):
        self.getter = getattr(gconf.Value, 'get_%s' % self.gconf_type.value_nick)
        self.setter = getattr(gconf.Value, 'set_%s' % self.gconf_type.value_nick)
        super(SimpleOption, self).__init__(*args, **kwargs)

    def __get__(self, instance, owner=None):
        gconf_value = super(SimpleOption, self).__get__(instance, owner)
        if gconf_value is None:
            return None
        return self.getter(gconf_value)

    def __set__(self, instance, value):
        gconf_value = gconf.Value(self.gconf_type)
        self.setter(gconf_value, value)
        super(SimpleOption, self).__set__(instance, gconf_value)

# Autogenerate classes StringOption, IntOption etc. with SimpleOption
# same as:
# class StringOption(SimpleOption):
#        gconf_type = gconf.VALUE_STRING
#
for gconf_type in GCONF_TYPES:
    class_name = '%sOption' % gconf_type.value_nick.capitalize()
    new_class = type(class_name, (SimpleOption,), {'gconf_type': gconf_type})
    globals()[class_name] = new_class


class Options(object):

    __metaclass__ = OptionsType

    def __init__(self, gconfDir):
        self.gconfDir = gconfDir
        self.client = gconf.client_get_default()
        # create gconf directory if not set yet
        if not self.client.dir_exists(self.gconfDir):
            self.client.add_dir(self.gconfDir, gconf.CLIENT_PRELOAD_NONE)


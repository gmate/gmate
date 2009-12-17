# -*- coding: utf-8 -*-

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

    def __new__(cls, base, name, attrs):
        attrs['options'] = {}
        for key, attr in attrs.iteritems():
            if isinstance(attr, Option):
                attrs['options'][key] = attr
        new_class = super(OptionsType, cls).__new__(cls, base, name, attrs)
        return new_class

class Option(object):

    def __init__(self, key, default_value=None):
        self.key = key
        self.default_value = default_value

    def __get__(self, instance, owner=None):
        if instance is None:
            raise ValueError("Can't access to field without instance")
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
        instance.client.unset(os.path.join(instance.gconfDir, self.key))

class SimpleOption(Option):

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
#     gconf_type = gconf.VALUE_STRING
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


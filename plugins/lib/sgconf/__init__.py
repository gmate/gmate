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

class OptionsContainerType(type):
    """
       Metaclass for any options container class.
    """
    def __new__(cls, base, name, attrs):
        attrs['options'] = {}
        for key, attr in attrs.iteritems():
            if isinstance(attr, Option):
                attrs['options'][key] = attr
                attr.default_key = key
                attr._storage_client = '_storage' in attrs and attrs['_storage'] or Options._storage
                attr._base_uri = attrs['_uri']

        new_class = super(OptionsContainerType, cls).__new__(cls, base, name, attrs)
        return new_class


class Option(object):
    """
    Base class for option. Here mostly nothing known about gconf.
    """

    def __init__(self, default_value=None, **kwargs):
        self.key = kwargs.get('key', None)
        self.default_value = default_value

    def get_key(self, path):
        if not hasattr(self, '_full_key'):
            if self.key is None:
                self.key = self.default_key
            self._full_key = os.path.join(path, self.key)
        return self._full_key

    def __get__(self, instance, owner=None):
        key = self.get_key(self._base_uri)
        value = self._storage_client.get(key)
        if value is None and self.default_value is not None:
            self.__set__(instance, self.default_value)
            return Option.__get__(self, instance, owner)

        return value

    def __set__(self, instance, value):
        key = self.get_key(self._base_uri)
        self._storage_client.set(key, value)

    def __delete__(self, instance):
        self._storage_client.unset(self.get_key(self._base_uri))


class SimpleOption(Option):
    """
        Base class for all types in gconf.
        Define setters and getters only
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
    locals()[class_name] = new_class


class ListOption(SimpleOption):
    gconf_type = gconf.VALUE_LIST

    def _py_to_gconf(self, t):
        return {
            int: gconf.VALUE_INT,
            float: gconf.VALUE_FLOAT,
            str: gconf.VALUE_STRING,
            unicode: gconf.VALUE_STRING,
            bool: gconf.VALUE_BOOL
        }[type(t)]

    def __init__(self, default_value=None, **kwargs):
        if default_value is not None:
            assert hasattr(default_value, '__iter__'), 'Default value of ListOption must be iterable'
            if len(default_value):
                self.list_type = self._py_to_gconf(default_value[0])

        if not hasattr(self, 'list_type'):
            assert 'list_type' in kwargs, 'You must specify list_type'
            self.list_type = kwargs.get('list_type')
        self.child_setter = getattr(gconf.Value, 'set_%s' % self.list_type.value_nick)
        self.child_getter = getattr(gconf.Value, 'get_%s' % self.list_type.value_nick)
        super(ListOption, self).__init__(default_value, **kwargs)

    def __get__(self, instance, owner=None):
        v = super(ListOption, self).__get__(instance, owner)
        if v is not None:
            return map(self.child_getter, v)
        else:
            return []

    def __set__(self, instance, value):
        assert hasattr(value, '__iter__'), 'value of ListOption must be iterable'
        gvalues = [gconf.Value(self.list_type) for i in range(len(value))]
        for g, v in map(None, gvalues, value):
            getattr(g, 'set_%s' % self.list_type.value_nick)(v)
        gconf_value = gconf.Value(self.gconf_type)
        gconf_value.set_list_type(self.list_type)
        self.setter(gconf_value, gvalues)
        Option.__set__(self, instance, gconf_value)



class Options(object):
    __metaclass__ = OptionsContainerType

    _storage = gconf.client_get_default()

    def __init__(self):
        # create gconf directory if not set yet
        if not self._storage.dir_exists(self._uri):
            self._storage.add_dir(self._uri, gconf.CLIENT_PRELOAD_NONE)


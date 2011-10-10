# -*- coding: utf8 -*-
#  Click_Config plugin for Gedit
#
#  Copyright (C) 2010 Derek Veit
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module provides functions for writing and reading Python dictionaries as
text files, formatted for readability.

Usage:
from dictfile import write_dict_to_file, read_dict_from_file
dictionary = {...}
filename = '/path/to/new/file'
write_dict_to_file(dictionary, filename)
dictionary = read_dict_from_file(filename)

"""

def write_dict_to_file(dictionary, filename):
    """Write a dictionary to a text file."""
    file_handle = open(filename, 'w')
    dict_string = format_dict(dictionary)
    file_handle.writelines(dict_string)
    file_handle.close()

def format_dict(dictionary, level=0):
    """Format a dictionary as a readable multiline string."""
    brace_indent = '    ' * level
    level += 1
    item_indent = '    ' * level
    string = '{\n'
    for key in sorted(dictionary.keys()):
        value = dictionary[key]
        string += item_indent + repr(key) + ': ' + format_value(value, level)
    string += brace_indent + '}'
    return string

def format_list(list_, level=0):
    """Format a list as a readable multiline string."""
    brace_indent = '    ' * level
    level += 1
    item_indent = '    ' * level
    string = '[\n'
    for value in list_:
        string += item_indent + format_value(value, level)
    string += brace_indent + ']'
    return string

def format_value(value, level):
    """Format a value for readability as dict, list, or other type."""
    if isinstance(value, dict):
        string = format_dict(value, level)
    elif isinstance(value, list):
        string = format_list(value, level)
    else:
        string = repr(value)
    return string + ',\n'

def read_dict_from_file(filename):
    """Read a text file as a dictionary."""
    file_handle = open(filename, 'r')
    dict_string = file_handle.read().strip()
    file_handle.close()
    if dict_string.startswith('{') and dict_string.endswith('}'):
        dictionary = eval(dict_string)
    else:
        raise TypeError(
            'File does not contain a Python dictionary representation.')
        dictionary = None
    return dictionary


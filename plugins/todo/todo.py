# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 - Alexandre da Silva
#
# Inspired in Nando Vieira's todo.rb source code
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

import os, sys, operator
from stat import *
from string import Template
import re

# Get the command line argument to define the root folder on search for
root = sys.argv[1]

home_folder = os.path.expanduser('~')

temp_file_name = '/tmp/_todo_%s_todo.html' %  os.environ['USER']

# TODO: Look first for a config file present in /etc to facility configuration
# Config FileName
config_file = os.path.join(os.path.dirname(__file__), "todo.conf")

# Configs read regular expression
cfg_rx = re.compile(r"(ALLOWED_EXTENSIONS|SKIPED_DIRS|KNOWN_MARKS|SKIPED_FILES|SHOW_EMPTY_MARKS|REQUIRE_COLON|MARK_COLORS)=+(.*?)$")

# Get Configuration Info
cfg_file = open(config_file,'r')
cfg_data = cfg_file.read().split('\n')

configs = {'ALLOWED_EXTENSIONS':'','SKIPED_DIRS':'','KNOWN_MARKS':'',\
        'SKIPED_FILES':'','SHOW_EMPTY_MARKS':'0','REQUIRE_COLON':'1','MARK_COLORS': ''}

for cfg_line in cfg_data:
    cfg_match = cfg_rx.search(cfg_line)
    if cfg_match:
        configs[cfg_match.group(1)] = cfg_match.group(2)

def make_regex(config_str):
    return "|".join([re.escape(k) for k in configs[config_str].split(';')])

allowed_extensions_regex = make_regex('ALLOWED_EXTENSIONS')
skiped_dirs_regex = make_regex('SKIPED_DIRS')
known_marks_regex = make_regex('KNOWN_MARKS')
skiped_files_regex = make_regex('SKIPED_FILES')

known_marks_list = known_marks_regex.split('|')

# Initial Setup
allowed_types = re.compile(r'.*\.\b(%s)\b$' % allowed_extensions_regex)
skiped_dirs = re.compile(r'.*(%s)$' % skiped_dirs_regex)
# Enable os disable colons
if configs["REQUIRE_COLON"] == "1":
    known_marks = re.compile(r'\b(%s)\b\s?: +(.*?)$' % known_marks_regex)
else:
    known_marks = re.compile(r'\b(%s)\b\s?:? +(.*?)$' % known_marks_regex)
skiped_files = re.compile(r"("+skiped_files_regex+")$")

total_marks = 0

# Helper Functions
def file_link(file, line=0):
    return "gedit:///%s?line=%d" % (file,line-1)

# Escape possible tags from comments as HTML
def escape(str_):
    lt = re.compile(r'<')
    gt = re.compile(r'>')
    return lt.sub("&lt;",gt.sub("&gt;",str_))

# Todo Header image pattern
def todo_header():
    return "file:///%s/.gnome2/gedit/plugins/todo/todo_header.png" % home_folder

# Todo Gear Image
def todo_gears():
    return  "file:///%s/.gnome2/gedit/plugins/todo/todo_gears.png"  % home_folder

# Initialize the values list
values = []

# Markup Label Counter
labels = {}

for label in known_marks_list:
    labels[label]=0


# walk over directory tree
def walktree(top, callback):
    '''recursively descend the directory tree rooted at top,
       calling the callback function for each regular file'''

    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        try:
            mode = os.stat(pathname)[ST_MODE]
            if S_ISDIR(mode):
                # It's a directory, recurse into it
                if not skiped_dirs.match(pathname):
                    walktree(pathname, callback)
            elif S_ISREG(mode):
                # It's a file, call the callback function
                if not skiped_files.match(pathname):
                    callback(pathname)
            else:
                # Unknown file type, pass
                pass
        except OSError:
            continue

# Test File Callback function
def test_file(file):
    """ Parse the file passed as argument searching for TODO Tags"""
    if allowed_types.match(file):
        try:
            file_search = open(file, 'r')
        except IOError:
            sys.exit(2)

        data = file_search.read()
        data = data.split('\n')

        # Line Number
        ln = 0
        for line in data:
            ln = ln + 1
            a_match = known_marks.search(line)
            if (a_match):
                pt, fl = os.path.split(file)
                labels[a_match.group(1)] += 1
                result = [file,fl,ln,a_match.group(1),a_match.group(2)]
                values.append(result)

# Search Directories for files matching
walktree(root, test_file)

html = '<div id="todo_list">\n'

# Make the Menu
menu = '<ul id="navigation">\n'
for label in labels:
    total_marks += labels[label]
    if configs['SHOW_EMPTY_MARKS'] == '1' or labels[label]:
        menu += '   <li class="%s"><a href="#%s-title">%s</a>: %d</li>\n' % (label.lower(), label.lower(), label, labels[label])

menu += '<li class="total">Total: %d</li></ul>\n' % total_marks

table_pattern = Template(\
"""\
    <h2 id=\"${label}-title\">${labelU}</h2>
    <table id="${label}">
    <thead>
        <tr>
            <th class="file">File</th>
            <th class="comment">Comment</th>
        </tr>
    </thead>
    <tbody>
"""
)

tables = {}

for label_ in known_marks_list:
    tables[label_]= table_pattern.substitute(dict(label=label_.lower(),labelU=label_.upper()))

table_row_pattern = '        <tr class="%s"><td><a href="%s"  title="%s">%s</a> <span>(%s)</span></td><td>%s</td>\n'

def format_row(value_):
    return table_row_pattern % (css, file_link(value_[0], value_[2]), value_[0], value_[1], value_[2], value_[4])

for ix, value in enumerate(sorted(values,key=operator.itemgetter(3))):
    css = 'odd'
    if ix % 2 == 0:
        css = 'even'
    for table_value in tables:
        if value[3] == table_value:
            tables[table_value] += format_row(value)

for table_value in tables:
    tables[table_value] += '    </tbody></table>\n'

html += menu

for label in labels:
    if labels[label]:
        html += tables[label]

html += '   <a href="#todo_list" id="toplink">↑ top</a>\n  </div>'

todo_links_css_pattern = \
"""
    #${label}-title {
        color: ${color};
    }
    li.${label} {
        background: ${color};
    }
"""

todo_links_css = ''

color_rx = re.compile(r'^(.*)(#[0-9a-fA-F]{6})$')

todo_links_template = Template(todo_links_css_pattern)

for markcolor in configs['MARK_COLORS'].split(';'):
    c_match = color_rx.search(markcolor)
    if c_match:
        mark,mcolor = c_match.group(1), c_match.group(2)
        todo_links_css += todo_links_template.substitute(label=mark.lower(),color=mcolor)
# TODO: load this template pattern from a file.
html_pattern = \
"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html>
<head>
    <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
    <title>TODO-List</title>
    <style type="text/css">
    * {
        color: #333;
    }

    body {
        font-size: 12px;
        font-family: "bitstream vera sans mono", "sans-serif";
        padding: 0;
        margin: 0;
        width: 700px;
        height: 500px;
    }

    th {
        text-align: left;
    }

    td {
        vertical-align: top;
    }

    ${labelcss}

    th, a {
        color: #0D2681;
    }

    .odd td {
        background: #f0f0f0;
    }

    table {
        border-collapse: collapse;
        width: 650px;
    }

    td,th {
        padding: 3px;
    }

    th {
        border-bottom: 1px solid #999;
    }

    th.file {
        width: 30%;
    }

    #toplink {
        position: fixed;
        bottom: 10px;
        right: 40px;
    }

    h1 {
        color: #fff;
        padding: 20px 5px 18px 5px;
        margin: 0;
    }

    h2 {
        font-size: 16px;
        margin: 0 0 10px;
        padding-top: 30px;
    }

    #page {
        overflow: auto;
        height: 406px;
        padding: 0 15px 20px 15px;
        position: relative;
    }

    #root {
        position: absolute;
        top: 28px;
        right: 23px;
        color: #fff;
    }

    #navigation {
        margin: 0;
        padding: 0;
        border-left: 1px solid #000;
    }

    #navigation * {
        color: #fff;
    }

    li.total {
        background: #000000;
        font-weight: bold
    }

    #navigation li {
        float: left;
        list-style: none;
        text-align: center;
        padding: 7px 10px;
        margin: 0;
        border: 1px solid #000;
        border-left: none;
        font-weight: bold
    }

    #navigation:after {
        content: ".";
        display: block;
        height: 0;
        clear: both;
        visibility: hidden;
    }

    #todo_list {
        padding-top: 30px;
    }

    #container {
        position: relative;
        background: url(${todo_header}) repeat-x;
    }

    #gears {
        float : right;
        margin : 0 0 0 0;
    }

    </style>
</head>
<body>
<div id="container">
<img src="${todo_gears}" id="gears" />
<h1>TODO List</h1>
<p id="root">${root}</p>
<div id="page">
    ${html}
</div>
</div>
</body>
</html>
"""

markup = Template(html_pattern)

markup_out = markup.substitute(todo_header=todo_header(), \
    todo_gears=todo_gears(),root=escape(root), html=html, \
    labelcss=todo_links_css)

# Remove the file if exists
try:
    os.unlink(temp_file_name)
except OSError:
    pass

# Create the temp new file
tmp_file = open(temp_file_name,'w')
tmp_file.write(markup_out)
tmp_file.close()

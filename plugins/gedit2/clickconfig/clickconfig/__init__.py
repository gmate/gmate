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
Click_Config plugin package

2010-09-20
Version 1.2.0

Description:
This plugin provides configurable text selections based on single or multiple
left mouse button clicks, i.e.,
    single click, double click, triple click, quadruple click, quintuple click.

For example, a double click can be set to select names that include
underscores, or a quadruple click can be set to select a paragraph.

Regular expressions are used for specifying types of text selections.

The plugin also creates a submenu within Gedit's Edit menu for accessing the
configuration window or directly making a selection.  This allows for hotkeys
to be set for any of the defined selections.

Typical location:
~/.gnome2/gedit/plugins     (for one user)
    or
/usr/lib/gedit-2/plugins    (for all users)

Files:
clickconfig.gedit-plugin    -- Gedit reads this to know about the plugin.
clickconfig/                -- Package directory
    __init__.py             -- Package module loaded by Gedit.
    click_config.py         -- Plugin and plugin helper classes.
    data.py                 -- Configuration data classes.
    dictfile.py             -- Reads/writes dictionaries from/to files.
    ui.py                   -- Configuration window class.
    Click_Config.xml        -- Configuration window layout (from .glade file)
    Click_Config.glade      -- Configuration window layout from Glade.
    gpl.txt                 -- GNU General Public License.
    
    click_config_configs    -- Created by user customization to store settings.

How it loads:
1. Gedit finds clickconfig.gedit-plugin in its plugins directory.
2. That file tells Gedit to use Python to load the clickconfig module.
3. Python identifies the clickconfig directory as the clickconfig module.
4. Python loads __init__.py (this file) from the clickconfig directory.
5. This file imports the ClickConfigPlugin class from click_config.py.
6. Gedit identifies ClickConfigPlugin as the gedit.Plugin object.
7. Gedit calls methods of ClickConfigPlugin.

"""
from .click_config import ClickConfigPlugin


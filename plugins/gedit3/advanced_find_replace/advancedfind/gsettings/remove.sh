#!/bin/sh

rm /usr/share/glib-2.0/schemas/org.gnome.gedit.plugins.advancedfind.gschema.xml
glib-compile-schemas /usr/share/glib-2.0/schemas/

#!/bin/sh

cp org.gnome.gedit.plugins.advancedfind.gschema.xml /usr/share/glib-2.0/schemas/
glib-compile-schemas /usr/share/glib-2.0/schemas/

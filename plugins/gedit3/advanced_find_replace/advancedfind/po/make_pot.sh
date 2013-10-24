#!/bin/bash
#
#Make pot file.

app_name="advancedfind"

xgettext --output="${app_name}".pot ../*.py ../*.glade



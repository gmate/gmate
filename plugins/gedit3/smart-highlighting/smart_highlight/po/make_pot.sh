#!/bin/bash
#
#Make pot file.

app_name="smart_highlight"

xgettext --output="${app_name}".pot ../*.py ../*.glade



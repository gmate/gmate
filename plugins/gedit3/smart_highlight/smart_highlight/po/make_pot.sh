#!/bin/bash
#
#Make pot file.

app_name="smart-highlight"

xgettext --output="${app_name}".pot ../*.py ../*.glade



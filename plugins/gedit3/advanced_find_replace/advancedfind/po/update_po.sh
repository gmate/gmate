#!/bin/bash
#
#Update po file.

app_name="advancedfind"
locale_str=$(zenity --entry --title="Locale" --text="Enter the locale : " --entry-text="")
if [ "${locale_str}" == "" ]; then
	exit
fi

xgettext --output="${app_name}".pot ../*.py ../*.glade
msgmerge -U "${locale_str}".po "${app_name}".pot



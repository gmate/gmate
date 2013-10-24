#!/bin/bash
#
#Update po file.

app_name="smart_highlight"
locale_str=$(zenity --entry --title="Locale" --text="Enter the locale : " --entry-text="")
if [ "${locale_str}" == "" ]; then
	exit
fi

msgmerge -U "${locale_str}".po "${app_name}".pot



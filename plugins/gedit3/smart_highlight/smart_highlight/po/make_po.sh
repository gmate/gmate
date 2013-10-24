#!/bin/bash
#
#Make po file.

app_name="smart_highlight"
locale_str=$(zenity --entry --title="Locale" --text="Enter the locale : " --entry-text="")
if [ "${locale_str}" == "" ]; then
	exit
fi

msginit --input="${app_name}".pot --locale="${locale_str}" --no-translator


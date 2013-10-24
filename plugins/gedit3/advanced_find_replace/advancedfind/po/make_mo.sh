#!/bin/bash
#
#Make mo file.

app_name="advancedfind"
locale_str=$(zenity --entry --title="Locale" --text="Enter the locale : " --entry-text="")
if [ "${locale_str}" == "" ]; then
	exit
fi

mkdir -pv ../locale/"${locale_str}"/LC_MESSAGES/
msgfmt --output-file=../locale/"${locale_str}"/LC_MESSAGES/"${app_name}".mo "${locale_str}".po
#msgfmt --output-file="${app_name}".mo "${locale_str}".po


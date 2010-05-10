#!/bin/sh
# Kill all runing instances if exists
# killall gedit

# Put the Zen Coding image in the correct place and update Icon Cache.
sudo cp plugins/zencoding/zencoding.png /usr/share/icons/hicolor/16x16/apps
sudo gtk-update-icon-cache /usr/share/icons/hicolor > /dev/null 2>&1
# Register rails-related mime types
sudo cp mime/rails.xml /usr/share/mime/packages
sudo cp mime/cfml.xml /usr/share/mime/packages
# Copy language definitions
sudo cp lang-specs/*.lang /usr/share/gtksourceview-2.0/language-specs/
# Copy Gmate executable
sudo mkdir -p /usr/share/gedit-2/gmate
sudo cp gmate.py /usr/share/gedit-2/gmate/gmate.py
# Copy Tags
if [ ! -d /usr/share/gedit-2/plugins/taglist/ ]
then
  sudo mkdir -p /usr/share/gedit-2/plugins/taglist/
fi
sudo cp tags/*.tags.gz /usr/share/gedit-2/plugins/taglist/

# Update mime type database
sudo update-mime-database /usr/share/mime

# Copy gedit facilities
if [ ! -d $HOME/.gnome2/gedit ]
then
  mkdir -p ~/.gnome2/gedit
fi
# Copy Snippets
if [ ! -d $HOME/.gnome2/gedit/snippets ]
then
  mkdir -p ~/.gnome2/gedit/snippets
fi
cp snippets/* ~/.gnome2/gedit/snippets/

# Copy Plugins
if [ ! -d $HOME/.gnome2/gedit/plugins ]
then
  mkdir -p ~/.gnome2/gedit/plugins
fi
cp -R plugins/* ~/.gnome2/gedit/plugins

# Copy Styles
if [ ! -d $HOME/.gnome2/gedit/styles ]
then
  mkdir -p ~/.gnome2/gedit/styles
fi
cp styles/* ~/.gnome2/gedit/styles

# Ask for Python-Webkit package
if [ -f /etc/debian_version ]; then
  sudo apt-get install python-webkit
fi

# Execute debian postins script

`sudo sh ./debian/postinst`

echo -n "Do you want to activate default plugin and configuration set? [y,N]:"
read answer
case "$answer" in
    [yY])
        `gconftool-2 --set /apps/gedit-2/plugins/active-plugins -t list --list-type=str [rails_extract_partial,rubyonrailsloader,align,smart_indent,text_tools,completion,quickhighlightmode,gemini,trailsave,rails_hotkeys,snapopen,filebrowser,snippets,modelines,smartspaces,docinfo,time,spell,terminal,drawspaces,codecomment,colorpicker,indent]`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/auto_indent/auto_indent -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/bracket_matching/bracket_matching -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/current_line/highlight_current_line -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/cursor_position/restore_cursor_position -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/line_numbers/display_line_numbers -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/right_margin/display_right_margin -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/right_margin/right_margin_position -t int 80`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/colors/scheme -t str twilight`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/tabs/insert_spaces -t bool true`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/tabs/tabs_size -t int 4`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/wrap_mode/wrap_mode -t str GTK_WRAP_NONE`
        `gconftool-2 --set /apps/gedit-2/preferences/editor/save/create_backup_copy -t bool false`
        echo "Configuration set."
        ;;
        *)
        echo "No config performed."
        ;;
esac


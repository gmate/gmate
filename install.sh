#!/bin/sh
# Kill all runing instances if exists
#killall gedit

# Register rails-related mime types
sudo cp mime/rails.xml /usr/share/mime/packages
# Copy language definitions
sudo cp lang-specs/*.lang /usr/share/gtksourceview-2.0/language-specs/
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

echo -n "Do you want to activate default plugin and configuration set? [y,N]:"
read answer
case "$answer" in
    [yY])
        `gconftool-2 --set /apps/gedit-2/plugins/teste -t list --list-type=str [smart_indent,text_tools,trailsave,rails_extract_partial,snapopen,rubyonrailsloader,quickhighlightmode,gemini,completion,align,spell,codecomment,time,pythonconsole,drawspaces,indent,snippets,smartspaces,docinfo,modelines,colorpicker,filebrowser]`
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
        echo "Configuration set."
        ;;
        *)
        echo "No config performed."
        ;;
esac


#!/bin/sh
# Kill all runing instances if exists
# killall gedit

## Try to use sudo
#echo "Type root password if you want to install system wide. Press [Enter] to install to this user only."
#sudo -v

#if [ $(id -u) = "0" ]; then
#  sudo="yes"
#else
#  sudo="no"
#fi

## Copy gedit facilities
#if [ $sudo = "yes" ]; then
#    if [ ! -d $HOME/.gnome2/gedit ]; then
#        mkdir -p ~/.gnome2/gedit
#    fi
#fi

## Copy language definitions
#if [ $sudo = "yes" ]; then
#    sudo cp lang-specs/*.lang /usr/share/gtksourceview-2.0/language-specs/
#else
#    mkdir -p ~/.local/share/gtksourceview-2.0/language-specs
#    cp lang-specs/* ~/.local/share/gtksourceview-2.0/language-specs/
#fi

## Register rails-related mime types
#if [ $sudo = "yes" ]; then
#    sudo cp mime/rails.xml /usr/share/mime/packages
#    sudo cp mime/cfml.xml /usr/share/mime/packages
#else
#    mkdir -p ~/.local/share/mime/packages
#    cp mime/rails.xml ~/.local/share/mime/packages
#    cp mime/cfml.xml ~/.local/share/mime/packages
#fi

## Update mime type database
#if [ $sudo = "yes" ]; then
#    sudo update-mime-database /usr/share/mime
#else
#    update-mime-database ~/.local/share/mime
#fi

## Copy Gmate executable
#if [ $sudo = "yes" ]; then
#    sudo mkdir -p /usr/share/gedit-2/gmate
#    sudo cp gmate.py /usr/share/gedit-2/gmate/gmate.py
#else
#    mkdir -p ~/gmate
#    cp gmate.py ~/gmate
#fi

## Copy Tags
#if [ $sudo = "yes" ]; then
#    sudo mkdir -p /usr/share/gedit-2/plugins/taglist/
#    sudo cp tags/*.tags.gz /usr/share/gedit-2/plugins/taglist/
#else
#    mkdir -p ~/.gnome2/gedit/taglist/
#    cp tags/*.tags.gz ~/.gnome2/gedit/taglist/
#fi

## Copy Snippets
#if [ $sudo = "yes" ]; then
#    sudo cp snippets/* /usr/share/gedit-2/plugins/snippets/
#else
#    if [ ! -d $HOME/.gnome2/gedit/snippets ]; then
#        mkdir -p ~/.gnome2/gedit/snippets
#    fi
#    cp snippets/* ~/.gnome2/gedit/snippets/
#fi

## Copy plugins
#if [ $sudo = "yes" ]; then
#    for plugin in plugins/gedit2/*; do
#        sudo cp -R $plugin/* /usr/lib/gedit-2/plugins/
#    done
#else
#    if [ ! -d $HOME/.gnome2/gedit/plugins ]; then
#        mkdir -p ~/.gnome2/gedit/plugins
#    fi
#    for plugin in plugins/gedit2/*; do
#        cp -R $plugin/* ~/.gnome2/gedit/plugins
#    done
#fi

## Copy Styles
#if [ $sudo = "yes" ]; then
#    sudo cp styles/* /usr/share/gtksourceview-2.0/styles/
#else
#    if [ ! -d $HOME/.gnome2/gedit/styles ]; then
#        mkdir -p ~/.gnome2/gedit/styles
#    fi
#    cp styles/* ~/.gnome2/gedit/styles
#fi

## Ask for Python-Webkit package
#if [ -f /etc/debian_version ]; then
#  if [ $sudo = "yes" ]; then
#    sudo apt-get install python-webkit
#  else
#    echo "Please install python-webkit (sudo apt-get install python-webkit)"
#  fi
#fi

## Execute debian postins script
#if [ $sudo = "yes" ]; then
#  `sudo sh ./debian/postinst`
#else
#  `sh ./debian/postinst`
#fi

echo -n "Do you want to activate default plugin and configuration set? [y,N]:"
read answer
case "$answer" in
    [yY])
        gconftool-2 --set /apps/gedit-2/plugins/active-plugins -t list --list-type=str [rails_extract_partial,rubyonrailsloader,align,smart_indent,text_tools,completion,quickhighlightmode,gemini,trailsave,rails_hotkeys,fuzzyopen,filebrowser,snippets,modelines,smartspaces,docinfo,time,spell,terminal,drawspaces,codecomment,colorpicker,indent,encodingpy,FindInProject]
        gconftool-2 --set /apps/gedit-2/preferences/editor/auto_indent/auto_indent -t bool true
        gconftool-2 --set /apps/gedit-2/preferences/editor/bracket_matching/bracket_matching -t bool true
        gconftool-2 --set /apps/gedit-2/preferences/editor/current_line/highlight_current_line -t bool true
        gconftool-2 --set /apps/gedit-2/preferences/editor/cursor_position/restore_cursor_position -t bool true
        gconftool-2 --set /apps/gedit-2/preferences/editor/line_numbers/display_line_numbers -t bool true
        gconftool-2 --set /apps/gedit-2/preferences/editor/right_margin/display_right_margin -t bool true
        gconftool-2 --set /apps/gedit-2/preferences/editor/right_margin/right_margin_position -t int 80
        gconftool-2 --set /apps/gedit-2/preferences/editor/colors/scheme -t str twilight
        gconftool-2 --set /apps/gedit-2/preferences/editor/tabs/insert_spaces -t bool true
        gconftool-2 --set /apps/gedit-2/preferences/editor/tabs/tabs_size -t int 4
        gconftool-2 --set /apps/gedit-2/preferences/editor/wrap_mode/wrap_mode -t str GTK_WRAP_NONE
        gconftool-2 --set /apps/gedit-2/preferences/editor/save/create_backup_copy -t bool false
        echo "Configuration set."
        ;;
    *)
        echo "No config performed."
        ;;
esac

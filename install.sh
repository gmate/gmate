#!/bin/sh
# Kill all runing instances if exists
# killall gedit

version3="`gedit --version | grep '\s3\.'`"

# Try to use sudo
echo "Type root password if you want to install system wide. Press [Enter] to install to this user only."
sudo -v

if [ $(id -u) = "0" ]; then
    sudo="yes"
else
    sudo="no"
fi

# Copy gedit facilities
if [ $sudo = "yes" ]; then
    if [ ! -d $HOME/.gnome2/gedit ]; then
        mkdir -p ~/.gnome2/gedit
    fi
fi

# Copy language definitions
if [ "$(echo $version3)" ]; then
    gtksourceview="gtksourceview-3.0"
else
    gtksourceview="gtksourceview-2.0"
fi
if [ $sudo = "yes" ]; then
    sudo cp lang-specs/*.lang /usr/share/$gtksourceview/language-specs/
else
    mkdir -p ~/.local/share/$gtksourceview/language-specs
    cp lang-specs/* ~/.local/share/$gtksourceview/language-specs/
fi

# Copy Styles
if [ $sudo = "yes" ]; then
    sudo cp styles/* /usr/share/$gtksourceview/styles/
else
    if [ "$(echo $version3)" ]; then
        if [ ! -d $HOME/.local/share/$gtksourceview/styles ]; then
            mkdir -p ~/.local/share/$gtksourceview/styles
        fi
        cp styles/* ~/.local/share/$gtksourceview/styles
    else
        if [ ! -d $HOME/.gnome2/gedit/styles ]; then
            mkdir -p ~/.gnome2/gedit/styles
        fi
        cp styles/* ~/.gnome2/gedit/styles
    fi
fi

# Register MIME-types
if [ $sudo = "yes" ]; then
    sudo cp mime/*.xml /usr/share/mime/packages
    sudo update-mime-database /usr/share/mime
else
    mkdir -p ~/.local/share/mime/packages
    cp mime/*.xml ~/.local/share/mime/packages
    update-mime-database ~/.local/share/mime
fi

if [ "$(echo $version3)" ]; then
    geditdir="gedit"
else
    geditdir="gedit-2"
fi

# Copy Gmate executable
if [ $sudo = "yes" ]; then
    sudo mkdir -p /usr/share/$geditdir/gmate
    sudo cp gmate.py /usr/share/$geditdir/gmate/gmate.py
else
    mkdir -p ~/gmate
    cp gmate.py ~/gmate
fi

# Copy Tags
if [ $sudo = "yes" ]; then
    sudo mkdir -p /usr/share/$geditdir/plugins/taglist/
    sudo cp tags/*.tags.gz /usr/share/$geditdir/plugins/taglist/
else
    mkdir -p ~/.gnome2/gedit/taglist/
    cp tags/*.tags.gz ~/.gnome2/gedit/taglist/
fi

# Copy Snippets
if [ $sudo = "yes" ]; then
    sudo cp snippets/* /usr/share/$geditdir/plugins/snippets/
else
    if [ ! -d $HOME/.gnome2/gedit/snippets ]; then
        mkdir -p ~/.gnome2/gedit/snippets
    fi
    cp snippets/* ~/.gnome2/gedit/snippets/
fi

# Copy plugins
if [ "$(echo $version3)" ]; then
    if [ $sudo = "yes" ]; then
        for plugin in plugins/gedit3/*; do
            sudo cp -R $plugin /usr/lib/gedit/plugins/
        done
    else
        if [ ! -d $HOME/.local/share/gedit/plugins ]; then
            mkdir -p ~/.local/share/gedit/plugins
        fi
        for plugin in plugins/gedit3/*; do
            cp -R $plugin ~/.local/share/gedit/plugins
        done
    fi
else
    if [ $sudo = "yes" ]; then
        for plugin in plugins/gedit2/*; do
            sudo cp -R $plugin/* /usr/lib/gedit-2/plugins/
        done
    else
        if [ ! -d $HOME/.gnome2/gedit/plugins ]; then
            mkdir -p ~/.gnome2/gedit/plugins
        fi
        for plugin in plugins/gedit2/*; do
            cp -R $plugin/* ~/.gnome2/gedit/plugins
        done
    fi
fi

if [ !"$(echo $version3)" ]; then
    # Ask for Python-Webkit package
    if [ -f /etc/debian_version ]; then
      if [ $sudo = "yes" ]; then
        sudo apt-get install python-webkit
      else
        dpkg --list python-webkit > /dev/null 2>&1 || echo "Please install python-webkit (sudo apt-get install python-webkit)"
      fi
    fi

    # Execute debian postins script
    if [ $sudo = "yes" ]; then
      `sudo sh ./debian/postinst`
    else
      # Fix for the RestoreTabs plugin
      if [ ! -d $HOME~/.local/share/glib-2.0/schemas/ ]; then
          mkdir -p ~/.local/share/glib-2.0/schemas/
      fi
      mv ~/.local/share/gedit/plugins/restoretabs/org.gnome.gedit.plugins.restoretabs.gschema.xml ~/.local/share/glib-2.0/schemas/
      glib-compile-schemas ~/.local/share/glib-2.0/schemas/
    fi

    echo -n "Do you want to activate default plugin and configuration set? [y,N]:"
    read answer
    case "$answer" in
        [yY])
            gconftool-2 --set /apps/gedit-2/plugins/active-plugins -t list --list-type=str [rails_extract_partial,rubyonrailsloader,align-columns,smart_indent,text_tools,completion,quickhighlightmode,gemini,trailsave,rails_hotkeys,fuzzyopen,filebrowser,snippets,modelines,smartspaces,docinfo,time,spell,terminal,drawspaces,codecomment,colorpicker,indent,encodingpy,FindInProject]
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
fi

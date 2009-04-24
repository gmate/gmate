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

echo -n "Do you want to activate default plugin set? [y,N]:"
read answer
case "$answer" in
    [yY])
        `gconftool-2 --set /apps/gedit-2/plugins/teste -t list --list-type=str [smart_indent,text_tools,trailsave,rails_extract_partial,snapopen,rubyonrailsloader,quickhighlightmode,gemini,completion,align,spell,time,pythonconsole,indent,snippets,docinfo,modelines,filebrowser]`
        echo "Configuration set."
        ;;
        *)
        echo "No config performed."
        ;;
esac


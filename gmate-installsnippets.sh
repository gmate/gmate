#!/bin/sh

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

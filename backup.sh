#!/bin/sh

cp ~/.gnome2/gedit/snippets/* ./snippets/

cp -R ~/.gnome2/gedit/plugins/* ./plugins/

cp ~/.gnome2/gedit/styles/* ./styles/

cp /usr/share/gtksourceview-2.0/language-specs/ruby.lang ./lang-specs/
cp /usr/share/gtksourceview-2.0/language-specs/yml.lang ./lang-specs/
cp /usr/share/gtksourceview-2.0/language-specs/rhtml.lang ./lang-specs/

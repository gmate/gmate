#!/bin/sh

if [ ! -d ./build/ ]
then
  mkdir ./build/
fi

rm -rf ./build/tmp
# Configure control folder and file
mkdir -p ./build/tmp/gedit-gmate
cp -r DEBIAN ./build/tmp/gedit-gmate/
# Copy language specs
mkdir -p ./build/tmp/gedit-gmate/usr/share/gtksourceview-2.0/language-specs
cp ./lang-specs/*.lang ./build/tmp/gedit-gmate/usr/share/gtksourceview-2.0/language-specs/
# Copy mime type
mkdir -p ./build/tmp/gedit-gmate/usr/share/mime/packages
cp ./mime/* ./build/tmp/gedit-gmate/usr/share/mime/packages/
# Copy Plugins
mkdir -p ./build/tmp/gedit-gmate/usr/lib/gedit-2/plugins
cp -r ./plugins/* ./build/tmp/gedit-gmate/usr/lib/gedit-2/plugins/
# Copy Snippets
mkdir -p ./build/tmp/gedit-gmate/usr/share/gedit-2/gmate/snippets
cp -r ./snippets/* ./build/tmp/gedit-gmate/usr/share/gedit-2/gmate/snippets/
cp gmate-installsnippets.sh ./build/tmp/gedit-gmate/usr/share/gedit-2/gmate/
# Copy Styles
mkdir -p ./build/tmp/gedit-gmate/usr/share/gtksourceview-2.0/styles
cp -r ./styles/* ./build/tmp/gedit-gmate/usr/share/gtksourceview-2.0/styles/
# Copy documentation
mkdir -p ./build/tmp/gedit-gmate/usr/share/gedit-2/gmate/doc
cp README.rdoc ./build/tmp/gedit-gmate/usr/share/gedit-2/gmate/doc/
# Copy the command line helper
cp gmate.py ./build/tmp/gedit-gmate/usr/share/gedit-2/gmate/
# Make the deb package
dpkg-deb -b ./build/tmp/gedit-gmate ./build
# Remove temporary directory
rm -rf ./build/tmp


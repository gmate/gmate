#!/bin/sh
# Build all files to upload to PPA.

version=`cat debian/control | grep ^Standards-Version: | awk '{print $2}'`
dir=gedit-gmate-$version

if [ -d package ]; then
    rm -R package
fi
mkdir package
cd package

mkdir $dir
cd $dir

for file in `ls -A ../../ | grep -v package`; do
    cp -R ../../$file ./
done

rm -Rf .git
rm -Rf build
for file in `find . -name \*.gitignore`; do cp -R $file ./; done
rm -R DEBIAN

debuild -S

cd ..
rm -R $dir
cd ..

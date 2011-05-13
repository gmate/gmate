#!/bin/sh
# Build all files to upload to PPA or .deb package (call with deb argument).
# 
# To build release install developer’s packages:
# sudo apt-get install devscripts debhelper

version=`cat debian/control | grep ^Standards-Version: | awk '{print $2}'`
dir=gedit-gmate-$version

if [ -d build ]; then
    rm -R build
fi
mkdir -p build/$dir
cd build/$dir

for file in `ls -A ../../ | grep -v build`; do
    cp -R ../../$file ./
done

rm -Rf .git
rm -Rf build
for file in `find . -name \*.gitignore`; do cp -R $file ./; done

if [ 'deb' = "$1" ]; then
    debuild
else
    debuild -S
fi

cd ..
rm -R $dir

if [ 'deb' = "$1" ]; then
    for file in `ls ./ | grep -v .deb`; do
        rm $file
    done
fi

cd ..

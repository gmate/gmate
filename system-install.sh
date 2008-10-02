#!/bin/sh
# Register rails-related mime types
sudo cp mime/rails.xml /usr/share/mime/packages
# Copy language definitions
sudo cp lang-specs/*.lang /usr/share/gtksourceview-2.0/language-specs/
# Update mime type database
sudo update-mime-database /usr/share/mime

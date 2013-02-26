Gedit Source Code Browser
=========================

A source code class and function browser plugin for Gedit 3. 

* Author: Micah Carrick

This plugin will add a new tab to the side pane in the Gedit text editor which
shows symbols (functions, classes, variables, etc.) for the active document. 
Clicking a symbol in the list wil jump to the line on which that symbol is 
defined.

See the [ctags supported languages](http://ctags.sourceforge.net/languages.html)
for a list of the 41 programming languages supported by this plugin.


Requirements
------------

This plugins is for Gedit 3 and is **not compatible with Gedit 2.x**. 

The Gedit Source Code Browser plugin uses 
[Exuberant Ctags](http://ctags.sourceforge.net/) to parse symbols
out of source code. Exuberant Ctags is avaialable in the software repository for
many distributions. To make sure you have ctags correctly installed, issue
the following command:

    ctags --version
    
Make sure that you see *Exuberant* Ctags in the version output.


Installation
------------

1. Download this repository by clicking the Downloads button at the top of the 
   github page or issue the following command in a terminal:

    git clone git://github.com/Quixotix/gedit-source-code-browser.git

2. Copy the file `sourcecodebrowser.plugin` and the folder `sourcecodebrowser` to
   `~/.local/share/gedit/plugins/`.

3. Restart Gedit.

4. Activate the plugin in Gedit by choosing 'Edit > Preferences', the selecting
   the 'Plugins' tab, and checking the box next to 'Soucre Code Browser'.
   
5. (Optional) If you want to enable the configuration dialog you need to compile
   the settings schema. You must do this as root.

    cd /home/&lt;YOUR USER NAME&gt;/.local/share/gedit/plugins/sourcecodebrowser/data/
    
    cp org.gnome.gedit.plugins.sourcecodebrowser.gschema.xml /usr/share/glib-2.0/schemas/
    
    glib-compile-schemas /usr/share/glib-2.0/schemas/

Screenshots
-----------

![Python code in Source Code Browser](http://www.micahcarrick.com/images/gedit-source-code-browser/python.png)


Known Issues
------------

* CSS is not supported. This issue is about ctags and not this plugin. You can
  [extend ctags](http://ctags.sourceforge.net/EXTENDING.html) to add support for 
  any language you like. Many people have provided their fixes to on internet 
  such as this [patch for CSS support](http://scie.nti.st/2006/12/22/how-to-add-css-support-to-ctags).
  
* PHP is supported, however, PHP5 classes are not well supported. This is again
  an issue with ctags. There are numerous fixes to be found onn the internet
  such as these 
  [patches for better PHP5 support](http://www.jejik.com/articles/2008/11/patching_exuberant-ctags_for_better_php5_support_in_vim/).


License
-------

Copyright (c) 2011, Micah Carrick
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this 
list of conditions and the following disclaimer.
      
* Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.
    
* Neither the name of Micah Carrick nor the names of its 
contributors may be used to endorse or promote products derived from this 
software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR 
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON 
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

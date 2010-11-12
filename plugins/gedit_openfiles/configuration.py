from lib import sgconf

class Configuration(sgconf.Options):
    _uri = u"/apps/gedit-2/plugins/openfiles"

    exclude_list = sgconf.ListOption(['*pyc', '*.class', '*.swp', '.svn', '.git', '*.gif', '*.png', '*.jpg', '*.jpeg', '*.ico'])
    static_root_path = sgconf.StringOption('/')
    use_filebrowser = sgconf.BoolOption(True)


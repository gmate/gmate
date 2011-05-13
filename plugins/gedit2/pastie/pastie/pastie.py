import urllib2
import urllib

PASTES = {
    'Ruby (on Rails)':'ruby_on_rails',
    'Ruby':'ruby',
    'Python':'python',
    'Plain Text':'plain_text',
    'ActionScript':'actionscript',
    'C/C++':'c++',
    'CSS':'css',
    'Diff':'diff',
    'HTML (Rails)':'html_rails',
    'HTML / XML':'html',
    'Java':'java',
    'JavaScript':'javascript',
    'Objective C/C++':'objective-c++',
    'PHP':'php',
    'SQL':'sql',
    'Shell Script':'shell-unix-generic'
}
#because dictionaries don't store order
LANGS = ('Ruby (on Rails)', 'Ruby', 'Python', 'Plain Text', 'ActionScript', 'C/C++', 'CSS', 'Diff', 'HTML (Rails)', 'HTML / XML', 'Java', 'JavaScript', 'Objective C/C++', 'PHP', 'SQL', 'Shell Script')
         
URL = 'http://pastie.org/pastes'

class Pastie:

    def __init__(self, text='', syntax='Plain Text', private=False):
        self.text = text
        self.syntax = syntax
        self.private = private

    def paste(self):
        if not PASTES.has_key(self.syntax):
            return 'Wrong syntax.'
        
        opener = urllib2.build_opener()
        params = {
                  'paste[body]':self.text,
                  'paste[parser]':PASTES[self.syntax],
                  'paste[authorization]':'burger' #pastie protecion against general spam bots
                  }
        if self.private:
            params['paste[restricted]'] = '1'
        else:
            params['paste[restricted]'] = '0'
            
        data = urllib.urlencode(params)
        request = urllib2.Request(URL, data)
        request.add_header('User-Agent', 'PastiePythonClass/1.0 +http://hiler.pl/')
        try:
            firstdatastream = opener.open(request)
        except:
            return 'We are sorry but something went wrong. Maybe pastie is down?'
        else:
            return firstdatastream.url
            

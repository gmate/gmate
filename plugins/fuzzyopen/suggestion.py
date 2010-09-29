"""
    Class for suggestions
"""

import os
import subprocess
from util import debug
import util

max_result = 50
excluded_file_types = ["jpg", "jpeg", "gif", "png", "tif", "psd", "pyc"]

class FuzzySuggestion:
  def __init__( self, filepath, show_hidden=False, git=False ):
    self._filepath = filepath
    self._show_hidden = show_hidden
    self._git = git
    if self._git:
      self._load_git()
    self._load_file()

  def _load_file( self ):
    self._fileset = []
    for dirname, dirnames, filenames in os.walk( self._filepath ):
      if not self._show_hidden:
        for d in dirnames[:]:
          if d[0] == '.':
            dirnames.remove(d)
      path = os.path.relpath( dirname, self._filepath )
      for filename in filenames:
        if (self._show_hidden or filename[0] != '.'):
          if os.path.splitext( filename )[-1][1:] not in excluded_file_types:
            self._fileset.append( os.path.normpath(os.path.join( path, filename ) ) )
    self._fileset = sorted( self._fileset )
    debug("Loaded files count = %d" % len(self._fileset))

  def _load_git( self ):
    self._git_with_diff = subprocess.Popen(["git", "diff", "--numstat", "--relative"], cwd=self._filepath, stdout=subprocess.PIPE).communicate()[0].split('\n')[:-1]
    debug("Git file path: %s" % self._filepath)
    self._git_with_diff = [ s.strip().split('\t') for s in self._git_with_diff ]
    #print self._git_with_diff
    self._git_files = [ s[2] for s in self._git_with_diff ]

  def suggest( self, sub ):
    suggestion = []
    for f in self._fileset:
      highlight, score = self._match_score( sub, f )
      if score >= len(sub):
        suggestion.append((highlight, f, score))
    suggestion = sorted(suggestion, key=lambda x: x[2], reverse=True)[:max_result]
    debug("Suggestion count = %d" % len(suggestion))
    return [ self._metadata(s) for s in suggestion ]

  def _metadata( self, suggestion ):
    target = os.path.join(self._filepath, suggestion[1])
    time_string = util.relative_time(os.stat(target).st_mtime)
    highlight = suggestion[0] + "\nMODIFY " + time_string
    if self._git and (suggestion[1] in self._git_files):
      index = self._git_files.index(suggestion[1])
      highlight += self._git_string(index)
    return (self._token_string( suggestion[1] ), highlight, suggestion[1])

  def _token_string( self, file ):
    token = os.path.splitext(file)[-1]
    if token != '':
      token = token[1:]
    else:
      token = '.'
    return "<span variant='smallcaps' size='x-large' foreground='#FFFFFF' background='#929292'><b>" + token.upper() + '</b></span>'

  def _git_string( self, line_id ):
    add = int(self._git_with_diff[line_id][0])
    delete = int(self._git_with_diff[line_id][1])
    if add != 0 or delete != 0:
      return "  GIT <tt><span foreground='green'>" + ('+' * add) + "</span><span foreground='red'>" + ('-' * delete) + "</span></tt>"
    else:
      return ""

  def _match_score( self, sub, str ):
    result, score, pos, git, orig_length, highlight = 0, 0, 0, 0, len(str), ''
    for c in sub:
      while str != '' and str[0] != c:
        score = 0
        highlight += str[0]
        str = str[1:]
      if str == '':
        return (highlight, 0)
      score += 1
      result += score
      pos += len(str)
      str = str[1:]
      highlight += "<b>" + c + "</b>"
    highlight += str
    if len(sub) != 0 and orig_length > 1:
      pos = float(pos-1) / ((float(orig_length)-1.0) * float(len(sub)))
    else:
      pos = 0.0
    if self._git and (str in self._git_files):
      git = 1
    return (highlight, float(result) + pos + git)


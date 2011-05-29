#    Gedit file search plugin
#    Copyright (C) 2008-2011  Oliver Gerlich <oliver.gerlich@gmx.de>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


#
# Search functionality classes:
# - LineSplitter (accumulates incoming strings and splits them into lines)
# - RunCommand (runs a shell command and passes the output to LineSplitter)
# - GrepProcess (uses RunCommand to run Grep, parses its output, and passes that to the result window)
# - SearchProcess (uses RunCommand to run Find, parses its output, and starts GrepProcess)
#


import os
import gobject
import fcntl
import subprocess
import re
import errno


class LineSplitter:
    "Split incoming text into lines which are passed to the resultHandler object"
    def __init__ (self, resultHandler):
        self.buf = ""
        self.cancelled = False
        self.resultHandler = resultHandler

    def cancel (self):
        self.cancelled = True

    def parseFragment (self, text):
        if self.cancelled:
            return

        self.buf = self.buf + text

        while '\n' in self.buf:
            pos = self.buf.index('\n')
            line = self.buf[:pos]
            self.buf = self.buf[pos + 1:]
            self.resultHandler.handleLine(line)

    def finish (self):
        self.parseFragment("")
        if self.buf != "":
            self.resultHandler.handleLine(self.buf)
        self.resultHandler.handleFinished()


class RunCommand:
    "Run a command in background, passing all of its stdout output to a LineSplitter"
    def __init__ (self, cmd, resultHandler, prio=gobject.PRIORITY_LOW):
        self.lineSplitter = LineSplitter(resultHandler)

        #print "executing command: %s" % cmd
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
        self.pipe = self.proc.stdout

        # make pipe non-blocking:
        fl = fcntl.fcntl(self.pipe, fcntl.F_GETFL)
        fcntl.fcntl(self.pipe, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        #print "(add watch)"
        gobject.io_add_watch(self.pipe, gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP,
            self.onPipeReadable, priority=prio)

    def onPipeReadable (self, fd, cond):
        #print "condition: %s" % cond
        if (cond & gobject.IO_IN):
            readText = self.pipe.read(4000)
            #print "(read %d bytes)" % len(readText)
            if self.lineSplitter:
                self.lineSplitter.parseFragment(readText)
            return True
        else:
            # read all remaining data from pipe
            while True:
                readText = self.pipe.read(4000)
                #print "(read %d bytes before finish)" % len(readText)
                if len(readText) <= 0:
                    break
                if self.lineSplitter:
                    self.lineSplitter.parseFragment(readText)

            #print "(closing pipe)"
            self.pipe.close()
            self.proc.wait()
            if self.lineSplitter:
                self.lineSplitter.finish()
                self.lineSplitter = None
            return False

    def cancel (self):
        #print "(cancelling command)"
        pid = self.proc.pid
        #print "pid: %d" % pid
        try:
            os.kill(pid, 15)
        except OSError, e:
            if e.errno != errno.ESRCH:
                print "error killing PID %d: %s" % (pid, e)
        self.lineSplitter.cancel()


def buildQueryRE (queryText, caseSensitive, wholeWord):
    "returns a RegEx pattern for searching for the given queryText"

    # word detection etc. cannot be done on an encoding-less string:
    assert(type(queryText) == unicode)

    pattern = re.escape(queryText)
    if wholeWord:
        if re.search('^\w', queryText, re.UNICODE):
            pattern = '\\b' + pattern
        if re.search('\w$', queryText, re.UNICODE):
            pattern = pattern + '\\b'

    flags = re.UNICODE
    if not(caseSensitive):
        flags |= re.IGNORECASE
    return re.compile(pattern, flags)


class GrepProcess:
    def __init__ (self, query, resultCb, finishedCb):
        self.query = query
        self.resultCb = resultCb
        self.finishedCb = finishedCb

        # Assume all file contents are in UTF-8 encoding (AFAIK grep will just search for byte sequences, it doesn't care about encodings):
        self.queryText = query.text.encode("utf-8")

        self.fileNames = []
        self.cmdRunner = None
        self.cancelled = False
        self.numGreps = 0
        self.inputFinished = False

        self.postSearchPattern = None
        if query.wholeWord:
            self.postSearchPattern = buildQueryRE(self.query.text, query.caseSensitive, True)

    def cancel (self):
        self.cancelled = True
        if self.cmdRunner:
            self.cmdRunner.cancel()
            self.cmdRunner = None
        pass

    def addFilename (self, filename):
        self.fileNames.append(filename)
        self.runGrep()

    def handleInputFinished (self):
        "Called when there will be no more input files added"
        self.inputFinished = True
        if not(self.cmdRunner):
            # this can happen if no files at all are found
            self.finishedCb()

    def runGrep (self):
        if self.cmdRunner or len(self.fileNames) == 0 or self.cancelled:
            return

        # run Grep on many files at once:
        maxGrepFiles = 5000
        maxGrepLine = 3800
        fileNameList = []

        i = 0
        numChars = 0
        for f in self.fileNames:
            fileNameList += [f]
            i+=1
            numChars += len(f)
            if i > maxGrepFiles or numChars > maxGrepLine:
                break
        self.fileNames = self.fileNames[i:]

        self.numGreps += 1
        #if self.numGreps % 100 == 0:
            #print "ran %d greps so far" % self.numGreps

        grepCmd = ["grep", "-H", "-I", "-n", "-s", "-Z"]
        if not(self.query.caseSensitive):
            grepCmd += ["-i"]
        if not(self.query.isRegExp):
            grepCmd += ["-F"]

        grepCmd += ["-e", self.queryText]
        grepCmd += fileNameList

        self.cmdRunner = RunCommand(grepCmd, self)

    def handleLine (self, line):
        filename = None
        lineno = None
        linetext = ""
        if '\0' in line:
            [filename, end] = line.split('\0', 1)
            if ':' in end:
                [lineno, linetext] = end.split(':', 1)
                lineno = int(lineno)

        if lineno == None:
            #print "(ignoring invalid line)"
            pass
        else:
            # Assume that grep output is in UTF8 encoding, and convert it to
            # a Unicode string. Also, sanitize non-UTF8 characters.
            # TODO: what's the actual encoding of grep's output?
            linetext = unicode(linetext, 'utf8', 'replace')
            #print "file: '%s'; line: %d; text: '%s'" % (filename, lineno, linetext)
            linetext = linetext.rstrip("\n\r")

            # do some manual grep'ing on each line (for whole-word search):
            if self.postSearchPattern is not None and \
                self.postSearchPattern.search(linetext) is None:
                return

            self.resultCb(filename, lineno, linetext)

    def handleFinished (self):
        #print "grep finished"
        self.cmdRunner = None
        if len(self.fileNames) > 0 and not(self.cancelled):
            self.runGrep()
        else:
            if self.inputFinished:
                #print "ran %d greps" % self.numGreps
                self.finishedCb()


class SearchProcess:
    def __init__ (self, query, resultHandler):
        self.resultHandler = resultHandler
        self.cancelled = False
        self.files = []

        self.grepProcess = GrepProcess(query, self.handleGrepResult, self.handleGrepFinished)

        findCmd = ["find", query.directory]
        if not(query.includeSubfolders):
            findCmd += ["-maxdepth", "1"]
        if query.excludeHidden:
            findCmd += ["(", "!", "-path", "%s*/.*" % query.directory, ")"]
            findCmd += ["(", "!", "-path", "%s.*" % query.directory, ")"]
        if query.excludeBackup:
            findCmd += ["(", "!", "-name", "*~", "!", "-name", ".#*.*", ")"]
        if query.excludeVCS:
            findCmd += ["(", "!", "-path", "*/CVS/*", "!", "-path", "*/.svn/*", "!", "-path", "*/.git/*", "!", "-path", "*/RCS/*", "!", "-path", "*/.bzr/*", ")"]
        if query.selectFileTypes:
            fileTypeList = query.parseFileTypeString()
            if fileTypeList:
                findCmd += ["("]
                for t in fileTypeList:
                    findCmd += ["-name", t, "-o"]
                findCmd.pop()
                findCmd += [")"]
        findCmd += ["-xtype", "f", "-print"]

        self.cmdRunner = RunCommand(findCmd, self, gobject.PRIORITY_DEFAULT_IDLE)

    def cancel (self):
        self.cancelled = True
        if self.cmdRunner:
            self.cmdRunner.cancel()
            self.cmdRunner = None
        if self.grepProcess:
            self.grepProcess.cancel()

    def destroy (self):
        self.cancel()

    def handleLine (self, line):
        #print "find result line: '%s' (type: %s)" % (line, type(line))

        # Note: we don't assume anything about the encoding of output from `find`
        # but just treat it as encoding-less byte sequence.

        self.files.append(line)

    def handleFinished (self):
        #print "find finished (%d files found)" % len(self.files)
        self.cmdRunner = None

        if self.cancelled:
            self.resultHandler.handleFinished()
            self.files = []
            return

        self.files.sort(pathCompare)

        for f in self.files:
            self.grepProcess.addFilename(f)
        self.files = []
        self.grepProcess.handleInputFinished()

    def handleGrepResult (self, filename, lineno, linetext):
        self.resultHandler.handleResult(filename, lineno, linetext)

    def handleGrepFinished (self):
        self.resultHandler.handleFinished()
        self.grepProcess = None

def pathCompare (p1, p2):
    "Sort path names (files before directories; alphabetically)"
    s1 = os.path.split(p1)
    s2 = os.path.split(p2)
    return cmp(s1, s2)

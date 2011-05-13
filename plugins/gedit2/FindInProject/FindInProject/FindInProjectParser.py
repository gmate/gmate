"""
    Parse the result of ack into html
"""

import os
import subprocess
import cgi
import re

class FindInProjectParser:

    def __init__(self, query, path, context=True, regex=False, ignorecase=False, filetype=None):
        if filetype:
            filetype = filetype.replace(' ', '').split(',')
        ack = ""
        if os.popen("which ack-grep").readlines():
            ack = "ack-grep"
        elif os.popen("which ack").readlines():
            ack = "ack"

        if ack:
            arg = [ack, '--color', '--color-filename=reset', '--color-match=yellow', query]
            if context:
                arg.extend(['-C', '2'])
            if not regex:
                arg.append('-Q')
            if ignorecase:
                arg.append('-i')
            if filetype:
                filetype = ['.' + f for f in filetype]
                arg.extend(['--type-set', 'custom=%s' % ','.join(filetype), '--type=custom'])
            process = subprocess.Popen(arg, stdout=subprocess.PIPE, cwd=path)
            self.raw = cgi.escape(process.communicate()[0])
            self.raw = self.raw.replace('\x1b[0m\x1b[K','')
        else:
            arg = ['grep', '-R', '-n', '-H', '-I', query, '.', '--color=force']
            if context:
                arg.extend(['-C', '2'])
            if regex:
                arg.append('-E')
            if ignorecase:
                arg.append('-i')
            if filetype:
                arg.extend(['--include=*.%s' % t for t in filetype])
            process = subprocess.Popen(arg, stdout=subprocess.PIPE, cwd=path,env={"GREP_COLORS": "ms=33:mc=01;31:sl=:cx=:fn=0:ln=:bn=32:se="})
            self.raw = cgi.escape(process.communicate()[0])
            self.raw = self.raw.replace('\x1b[K', '')
        self.filelist = []
        self.matches = 0

    def status(self):
        return (self.matches, len(self.filelist))

    def html(self):
        blocks = self.__tuple()
        result = ""
        if not blocks or len(blocks[0]) == 0:
            return result
        for block in blocks:
            table = """
<table>
    <colgroup class="line-number"></colgroup>
    <colgroup class="code"></colgroup>
    <thead onclick="javascript:toggle(this)">
        <tr>
            <td class="filename" colspan="2"><span class="open">&#9660;</span>&nbsp;%s</td>
        </tr>
    </thead>
    <tbody>
            """ % os.path.normpath(block[0][0])
            for line in block:
                matchclass = ""
                if line[2]:
                    matchclass = ' match'
                table += """
        <tr onclick="javascript:goto('%s', %s)">
            <td class="line-number%s">%s</td>
            <td class="code%s">%s</td>
        </tr>
                """ % (line[0], line[1], matchclass, line[1], matchclass, line[3])
            table += """
    </tbody>
</table>
            """
            result += table
        return result

    def __tuple(self):
        #\x1b[0mew\x1b[0m-64-
        #\x1b[0mew\x1b[0m-65-
        #\x1b[0mew\x1b[0m:66:if __name__ == "\x1b[33m__main__\x1b[0m":\x1b[0m\x1b[K
        #\x1b[0mew\x1b[0m-67-    Eastwind()
        #\x1b[0mew\x1b[0m-68-

        groups = re.split('(?<=\n)--\n', self.raw)
        if groups and len(groups) == 1:
            filename_hash = {}
            for l in groups[0].split('\n'):
                if not l:
                    continue
                meta = self.__metadata(l)
                if meta[0] in filename_hash:
                    filename_hash[meta[0]].append(meta)
                else:
                    filename_hash[meta[0]] = [meta]
            return [filename_hash[k] for k in filename_hash.keys()]
        else:
            return [[self.__metadata(l) for l in g.split('\n') if l != ''] for g in groups]

    def __metadata(self, line):
        match = re.match("^\\x1b\[0m(.*?)\\x1b\[0?m[:-](\d+)([:-])(.*)", line)
        matched = (match.group(3) == ':')
        clear = match.group(4).replace(' ', '&nbsp;')
        clear = re.sub("\\x1b\[33m(.*?)\\x1b\[0?m", '<span class="highlight">\\1</span>', clear)
        if matched:
            self.matches = self.matches + 1
        if not match.group(1) in self.filelist:
            self.filelist.append(match.group(1))
        return (match.group(1), match.group(2), matched, clear)


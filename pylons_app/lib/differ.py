# -*- coding: utf-8 -*-
# original copyright: 2007-2008 by Armin Ronacher
# licensed under the BSD license.

import re, difflib

def render_udiff(udiff, differ='udiff'):
    """Renders the udiff into multiple chunks of nice looking tables.
    The return value is a list of those tables.
    """
    return DiffProcessor(udiff, differ).prepare()

class DiffProcessor(object):
    """Give it a unified diff and it returns a list of the files that were
    mentioned in the diff together with a dict of meta information that
    can be used to render it in a HTML template.
    """
    _chunk_re = re.compile(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)')

    def __init__(self, udiff, differ):
        """
        :param udiff:   a text in udiff format
        """
        if isinstance(udiff, basestring):
            udiff = udiff.splitlines(1)
        
        self.lines = map(self.escaper, udiff)
        
        # Select a differ.
        if differ == 'difflib':
            self.differ = self._highlight_line_difflib
        else:
            self.differ = self._highlight_line_udiff
            

    def escaper(self, string):
        return string.replace('<', '&lt;').replace('>', '&gt;')

    def _extract_rev(self, line1, line2):
        """Extract the filename and revision hint from a line."""
        try:
            if line1.startswith('--- ') and line2.startswith('+++ '):
                filename, old_rev = line1[4:].split(None, 1)
                new_rev = line2[4:].split(None, 1)[1]
                return filename, 'old', 'new'
        except (ValueError, IndexError):
            pass
        return None, None, None

    def _highlight_line_difflib(self, line, next):
        """Highlight inline changes in both lines."""
        
        if line['action'] == 'del':
            old, new = line, next
        else:
            old, new = next, line
        
        oldwords = re.split(r'(\W)', old['line'])
        newwords = re.split(r'(\W)', new['line'])
        
        sequence = difflib.SequenceMatcher(None, oldwords, newwords)
        
        oldfragments, newfragments = [], []
        for tag, i1, i2, j1, j2 in sequence.get_opcodes():
            oldfrag = ''.join(oldwords[i1:i2])
            newfrag = ''.join(newwords[j1:j2])
            if tag != 'equal':
                if oldfrag:
                    oldfrag = '<del>%s</del>' % oldfrag
                if newfrag:
                    newfrag = '<ins>%s</ins>' % newfrag
            oldfragments.append(oldfrag)
            newfragments.append(newfrag)
        
        old['line'] = "".join(oldfragments)
        new['line'] = "".join(newfragments)

    def _highlight_line_udiff(self, line, next):
        """Highlight inline changes in both lines."""
        start = 0
        limit = min(len(line['line']), len(next['line']))
        while start < limit and line['line'][start] == next['line'][start]:
            start += 1
        end = -1
        limit -= start
        while - end <= limit and line['line'][end] == next['line'][end]:
            end -= 1
        end += 1
        if start or end:
            def do(l):
                last = end + len(l['line'])
                if l['action'] == 'add':
                    tag = 'ins'
                else:
                    tag = 'del'
                l['line'] = '%s<%s>%s</%s>%s' % (
                    l['line'][:start],
                    tag,
                    l['line'][start:last],
                    tag,
                    l['line'][last:]
                )
            do(line)
            do(next)

    def _parse_udiff(self):
        """Parse the diff an return data for the template."""
        lineiter = iter(self.lines)
        files = []
        try:
            line = lineiter.next()
            while 1:
                # continue until we found the old file
                if not line.startswith('--- '):
                    line = lineiter.next()
                    continue

                chunks = []
                filename, old_rev, new_rev = \
                    self._extract_rev(line, lineiter.next())
                files.append({
                    'filename':         filename,
                    'old_revision':     old_rev,
                    'new_revision':     new_rev,
                    'chunks':           chunks
                })

                line = lineiter.next()
                while line:
                    match = self._chunk_re.match(line)
                    if not match:
                        break

                    lines = []
                    chunks.append(lines)

                    old_line, old_end, new_line, new_end = \
                        [int(x or 1) for x in match.groups()[:-1]]
                    old_line -= 1
                    new_line -= 1
                    context = match.groups()[-1]
                    old_end += old_line
                    new_end += new_line

                    if context:
                        lines.append({
                            'old_lineno': None,
                            'new_lineno': None,
                            'action': 'context',
                            'line': line,
                        })

                    line = lineiter.next()

                    while old_line < old_end or new_line < new_end:
                        if line:
                            command, line = line[0], line[1:]
                        else:
                            command = ' '
                        affects_old = affects_new = False

                        # ignore those if we don't expect them
                        if command in '#@':
                            continue
                        elif command == '+':
                            affects_new = True
                            action = 'add'
                        elif command == '-':
                            affects_old = True
                            action = 'del'
                        else:
                            affects_old = affects_new = True
                            action = 'unmod'

                        old_line += affects_old
                        new_line += affects_new
                        lines.append({
                            'old_lineno':   affects_old and old_line or '',
                            'new_lineno':   affects_new and new_line or '',
                            'action':       action,
                            'line':         line
                        })
                        line = lineiter.next()

        except StopIteration:
            pass

        # highlight inline changes
        for file in files:
            for chunk in chunks:
                lineiter = iter(chunk)
                first = True
                try:
                    while 1:
                        line = lineiter.next()
                        if line['action'] != 'unmod':
                            nextline = lineiter.next()
                            if nextline['action'] == 'unmod' or \
                               nextline['action'] == line['action']:
                                continue
                            self.differ(line, nextline)
                except StopIteration:
                    pass

        return files

    def prepare(self):
        """Prepare the passed udiff for HTML rendering."""
        return self._parse_udiff()

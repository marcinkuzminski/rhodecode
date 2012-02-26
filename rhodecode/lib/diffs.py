# -*- coding: utf-8 -*-
"""
    rhodecode.lib.diffs
    ~~~~~~~~~~~~~~~~~~~

    Set of diffing helpers, previously part of vcs


    :created_on: Dec 4, 2011
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
    :original copyright: 2007-2008 by Armin Ronacher
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import difflib
import markupsafe
from itertools import tee, imap

from pylons.i18n.translation import _

from rhodecode.lib.vcs.exceptions import VCSError
from rhodecode.lib.vcs.nodes import FileNode

from rhodecode.lib.utils import EmptyChangeset


def wrap_to_table(str_):
    return '''<table class="code-difftable">
                <tr class="line no-comment">
                <td class="lineno new"></td>
                <td class="code no-comment"><pre>%s</pre></td>
                </tr>
              </table>''' % str_


def wrapped_diff(filenode_old, filenode_new, cut_off_limit=None,
                ignore_whitespace=True, line_context=3,
                enable_comments=False):
    """
    returns a wrapped diff into a table, checks for cut_off_limit and presents
    proper message
    """

    if filenode_old is None:
        filenode_old = FileNode(filenode_new.path, '', EmptyChangeset())

    if filenode_old.is_binary or filenode_new.is_binary:
        diff = wrap_to_table(_('binary file'))
        stats = (0, 0)
        size = 0

    elif cut_off_limit != -1 and (cut_off_limit is None or
    (filenode_old.size < cut_off_limit and filenode_new.size < cut_off_limit)):

        f_gitdiff = get_gitdiff(filenode_old, filenode_new,
                                ignore_whitespace=ignore_whitespace,
                                context=line_context)
        diff_processor = DiffProcessor(f_gitdiff, format='gitdiff')

        diff = diff_processor.as_html(enable_comments=enable_comments)
        stats = diff_processor.stat()
        size = len(diff or '')
    else:
        diff = wrap_to_table(_('Changeset was to big and was cut off, use '
                               'diff menu to display this diff'))
        stats = (0, 0)
        size = 0

    if not diff:
        diff = wrap_to_table(_('No changes detected'))

    cs1 = filenode_old.last_changeset.raw_id
    cs2 = filenode_new.last_changeset.raw_id

    return size, cs1, cs2, diff, stats


def get_gitdiff(filenode_old, filenode_new, ignore_whitespace=True, context=3):
    """
    Returns git style diff between given ``filenode_old`` and ``filenode_new``.

    :param ignore_whitespace: ignore whitespaces in diff
    """
    # make sure we pass in default context
    context = context or 3

    for filenode in (filenode_old, filenode_new):
        if not isinstance(filenode, FileNode):
            raise VCSError("Given object should be FileNode object, not %s"
                % filenode.__class__)

    repo = filenode_new.changeset.repository
    old_raw_id = getattr(filenode_old.changeset, 'raw_id', repo.EMPTY_CHANGESET)
    new_raw_id = getattr(filenode_new.changeset, 'raw_id', repo.EMPTY_CHANGESET)

    vcs_gitdiff = repo.get_diff(old_raw_id, new_raw_id, filenode_new.path,
                                 ignore_whitespace, context)

    return vcs_gitdiff


class DiffProcessor(object):
    """
    Give it a unified diff and it returns a list of the files that were
    mentioned in the diff together with a dict of meta information that
    can be used to render it in a HTML template.
    """
    _chunk_re = re.compile(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)')

    def __init__(self, diff, differ='diff', format='udiff'):
        """
        :param diff:   a text in diff format or generator
        :param format: format of diff passed, `udiff` or `gitdiff`
        """
        if isinstance(diff, basestring):
            diff = [diff]

        self.__udiff = diff
        self.__format = format
        self.adds = 0
        self.removes = 0

        if isinstance(self.__udiff, basestring):
            self.lines = iter(self.__udiff.splitlines(1))

        elif self.__format == 'gitdiff':
            udiff_copy = self.copy_iterator()
            self.lines = imap(self.escaper, self._parse_gitdiff(udiff_copy))
        else:
            udiff_copy = self.copy_iterator()
            self.lines = imap(self.escaper, udiff_copy)

        # Select a differ.
        if differ == 'difflib':
            self.differ = self._highlight_line_difflib
        else:
            self.differ = self._highlight_line_udiff

    def escaper(self, string):
        return markupsafe.escape(string)

    def copy_iterator(self):
        """
        make a fresh copy of generator, we should not iterate thru
        an original as it's needed for repeating operations on
        this instance of DiffProcessor
        """
        self.__udiff, iterator_copy = tee(self.__udiff)
        return iterator_copy

    def _extract_rev(self, line1, line2):
        """
        Extract the filename and revision hint from a line.
        """

        try:
            if line1.startswith('--- ') and line2.startswith('+++ '):
                l1 = line1[4:].split(None, 1)
                old_filename = (l1[0].replace('a/', '', 1)
                                if len(l1) >= 1 else None)
                old_rev = l1[1] if len(l1) == 2 else 'old'

                l2 = line2[4:].split(None, 1)
                new_filename = (l2[0].replace('b/', '', 1)
                                if len(l1) >= 1 else None)
                new_rev = l2[1] if len(l2) == 2 else 'new'

                filename = (old_filename
                            if old_filename != '/dev/null' else new_filename)

                return filename, new_rev, old_rev
        except (ValueError, IndexError):
            pass

        return None, None, None

    def _parse_gitdiff(self, diffiterator):
        def line_decoder(l):
            if l.startswith('+') and not l.startswith('+++'):
                self.adds += 1
            elif l.startswith('-') and not l.startswith('---'):
                self.removes += 1
            return l.decode('utf8', 'replace')

        output = list(diffiterator)
        size = len(output)

        if size == 2:
            l = []
            l.extend([output[0]])
            l.extend(output[1].splitlines(1))
            return map(line_decoder, l)
        elif size == 1:
            return  map(line_decoder, output[0].splitlines(1))
        elif size == 0:
            return []

        raise Exception('wrong size of diff %s' % size)

    def _highlight_line_difflib(self, line, next_):
        """
        Highlight inline changes in both lines.
        """

        if line['action'] == 'del':
            old, new = line, next_
        else:
            old, new = next_, line

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

    def _highlight_line_udiff(self, line, next_):
        """
        Highlight inline changes in both lines.
        """
        start = 0
        limit = min(len(line['line']), len(next_['line']))
        while start < limit and line['line'][start] == next_['line'][start]:
            start += 1
        end = -1
        limit -= start
        while -end <= limit and line['line'][end] == next_['line'][end]:
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
            do(next_)

    def _parse_udiff(self):
        """
        Parse the diff an return data for the template.
        """
        lineiter = self.lines
        files = []
        try:
            line = lineiter.next()
            # skip first context
            skipfirst = True
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
                    context = len(match.groups()) == 5
                    old_end += old_line
                    new_end += new_line

                    if context:
                        if not skipfirst:
                            lines.append({
                                'old_lineno': '...',
                                'new_lineno': '...',
                                'action':     'context',
                                'line':       line,
                            })
                        else:
                            skipfirst = False

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
        for _ in files:
            for chunk in chunks:
                lineiter = iter(chunk)
                #first = True
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
        """
        Prepare the passed udiff for HTML rendering. It'l return a list
        of dicts
        """
        return self._parse_udiff()

    def _safe_id(self, idstring):
        """Make a string safe for including in an id attribute.

        The HTML spec says that id attributes 'must begin with
        a letter ([A-Za-z]) and may be followed by any number
        of letters, digits ([0-9]), hyphens ("-"), underscores
        ("_"), colons (":"), and periods (".")'. These regexps
        are slightly over-zealous, in that they remove colons
        and periods unnecessarily.

        Whitespace is transformed into underscores, and then
        anything which is not a hyphen or a character that
        matches \w (alphanumerics and underscore) is removed.

        """
        # Transform all whitespace to underscore
        idstring = re.sub(r'\s', "_", '%s' % idstring)
        # Remove everything that is not a hyphen or a member of \w
        idstring = re.sub(r'(?!-)\W', "", idstring).lower()
        return idstring

    def raw_diff(self):
        """
        Returns raw string as udiff
        """
        udiff_copy = self.copy_iterator()
        if self.__format == 'gitdiff':
            udiff_copy = self._parse_gitdiff(udiff_copy)
        return u''.join(udiff_copy)

    def as_html(self, table_class='code-difftable', line_class='line',
                new_lineno_class='lineno old', old_lineno_class='lineno new',
                code_class='code', enable_comments=False):
        """
        Return udiff as html table with customized css classes
        """
        def _link_to_if(condition, label, url):
            """
            Generates a link if condition is meet or just the label if not.
            """

            if condition:
                return '''<a href="%(url)s">%(label)s</a>''' % {
                    'url': url,
                    'label': label
                }
            else:
                return label
        diff_lines = self.prepare()
        _html_empty = True
        _html = []
        _html.append('''<table class="%(table_class)s">\n''' % {
            'table_class': table_class
        })
        for diff in diff_lines:
            for line in diff['chunks']:
                _html_empty = False
                for change in line:
                    _html.append('''<tr class="%(lc)s %(action)s">\n''' % {
                        'lc': line_class,
                        'action': change['action']
                    })
                    anchor_old_id = ''
                    anchor_new_id = ''
                    anchor_old = "%(filename)s_o%(oldline_no)s" % {
                        'filename': self._safe_id(diff['filename']),
                        'oldline_no': change['old_lineno']
                    }
                    anchor_new = "%(filename)s_n%(oldline_no)s" % {
                        'filename': self._safe_id(diff['filename']),
                        'oldline_no': change['new_lineno']
                    }
                    cond_old = (change['old_lineno'] != '...' and
                                change['old_lineno'])
                    cond_new = (change['new_lineno'] != '...' and
                                change['new_lineno'])
                    if cond_old:
                        anchor_old_id = 'id="%s"' % anchor_old
                    if cond_new:
                        anchor_new_id = 'id="%s"' % anchor_new
                    ###########################################################
                    # OLD LINE NUMBER
                    ###########################################################
                    _html.append('''\t<td %(a_id)s class="%(olc)s">''' % {
                        'a_id': anchor_old_id,
                        'olc': old_lineno_class
                    })

                    _html.append('''%(link)s''' % {
                        'link': _link_to_if(True, change['old_lineno'],
                                            '#%s' % anchor_old)
                    })
                    _html.append('''</td>\n''')
                    ###########################################################
                    # NEW LINE NUMBER
                    ###########################################################

                    _html.append('''\t<td %(a_id)s class="%(nlc)s">''' % {
                        'a_id': anchor_new_id,
                        'nlc': new_lineno_class
                    })

                    _html.append('''%(link)s''' % {
                        'link': _link_to_if(True, change['new_lineno'],
                                            '#%s' % anchor_new)
                    })
                    _html.append('''</td>\n''')
                    ###########################################################
                    # CODE
                    ###########################################################
                    comments = '' if enable_comments else 'no-comment'
                    _html.append('''\t<td class="%(cc)s %(inc)s">''' % {
                        'cc': code_class,
                        'inc': comments
                    })
                    _html.append('''\n\t\t<pre>%(code)s</pre>\n''' % {
                        'code': change['line']
                    })
                    _html.append('''\t</td>''')
                    _html.append('''\n</tr>\n''')
        _html.append('''</table>''')
        if _html_empty:
            return None
        return ''.join(_html)

    def stat(self):
        """
        Returns tuple of added, and removed lines for this instance
        """
        return self.adds, self.removes

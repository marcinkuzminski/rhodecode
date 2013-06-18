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
import logging

from itertools import tee, imap

from pylons.i18n.translation import _

from rhodecode.lib.vcs.exceptions import VCSError
from rhodecode.lib.vcs.nodes import FileNode, SubModuleNode
from rhodecode.lib.vcs.backends.base import EmptyChangeset
from rhodecode.lib.helpers import escape
from rhodecode.lib.utils2 import safe_unicode, safe_str

log = logging.getLogger(__name__)


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
        diff = wrap_to_table(_('Binary file'))
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
        diff = wrap_to_table(_('Changeset was too big and was cut off, use '
                               'diff menu to display this diff'))
        stats = (0, 0)
        size = 0
    if not diff:
        submodules = filter(lambda o: isinstance(o, SubModuleNode),
                            [filenode_new, filenode_old])
        if submodules:
            diff = wrap_to_table(escape('Submodule %r' % submodules[0]))
        else:
            diff = wrap_to_table(_('No changes detected'))

    cs1 = filenode_old.changeset.raw_id
    cs2 = filenode_new.changeset.raw_id

    return size, cs1, cs2, diff, stats


def get_gitdiff(filenode_old, filenode_new, ignore_whitespace=True, context=3):
    """
    Returns git style diff between given ``filenode_old`` and ``filenode_new``.

    :param ignore_whitespace: ignore whitespaces in diff
    """
    # make sure we pass in default context
    context = context or 3
    submodules = filter(lambda o: isinstance(o, SubModuleNode),
                        [filenode_new, filenode_old])
    if submodules:
        return ''

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

NEW_FILENODE = 1
DEL_FILENODE = 2
MOD_FILENODE = 3
RENAMED_FILENODE = 4
COPIED_FILENODE = 5
CHMOD_FILENODE = 6
BIN_FILENODE = 7


class DiffLimitExceeded(Exception):
    pass


class LimitedDiffContainer(object):

    def __init__(self, diff_limit, cur_diff_size, diff):
        self.diff = diff
        self.diff_limit = diff_limit
        self.cur_diff_size = cur_diff_size

    def __iter__(self):
        for l in self.diff:
            yield l


class DiffProcessor(object):
    """
    Give it a unified or git diff and it returns a list of the files that were
    mentioned in the diff together with a dict of meta information that
    can be used to render it in a HTML template.
    """
    _chunk_re = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)')
    _newline_marker = re.compile(r'^\\ No newline at end of file')
    _git_header_re = re.compile(r"""
        #^diff[ ]--git
            [ ]a/(?P<a_path>.+?)[ ]b/(?P<b_path>.+?)\n
        (?:^similarity[ ]index[ ](?P<similarity_index>\d+)%\n
           ^rename[ ]from[ ](?P<rename_from>\S+)\n
           ^rename[ ]to[ ](?P<rename_to>\S+)(?:\n|$))?
        (?:^old[ ]mode[ ](?P<old_mode>\d+)\n
           ^new[ ]mode[ ](?P<new_mode>\d+)(?:\n|$))?
        (?:^new[ ]file[ ]mode[ ](?P<new_file_mode>.+)(?:\n|$))?
        (?:^deleted[ ]file[ ]mode[ ](?P<deleted_file_mode>.+)(?:\n|$))?
        (?:^index[ ](?P<a_blob_id>[0-9A-Fa-f]+)
            \.\.(?P<b_blob_id>[0-9A-Fa-f]+)[ ]?(?P<b_mode>.+)?(?:\n|$))?
        (?:^(?P<bin_patch>GIT[ ]binary[ ]patch)(?:\n|$))?
        (?:^---[ ](a/(?P<a_file>.+)|/dev/null)(?:\n|$))?
        (?:^\+\+\+[ ](b/(?P<b_file>.+)|/dev/null)(?:\n|$))?
    """, re.VERBOSE | re.MULTILINE)
    _hg_header_re = re.compile(r"""
        #^diff[ ]--git
            [ ]a/(?P<a_path>.+?)[ ]b/(?P<b_path>.+?)\n
        (?:^old[ ]mode[ ](?P<old_mode>\d+)\n
           ^new[ ]mode[ ](?P<new_mode>\d+)(?:\n|$))?
        (?:^similarity[ ]index[ ](?P<similarity_index>\d+)%(?:\n|$))?
        (?:^rename[ ]from[ ](?P<rename_from>\S+)\n
           ^rename[ ]to[ ](?P<rename_to>\S+)(?:\n|$))?
        (?:^copy[ ]from[ ](?P<copy_from>\S+)\n
           ^copy[ ]to[ ](?P<copy_to>\S+)(?:\n|$))?
        (?:^new[ ]file[ ]mode[ ](?P<new_file_mode>.+)(?:\n|$))?
        (?:^deleted[ ]file[ ]mode[ ](?P<deleted_file_mode>.+)(?:\n|$))?
        (?:^index[ ](?P<a_blob_id>[0-9A-Fa-f]+)
            \.\.(?P<b_blob_id>[0-9A-Fa-f]+)[ ]?(?P<b_mode>.+)?(?:\n|$))?
        (?:^(?P<bin_patch>GIT[ ]binary[ ]patch)(?:\n|$))?
        (?:^---[ ](a/(?P<a_file>.+)|/dev/null)(?:\n|$))?
        (?:^\+\+\+[ ](b/(?P<b_file>.+)|/dev/null)(?:\n|$))?
    """, re.VERBOSE | re.MULTILINE)

    #used for inline highlighter word split
    _token_re = re.compile(r'()(&gt;|&lt;|&amp;|\W+?)')

    def __init__(self, diff, vcs='hg', format='gitdiff', diff_limit=None):
        """
        :param diff:   a text in diff format
        :param vcs: type of version controll hg or git
        :param format: format of diff passed, `udiff` or `gitdiff`
        :param diff_limit: define the size of diff that is considered "big"
            based on that parameter cut off will be triggered, set to None
            to show full diff
        """
        if not isinstance(diff, basestring):
            raise Exception('Diff must be a basestring got %s instead' % type(diff))

        self._diff = diff
        self._format = format
        self.adds = 0
        self.removes = 0
        # calculate diff size
        self.diff_size = len(diff)
        self.diff_limit = diff_limit
        self.cur_diff_size = 0
        self.parsed = False
        self.parsed_diff = []
        self.vcs = vcs

        if format == 'gitdiff':
            self.differ = self._highlight_line_difflib
            self._parser = self._parse_gitdiff
        else:
            self.differ = self._highlight_line_udiff
            self._parser = self._parse_udiff

    def _copy_iterator(self):
        """
        make a fresh copy of generator, we should not iterate thru
        an original as it's needed for repeating operations on
        this instance of DiffProcessor
        """
        self.__udiff, iterator_copy = tee(self.__udiff)
        return iterator_copy

    def _escaper(self, string):
        """
        Escaper for diff escapes special chars and checks the diff limit

        :param string:
        """

        self.cur_diff_size += len(string)

        # escaper get's iterated on each .next() call and it checks if each
        # parsed line doesn't exceed the diff limit
        if self.diff_limit is not None and self.cur_diff_size > self.diff_limit:
            raise DiffLimitExceeded('Diff Limit Exceeded')

        return safe_unicode(string).replace('&', '&amp;')\
                .replace('<', '&lt;')\
                .replace('>', '&gt;')

    def _line_counter(self, l):
        """
        Checks each line and bumps total adds/removes for this diff

        :param l:
        """
        if l.startswith('+') and not l.startswith('+++'):
            self.adds += 1
        elif l.startswith('-') and not l.startswith('---'):
            self.removes += 1
        return safe_unicode(l)

    def _highlight_line_difflib(self, line, next_):
        """
        Highlight inline changes in both lines.
        """

        if line['action'] == 'del':
            old, new = line, next_
        else:
            old, new = next_, line

        oldwords = self._token_re.split(old['line'])
        newwords = self._token_re.split(new['line'])
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

    def _get_header(self, diff_chunk):
        """
        parses the diff header, and returns parts, and leftover diff
        parts consists of 14 elements::

            a_path, b_path, similarity_index, rename_from, rename_to,
            old_mode, new_mode, new_file_mode, deleted_file_mode,
            a_blob_id, b_blob_id, b_mode, a_file, b_file

        :param diff_chunk:
        """

        if self.vcs == 'git':
            match = self._git_header_re.match(diff_chunk)
            diff = diff_chunk[match.end():]
            return match.groupdict(), imap(self._escaper, diff.splitlines(1))
        elif self.vcs == 'hg':
            match = self._hg_header_re.match(diff_chunk)
            diff = diff_chunk[match.end():]
            return match.groupdict(), imap(self._escaper, diff.splitlines(1))
        else:
            raise Exception('VCS type %s is not supported' % self.vcs)

    def _clean_line(self, line, command):
        if command in ['+', '-', ' ']:
            #only modify the line if it's actually a diff thing
            line = line[1:]
        return line

    def _parse_gitdiff(self, inline_diff=True):
        _files = []
        diff_container = lambda arg: arg

        ##split the diff in chunks of separate --git a/file b/file chunks
        for raw_diff in ('\n' + self._diff).split('\ndiff --git')[1:]:
            head, diff = self._get_header(raw_diff)

            op = None
            stats = {
                'added': 0,
                'deleted': 0,
                'binary': False,
                'ops': {},
            }

            if head['deleted_file_mode']:
                op = 'D'
                stats['binary'] = True
                stats['ops'][DEL_FILENODE] = 'deleted file'

            elif head['new_file_mode']:
                op = 'A'
                stats['binary'] = True
                stats['ops'][NEW_FILENODE] = 'new file %s' % head['new_file_mode']
            else:  # modify operation, can be cp, rename, chmod
                # CHMOD
                if head['new_mode'] and head['old_mode']:
                    op = 'M'
                    stats['binary'] = True
                    stats['ops'][CHMOD_FILENODE] = ('modified file chmod %s => %s'
                                        % (head['old_mode'], head['new_mode']))
                # RENAME
                if (head['rename_from'] and head['rename_to']
                      and head['rename_from'] != head['rename_to']):
                    op = 'M'
                    stats['binary'] = True
                    stats['ops'][RENAMED_FILENODE] = ('file renamed from %s to %s'
                                    % (head['rename_from'], head['rename_to']))
                # COPY
                if head.get('copy_from') and head.get('copy_to'):
                    op = 'M'
                    stats['binary'] = True
                    stats['ops'][COPIED_FILENODE] = ('file copied from %s to %s'
                                        % (head['copy_from'], head['copy_to']))
                # FALL BACK: detect missed old style add or remove
                if op is None:
                    if not head['a_file'] and head['b_file']:
                        op = 'A'
                        stats['binary'] = True
                        stats['ops'][NEW_FILENODE] = 'new file'

                    elif head['a_file'] and not head['b_file']:
                        op = 'D'
                        stats['binary'] = True
                        stats['ops'][DEL_FILENODE] = 'deleted file'

                # it's not ADD not DELETE
                if op is None:
                    op = 'M'
                    stats['binary'] = True
                    stats['ops'][MOD_FILENODE] = 'modified file'

            # a real non-binary diff
            if head['a_file'] or head['b_file']:
                try:
                    chunks, _stats = self._parse_lines(diff)
                    stats['binary'] = False
                    stats['added'] = _stats[0]
                    stats['deleted'] = _stats[1]
                    # explicit mark that it's a modified file
                    if op == 'M':
                        stats['ops'][MOD_FILENODE] = 'modified file'

                except DiffLimitExceeded:
                    diff_container = lambda _diff: \
                        LimitedDiffContainer(self.diff_limit,
                                            self.cur_diff_size, _diff)
                    break
            else:  # GIT binary patch (or empty diff)
                # GIT Binary patch
                if head['bin_patch']:
                    stats['ops'][BIN_FILENODE] = 'binary diff not shown'
                chunks = []

            chunks.insert(0, [{
                'old_lineno': '',
                'new_lineno': '',
                'action':     'context',
                'line':       msg,
                } for _op, msg in stats['ops'].iteritems()
                  if _op not in [MOD_FILENODE]])

            _files.append({
                'filename':         head['b_path'],
                'old_revision':     head['a_blob_id'],
                'new_revision':     head['b_blob_id'],
                'chunks':           chunks,
                'operation':        op,
                'stats':            stats,
            })

        sorter = lambda info: {'A': 0, 'M': 1, 'D': 2}.get(info['operation'])

        if not inline_diff:
            return diff_container(sorted(_files, key=sorter))

        # highlight inline changes
        for diff_data in _files:
            for chunk in diff_data['chunks']:
                lineiter = iter(chunk)
                try:
                    while 1:
                        line = lineiter.next()
                        if line['action'] not in ['unmod', 'context']:
                            nextline = lineiter.next()
                            if nextline['action'] in ['unmod', 'context'] or \
                               nextline['action'] == line['action']:
                                continue
                            self.differ(line, nextline)
                except StopIteration:
                    pass

        return diff_container(sorted(_files, key=sorter))

    def _parse_udiff(self, inline_diff=True):
        raise NotImplementedError()

    def _parse_lines(self, diff):
        """
        Parse the diff an return data for the template.
        """

        lineiter = iter(diff)
        stats = [0, 0]

        try:
            chunks = []
            line = lineiter.next()

            while line:
                lines = []
                chunks.append(lines)

                match = self._chunk_re.match(line)

                if not match:
                    break

                gr = match.groups()
                (old_line, old_end,
                 new_line, new_end) = [int(x or 1) for x in gr[:-1]]
                old_line -= 1
                new_line -= 1

                context = len(gr) == 5
                old_end += old_line
                new_end += new_line

                if context:
                    # skip context only if it's first line
                    if int(gr[0]) > 1:
                        lines.append({
                            'old_lineno': '...',
                            'new_lineno': '...',
                            'action':     'context',
                            'line':       line,
                        })

                line = lineiter.next()

                while old_line < old_end or new_line < new_end:
                    command = ' '
                    if line:
                        command = line[0]

                    affects_old = affects_new = False

                    # ignore those if we don't expect them
                    if command in '#@':
                        continue
                    elif command == '+':
                        affects_new = True
                        action = 'add'
                        stats[0] += 1
                    elif command == '-':
                        affects_old = True
                        action = 'del'
                        stats[1] += 1
                    else:
                        affects_old = affects_new = True
                        action = 'unmod'

                    if not self._newline_marker.match(line):
                        old_line += affects_old
                        new_line += affects_new
                        lines.append({
                            'old_lineno':   affects_old and old_line or '',
                            'new_lineno':   affects_new and new_line or '',
                            'action':       action,
                            'line':         self._clean_line(line, command)
                        })

                    line = lineiter.next()

                    if self._newline_marker.match(line):
                        # we need to append to lines, since this is not
                        # counted in the line specs of diff
                        lines.append({
                            'old_lineno':   '...',
                            'new_lineno':   '...',
                            'action':       'context',
                            'line':         self._clean_line(line, command)
                        })

        except StopIteration:
            pass
        return chunks, stats

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

    def prepare(self, inline_diff=True):
        """
        Prepare the passed udiff for HTML rendering. It'l return a list
        of dicts with diff information
        """
        parsed = self._parser(inline_diff=inline_diff)
        self.parsed = True
        self.parsed_diff = parsed
        return parsed

    def as_raw(self, diff_lines=None):
        """
        Returns raw string diff
        """
        return self._diff
        #return u''.join(imap(self._line_counter, self._diff.splitlines(1)))

    def as_html(self, table_class='code-difftable', line_class='line',
                old_lineno_class='lineno old', new_lineno_class='lineno new',
                code_class='code', enable_comments=False, parsed_lines=None):
        """
        Return given diff as html table with customized css classes
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
        if not self.parsed:
            self.prepare()

        diff_lines = self.parsed_diff
        if parsed_lines:
            diff_lines = parsed_lines

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

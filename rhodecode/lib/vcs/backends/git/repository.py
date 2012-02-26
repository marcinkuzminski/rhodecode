# -*- coding: utf-8 -*-
"""
    vcs.backends.git
    ~~~~~~~~~~~~~~~~

    Git backend implementation.

    :created_on: Apr 8, 2010
    :copyright: (c) 2010-2011 by Marcin Kuzminski, Lukasz Balcerzak.
"""

import os
import re
import time
import posixpath
from dulwich.repo import Repo, NotGitRepository
#from dulwich.config import ConfigFile
from string import Template
from subprocess import Popen, PIPE
from rhodecode.lib.vcs.backends.base import BaseRepository
from rhodecode.lib.vcs.exceptions import BranchDoesNotExistError
from rhodecode.lib.vcs.exceptions import ChangesetDoesNotExistError
from rhodecode.lib.vcs.exceptions import EmptyRepositoryError
from rhodecode.lib.vcs.exceptions import RepositoryError
from rhodecode.lib.vcs.exceptions import TagAlreadyExistError
from rhodecode.lib.vcs.exceptions import TagDoesNotExistError
from rhodecode.lib.vcs.utils import safe_unicode, makedate, date_fromtimestamp
from rhodecode.lib.vcs.utils.lazy import LazyProperty
from rhodecode.lib.vcs.utils.ordered_dict import OrderedDict
from rhodecode.lib.vcs.utils.paths import abspath
from rhodecode.lib.vcs.utils.paths import get_user_home
from .workdir import GitWorkdir
from .changeset import GitChangeset
from .inmemory import GitInMemoryChangeset
from .config import ConfigFile


class GitRepository(BaseRepository):
    """
    Git repository backend.
    """
    DEFAULT_BRANCH_NAME = 'master'
    scm = 'git'

    def __init__(self, repo_path, create=False, src_url=None,
                 update_after_clone=False, bare=False):

        self.path = abspath(repo_path)
        self._repo = self._get_repo(create, src_url, update_after_clone, bare)
        try:
            self.head = self._repo.head()
        except KeyError:
            self.head = None

        self._config_files = [
            bare and abspath(self.path, 'config') or abspath(self.path, '.git',
                'config'),
            abspath(get_user_home(), '.gitconfig'),
        ]

    @LazyProperty
    def revisions(self):
        """
        Returns list of revisions' ids, in ascending order.  Being lazy
        attribute allows external tools to inject shas from cache.
        """
        return self._get_all_revisions()

    def run_git_command(self, cmd):
        """
        Runs given ``cmd`` as git command and returns tuple
        (returncode, stdout, stderr).

        .. note::
           This method exists only until log/blame functionality is implemented
           at Dulwich (see https://bugs.launchpad.net/bugs/645142). Parsing
           os command's output is road to hell...

        :param cmd: git command to be executed
        """
        #cmd = '(cd %s && git %s)' % (self.path, cmd)
        if isinstance(cmd, basestring):
            cmd = 'git %s' % cmd
        else:
            cmd = ['git'] + cmd
        try:
            opts = dict(
                shell=isinstance(cmd, basestring),
                stdout=PIPE,
                stderr=PIPE)
            if os.path.isdir(self.path):
                opts['cwd'] = self.path
            p = Popen(cmd, **opts)
        except OSError, err:
            raise RepositoryError("Couldn't run git command (%s).\n"
                "Original error was:%s" % (cmd, err))
        so, se = p.communicate()
        if not se.startswith("fatal: bad default revision 'HEAD'") and \
            p.returncode != 0:
            raise RepositoryError("Couldn't run git command (%s).\n"
                "stderr:\n%s" % (cmd, se))
        return so, se

    def _check_url(self, url):
        """
        Functon will check given url and try to verify if it's a valid
        link. Sometimes it may happened that mercurial will issue basic
        auth request that can cause whole API to hang when used from python
        or other external calls.

        On failures it'll raise urllib2.HTTPError
        """

        #TODO: implement this
        pass

    def _get_repo(self, create, src_url=None, update_after_clone=False,
            bare=False):
        if create and os.path.exists(self.path):
            raise RepositoryError("Location already exist")
        if src_url and not create:
            raise RepositoryError("Create should be set to True if src_url is "
                                  "given (clone operation creates repository)")
        try:
            if create and src_url:
                self._check_url(src_url)
                self.clone(src_url, update_after_clone, bare)
                return Repo(self.path)
            elif create:
                os.mkdir(self.path)
                if bare:
                    return Repo.init_bare(self.path)
                else:
                    return Repo.init(self.path)
            else:
                return Repo(self.path)
        except (NotGitRepository, OSError), err:
            raise RepositoryError(err)

    def _get_all_revisions(self):
        cmd = 'rev-list --all --date-order'
        try:
            so, se = self.run_git_command(cmd)
        except RepositoryError:
            # Can be raised for empty repositories
            return []
        revisions = so.splitlines()
        revisions.reverse()
        return revisions

    def _get_revision(self, revision):
        """
        For git backend we always return integer here. This way we ensure
        that changset's revision attribute would become integer.
        """
        pattern = re.compile(r'^[[0-9a-fA-F]{12}|[0-9a-fA-F]{40}]$')
        is_bstr = lambda o: isinstance(o, (str, unicode))
        is_null = lambda o: len(o) == revision.count('0')

        if len(self.revisions) == 0:
            raise EmptyRepositoryError("There are no changesets yet")

        if revision in (None, '', 'tip', 'HEAD', 'head', -1):
            revision = self.revisions[-1]

        if ((is_bstr(revision) and revision.isdigit() and len(revision) < 12)
            or isinstance(revision, int) or is_null(revision)):
            try:
                revision = self.revisions[int(revision)]
            except:
                raise ChangesetDoesNotExistError("Revision %r does not exist "
                    "for this repository %s" % (revision, self))

        elif is_bstr(revision):
            if not pattern.match(revision) or revision not in self.revisions:
                raise ChangesetDoesNotExistError("Revision %r does not exist "
                    "for this repository %s" % (revision, self))

        # Ensure we return full id
        if not pattern.match(str(revision)):
            raise ChangesetDoesNotExistError("Given revision %r not recognized"
                % revision)
        return revision

    def _get_archives(self, archive_name='tip'):

        for i in [('zip', '.zip'), ('gz', '.tar.gz'), ('bz2', '.tar.bz2')]:
                yield {"type": i[0], "extension": i[1], "node": archive_name}

    def _get_url(self, url):
        """
        Returns normalized url. If schema is not given, would fall to
        filesystem (``file:///``) schema.
        """
        url = str(url)
        if url != 'default' and not '://' in url:
            url = ':///'.join(('file', url))
        return url

    @LazyProperty
    def name(self):
        return os.path.basename(self.path)

    @LazyProperty
    def last_change(self):
        """
        Returns last change made on this repository as datetime object
        """
        return date_fromtimestamp(self._get_mtime(), makedate()[1])

    def _get_mtime(self):
        try:
            return time.mktime(self.get_changeset().date.timetuple())
        except RepositoryError:
            # fallback to filesystem
            in_path = os.path.join(self.path, '.git', "index")
            he_path = os.path.join(self.path, '.git', "HEAD")
            if os.path.exists(in_path):
                return os.stat(in_path).st_mtime
            else:
                return os.stat(he_path).st_mtime

    @LazyProperty
    def description(self):
        undefined_description = u'unknown'
        description_path = os.path.join(self.path, '.git', 'description')
        if os.path.isfile(description_path):
            return safe_unicode(open(description_path).read())
        else:
            return undefined_description

    @LazyProperty
    def contact(self):
        undefined_contact = u'Unknown'
        return undefined_contact

    @property
    def branches(self):
        if not self.revisions:
            return {}
        refs = self._repo.refs.as_dict()
        sortkey = lambda ctx: ctx[0]
        _branches = [('/'.join(ref.split('/')[2:]), head)
            for ref, head in refs.items()
            if ref.startswith('refs/heads/') or
            ref.startswith('refs/remotes/') and not ref.endswith('/HEAD')]
        return OrderedDict(sorted(_branches, key=sortkey, reverse=False))

    def _get_tags(self):
        if not self.revisions:
            return {}
        sortkey = lambda ctx: ctx[0]
        _tags = [('/'.join(ref.split('/')[2:]), head) for ref, head in
            self._repo.get_refs().items() if ref.startswith('refs/tags/')]
        return OrderedDict(sorted(_tags, key=sortkey, reverse=True))

    @LazyProperty
    def tags(self):
        return self._get_tags()

    def tag(self, name, user, revision=None, message=None, date=None,
            **kwargs):
        """
        Creates and returns a tag for the given ``revision``.

        :param name: name for new tag
        :param user: full username, i.e.: "Joe Doe <joe.doe@example.com>"
        :param revision: changeset id for which new tag would be created
        :param message: message of the tag's commit
        :param date: date of tag's commit

        :raises TagAlreadyExistError: if tag with same name already exists
        """
        if name in self.tags:
            raise TagAlreadyExistError("Tag %s already exists" % name)
        changeset = self.get_changeset(revision)
        message = message or "Added tag %s for commit %s" % (name,
            changeset.raw_id)
        self._repo.refs["refs/tags/%s" % name] = changeset._commit.id

        self.tags = self._get_tags()
        return changeset

    def remove_tag(self, name, user, message=None, date=None):
        """
        Removes tag with the given ``name``.

        :param name: name of the tag to be removed
        :param user: full username, i.e.: "Joe Doe <joe.doe@example.com>"
        :param message: message of the tag's removal commit
        :param date: date of tag's removal commit

        :raises TagDoesNotExistError: if tag with given name does not exists
        """
        if name not in self.tags:
            raise TagDoesNotExistError("Tag %s does not exist" % name)
        tagpath = posixpath.join(self._repo.refs.path, 'refs', 'tags', name)
        try:
            os.remove(tagpath)
            self.tags = self._get_tags()
        except OSError, e:
            raise RepositoryError(e.strerror)

    def get_changeset(self, revision=None):
        """
        Returns ``GitChangeset`` object representing commit from git repository
        at the given revision or head (most recent commit) if None given.
        """
        if isinstance(revision, GitChangeset):
            return revision
        revision = self._get_revision(revision)
        changeset = GitChangeset(repository=self, revision=revision)
        return changeset

    def get_changesets(self, start=None, end=None, start_date=None,
           end_date=None, branch_name=None, reverse=False):
        """
        Returns iterator of ``GitChangeset`` objects from start to end (both
        are inclusive), in ascending date order (unless ``reverse`` is set).

        :param start: changeset ID, as str; first returned changeset
        :param end: changeset ID, as str; last returned changeset
        :param start_date: if specified, changesets with commit date less than
          ``start_date`` would be filtered out from returned set
        :param end_date: if specified, changesets with commit date greater than
          ``end_date`` would be filtered out from returned set
        :param branch_name: if specified, changesets not reachable from given
          branch would be filtered out from returned set
        :param reverse: if ``True``, returned generator would be reversed
          (meaning that returned changesets would have descending date order)

        :raise BranchDoesNotExistError: If given ``branch_name`` does not
            exist.
        :raise ChangesetDoesNotExistError: If changeset for given ``start`` or
          ``end`` could not be found.

        """
        if branch_name and branch_name not in self.branches:
            raise BranchDoesNotExistError("Branch '%s' not found" \
                                          % branch_name)
        # %H at format means (full) commit hash, initial hashes are retrieved
        # in ascending date order
        cmd_template = 'log --date-order --reverse --pretty=format:"%H"'
        cmd_params = {}
        if start_date:
            cmd_template += ' --since "$since"'
            cmd_params['since'] = start_date.strftime('%m/%d/%y %H:%M:%S')
        if end_date:
            cmd_template += ' --until "$until"'
            cmd_params['until'] = end_date.strftime('%m/%d/%y %H:%M:%S')
        if branch_name:
            cmd_template += ' $branch_name'
            cmd_params['branch_name'] = branch_name
        else:
            cmd_template += ' --all'

        cmd = Template(cmd_template).safe_substitute(**cmd_params)
        revs = self.run_git_command(cmd)[0].splitlines()
        start_pos = 0
        end_pos = len(revs)
        if start:
            _start = self._get_revision(start)
            try:
                start_pos = revs.index(_start)
            except ValueError:
                pass

        if end is not None:
            _end = self._get_revision(end)
            try:
                end_pos = revs.index(_end)
            except ValueError:
                pass

        if None not in [start, end] and start_pos > end_pos:
            raise RepositoryError('start cannot be after end')

        if end_pos is not None:
            end_pos += 1

        revs = revs[start_pos:end_pos]
        if reverse:
            revs = reversed(revs)
        for rev in revs:
            yield self.get_changeset(rev)

    def get_diff(self, rev1, rev2, path=None, ignore_whitespace=False,
            context=3):
        """
        Returns (git like) *diff*, as plain text. Shows changes introduced by
        ``rev2`` since ``rev1``.

        :param rev1: Entry point from which diff is shown. Can be
          ``self.EMPTY_CHANGESET`` - in this case, patch showing all
          the changes since empty state of the repository until ``rev2``
        :param rev2: Until which revision changes should be shown.
        :param ignore_whitespace: If set to ``True``, would not show whitespace
          changes. Defaults to ``False``.
        :param context: How many lines before/after changed lines should be
          shown. Defaults to ``3``.
        """
        flags = ['-U%s' % context]
        if ignore_whitespace:
            flags.append('-w')

        if rev1 == self.EMPTY_CHANGESET:
            rev2 = self.get_changeset(rev2).raw_id
            cmd = ' '.join(['show'] + flags + [rev2])
        else:
            rev1 = self.get_changeset(rev1).raw_id
            rev2 = self.get_changeset(rev2).raw_id
            cmd = ' '.join(['diff'] + flags + [rev1, rev2])

        if path:
            cmd += ' -- "%s"' % path
        stdout, stderr = self.run_git_command(cmd)
        # If we used 'show' command, strip first few lines (until actual diff
        # starts)
        if rev1 == self.EMPTY_CHANGESET:
            lines = stdout.splitlines()
            x = 0
            for line in lines:
                if line.startswith('diff'):
                    break
                x += 1
            # Append new line just like 'diff' command do
            stdout = '\n'.join(lines[x:]) + '\n'
        return stdout

    @LazyProperty
    def in_memory_changeset(self):
        """
        Returns ``GitInMemoryChangeset`` object for this repository.
        """
        return GitInMemoryChangeset(self)

    def clone(self, url, update_after_clone=True, bare=False):
        """
        Tries to clone changes from external location.

        :param update_after_clone: If set to ``False``, git won't checkout
          working directory
        :param bare: If set to ``True``, repository would be cloned into
          *bare* git repository (no working directory at all).
        """
        url = self._get_url(url)
        cmd = ['clone']
        if bare:
            cmd.append('--bare')
        elif not update_after_clone:
            cmd.append('--no-checkout')
        cmd += ['--', '"%s"' % url, '"%s"' % self.path]
        cmd = ' '.join(cmd)
        # If error occurs run_git_command raises RepositoryError already
        self.run_git_command(cmd)

    @LazyProperty
    def workdir(self):
        """
        Returns ``Workdir`` instance for this repository.
        """
        return GitWorkdir(self)

    def get_config_value(self, section, name, config_file=None):
        """
        Returns configuration value for a given [``section``] and ``name``.

        :param section: Section we want to retrieve value from
        :param name: Name of configuration we want to retrieve
        :param config_file: A path to file which should be used to retrieve
          configuration from (might also be a list of file paths)
        """
        if config_file is None:
            config_file = []
        elif isinstance(config_file, basestring):
            config_file = [config_file]

        def gen_configs():
            for path in config_file + self._config_files:
                try:
                    yield ConfigFile.from_path(path)
                except (IOError, OSError, ValueError):
                    continue

        for config in gen_configs():
            try:
                return config.get(section, name)
            except KeyError:
                continue
        return None

    def get_user_name(self, config_file=None):
        """
        Returns user's name from global configuration file.

        :param config_file: A path to file which should be used to retrieve
          configuration from (might also be a list of file paths)
        """
        return self.get_config_value('user', 'name', config_file)

    def get_user_email(self, config_file=None):
        """
        Returns user's email from global configuration file.

        :param config_file: A path to file which should be used to retrieve
          configuration from (might also be a list of file paths)
        """
        return self.get_config_value('user', 'email', config_file)

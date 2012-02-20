import re
from itertools import chain
from dulwich import objects
from subprocess import Popen, PIPE
from rhodecode.lib.vcs.conf import settings
from rhodecode.lib.vcs.exceptions import RepositoryError
from rhodecode.lib.vcs.exceptions import ChangesetError
from rhodecode.lib.vcs.exceptions import NodeDoesNotExistError
from rhodecode.lib.vcs.exceptions import VCSError
from rhodecode.lib.vcs.exceptions import ChangesetDoesNotExistError
from rhodecode.lib.vcs.exceptions import ImproperArchiveTypeError
from rhodecode.lib.vcs.backends.base import BaseChangeset
from rhodecode.lib.vcs.nodes import FileNode, DirNode, NodeKind, RootNode, RemovedFileNode
from rhodecode.lib.vcs.utils import safe_unicode
from rhodecode.lib.vcs.utils import date_fromtimestamp
from rhodecode.lib.vcs.utils.lazy import LazyProperty


class GitChangeset(BaseChangeset):
    """
    Represents state of the repository at single revision.
    """

    def __init__(self, repository, revision):
        self._stat_modes = {}
        self.repository = repository
        self.raw_id = revision
        self.revision = repository.revisions.index(revision)

        self.short_id = self.raw_id[:12]
        self.id = self.raw_id
        try:
            commit = self.repository._repo.get_object(self.raw_id)
        except KeyError:
            raise RepositoryError("Cannot get object with id %s" % self.raw_id)
        self._commit = commit
        self._tree_id = commit.tree

        try:
            self.message = safe_unicode(commit.message[:-1])
            # Always strip last eol
        except UnicodeDecodeError:
            self.message = commit.message[:-1].decode(commit.encoding
                or 'utf-8')
        #self.branch = None
        self.tags = []
        #tree = self.repository.get_object(self._tree_id)
        self.nodes = {}
        self._paths = {}

    @LazyProperty
    def author(self):
        return safe_unicode(self._commit.committer)

    @LazyProperty
    def date(self):
        return date_fromtimestamp(self._commit.commit_time,
                                  self._commit.commit_timezone)

    @LazyProperty
    def status(self):
        """
        Returns modified, added, removed, deleted files for current changeset
        """
        return self.changed, self.added, self.removed

    @LazyProperty
    def branch(self):
        # TODO: Cache as we walk (id <-> branch name mapping)
        refs = self.repository._repo.get_refs()
        heads = [(key[len('refs/heads/'):], val) for key, val in refs.items()
            if key.startswith('refs/heads/')]

        for name, id in heads:
            walker = self.repository._repo.object_store.get_graph_walker([id])
            while True:
                id = walker.next()
                if not id:
                    break
                if id == self.id:
                    return safe_unicode(name)
        raise ChangesetError("This should not happen... Have you manually "
            "change id of the changeset?")

    def _fix_path(self, path):
        """
        Paths are stored without trailing slash so we need to get rid off it if
        needed.
        """
        if path.endswith('/'):
            path = path.rstrip('/')
        return path

    def _get_id_for_path(self, path):
        # FIXME: Please, spare a couple of minutes and make those codes cleaner;
        if not path in self._paths:
            path = path.strip('/')
            # set root tree
            tree = self.repository._repo[self._commit.tree]
            if path == '':
                self._paths[''] = tree.id
                return tree.id
            splitted = path.split('/')
            dirs, name = splitted[:-1], splitted[-1]
            curdir = ''
            for dir in dirs:
                if curdir:
                    curdir = '/'.join((curdir, dir))
                else:
                    curdir = dir
                #if curdir in self._paths:
                    ## This path have been already traversed
                    ## Update tree and continue
                    #tree = self.repository._repo[self._paths[curdir]]
                    #continue
                dir_id = None
                for item, stat, id in tree.iteritems():
                    if curdir:
                        item_path = '/'.join((curdir, item))
                    else:
                        item_path = item
                    self._paths[item_path] = id
                    self._stat_modes[item_path] = stat
                    if dir == item:
                        dir_id = id
                if dir_id:
                    # Update tree
                    tree = self.repository._repo[dir_id]
                    if not isinstance(tree, objects.Tree):
                        raise ChangesetError('%s is not a directory' % curdir)
                else:
                    raise ChangesetError('%s have not been found' % curdir)
            for item, stat, id in tree.iteritems():
                if curdir:
                    name = '/'.join((curdir, item))
                else:
                    name = item
                self._paths[name] = id
                self._stat_modes[name] = stat
            if not path in self._paths:
                raise NodeDoesNotExistError("There is no file nor directory "
                    "at the given path %r at revision %r"
                    % (path, self.short_id))
        return self._paths[path]

    def _get_kind(self, path):
        id = self._get_id_for_path(path)
        obj = self.repository._repo[id]
        if isinstance(obj, objects.Blob):
            return NodeKind.FILE
        elif isinstance(obj, objects.Tree):
            return NodeKind.DIR

    def _get_file_nodes(self):
        return chain(*(t[2] for t in self.walk()))

    @LazyProperty
    def parents(self):
        """
        Returns list of parents changesets.
        """
        return [self.repository.get_changeset(parent)
            for parent in self._commit.parents]

    def next(self, branch=None):

        if branch and self.branch != branch:
            raise VCSError('Branch option used on changeset not belonging '
                           'to that branch')

        def _next(changeset, branch):
            try:
                next_ = changeset.revision + 1
                next_rev = changeset.repository.revisions[next_]
            except IndexError:
                raise ChangesetDoesNotExistError
            cs = changeset.repository.get_changeset(next_rev)

            if branch and branch != cs.branch:
                return _next(cs, branch)

            return cs

        return _next(self, branch)

    def prev(self, branch=None):
        if branch and self.branch != branch:
            raise VCSError('Branch option used on changeset not belonging '
                           'to that branch')

        def _prev(changeset, branch):
            try:
                prev_ = changeset.revision - 1
                if prev_ < 0:
                    raise IndexError
                prev_rev = changeset.repository.revisions[prev_]
            except IndexError:
                raise ChangesetDoesNotExistError

            cs = changeset.repository.get_changeset(prev_rev)

            if branch and branch != cs.branch:
                return _prev(cs, branch)

            return cs

        return _prev(self, branch)

    def get_file_mode(self, path):
        """
        Returns stat mode of the file at the given ``path``.
        """
        # ensure path is traversed
        self._get_id_for_path(path)
        return self._stat_modes[path]

    def get_file_content(self, path):
        """
        Returns content of the file at given ``path``.
        """
        id = self._get_id_for_path(path)
        blob = self.repository._repo[id]
        return blob.as_pretty_string()

    def get_file_size(self, path):
        """
        Returns size of the file at given ``path``.
        """
        id = self._get_id_for_path(path)
        blob = self.repository._repo[id]
        return blob.raw_length()

    def get_file_changeset(self, path):
        """
        Returns last commit of the file at the given ``path``.
        """
        node = self.get_node(path)
        return node.history[0]

    def get_file_history(self, path):
        """
        Returns history of file as reversed list of ``Changeset`` objects for
        which file at given ``path`` has been modified.

        TODO: This function now uses os underlying 'git' and 'grep' commands
        which is generally not good. Should be replaced with algorithm
        iterating commits.
        """
        cmd = 'log --name-status -p %s -- "%s" | grep "^commit"' \
            % (self.id, path)
        so, se = self.repository.run_git_command(cmd)
        ids = re.findall(r'\w{40}', so)
        return [self.repository.get_changeset(id) for id in ids]

    def get_file_annotate(self, path):
        """
        Returns a list of three element tuples with lineno,changeset and line

        TODO: This function now uses os underlying 'git' command which is
        generally not good. Should be replaced with algorithm iterating
        commits.
        """
        cmd = 'blame -l --root -r %s -- "%s"' % (self.id, path)
        # -l     ==> outputs long shas (and we need all 40 characters)
        # --root ==> doesn't put '^' character for bounderies
        # -r sha ==> blames for the given revision
        so, se = self.repository.run_git_command(cmd)
        annotate = []
        for i, blame_line in enumerate(so.split('\n')[:-1]):
            ln_no = i + 1
            id, line = re.split(r' \(.+?\) ', blame_line, 1)
            annotate.append((ln_no, self.repository.get_changeset(id), line))
        return annotate

    def fill_archive(self, stream=None, kind='tgz', prefix=None,
                     subrepos=False):
        """
        Fills up given stream.

        :param stream: file like object.
        :param kind: one of following: ``zip``, ``tgz`` or ``tbz2``.
            Default: ``tgz``.
        :param prefix: name of root directory in archive.
            Default is repository name and changeset's raw_id joined with dash
            (``repo-tip.<KIND>``).
        :param subrepos: include subrepos in this archive.

        :raise ImproperArchiveTypeError: If given kind is wrong.
        :raise VcsError: If given stream is None

        """
        allowed_kinds = settings.ARCHIVE_SPECS.keys()
        if kind not in allowed_kinds:
            raise ImproperArchiveTypeError('Archive kind not supported use one'
                'of %s', allowed_kinds)

        if prefix is None:
            prefix = '%s-%s' % (self.repository.name, self.short_id)
        elif prefix.startswith('/'):
            raise VCSError("Prefix cannot start with leading slash")
        elif prefix.strip() == '':
            raise VCSError("Prefix cannot be empty")

        if kind == 'zip':
            frmt = 'zip'
        else:
            frmt = 'tar'
        cmd = 'git archive --format=%s --prefix=%s/ %s' % (frmt, prefix,
            self.raw_id)
        if kind == 'tgz':
            cmd += ' | gzip -9'
        elif kind == 'tbz2':
            cmd += ' | bzip2 -9'

        if stream is None:
            raise VCSError('You need to pass in a valid stream for filling'
                           ' with archival data')
        popen = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True,
            cwd=self.repository.path)

        buffer_size = 1024 * 8
        chunk = popen.stdout.read(buffer_size)
        while chunk:
            stream.write(chunk)
            chunk = popen.stdout.read(buffer_size)
        # Make sure all descriptors would be read
        popen.communicate()

    def get_nodes(self, path):
        if self._get_kind(path) != NodeKind.DIR:
            raise ChangesetError("Directory does not exist for revision %r at "
                " %r" % (self.revision, path))
        path = self._fix_path(path)
        id = self._get_id_for_path(path)
        tree = self.repository._repo[id]
        dirnodes = []
        filenodes = []
        for name, stat, id in tree.iteritems():
            obj = self.repository._repo.get_object(id)
            if path != '':
                obj_path = '/'.join((path, name))
            else:
                obj_path = name
            if obj_path not in self._stat_modes:
                self._stat_modes[obj_path] = stat
            if isinstance(obj, objects.Tree):
                dirnodes.append(DirNode(obj_path, changeset=self))
            elif isinstance(obj, objects.Blob):
                filenodes.append(FileNode(obj_path, changeset=self, mode=stat))
            else:
                raise ChangesetError("Requested object should be Tree "
                                     "or Blob, is %r" % type(obj))
        nodes = dirnodes + filenodes
        for node in nodes:
            if not node.path in self.nodes:
                self.nodes[node.path] = node
        nodes.sort()
        return nodes

    def get_node(self, path):
        if isinstance(path, unicode):
            path = path.encode('utf-8')
        path = self._fix_path(path)
        if not path in self.nodes:
            try:
                id = self._get_id_for_path(path)
            except ChangesetError:
                raise NodeDoesNotExistError("Cannot find one of parents' "
                    "directories for a given path: %s" % path)
            obj = self.repository._repo.get_object(id)
            if isinstance(obj, objects.Tree):
                if path == '':
                    node = RootNode(changeset=self)
                else:
                    node = DirNode(path, changeset=self)
                node._tree = obj
            elif isinstance(obj, objects.Blob):
                node = FileNode(path, changeset=self)
                node._blob = obj
            else:
                raise NodeDoesNotExistError("There is no file nor directory "
                    "at the given path %r at revision %r"
                    % (path, self.short_id))
            # cache node
            self.nodes[path] = node
        return self.nodes[path]

    @LazyProperty
    def affected_files(self):
        """
        Get's a fast accessible file changes for given changeset
        """

        return self.added + self.changed

    @LazyProperty
    def _diff_name_status(self):
        output = []
        for parent in self.parents:
            cmd = 'diff --name-status %s %s' % (parent.raw_id, self.raw_id)
            so, se = self.repository.run_git_command(cmd)
            output.append(so.strip())
        return '\n'.join(output)

    def _get_paths_for_status(self, status):
        """
        Returns sorted list of paths for given ``status``.

        :param status: one of: *added*, *modified* or *deleted*
        """
        paths = set()
        char = status[0].upper()
        for line in self._diff_name_status.splitlines():
            if not line:
                continue
            if line.startswith(char):
                splitted = line.split(char,1)
                if not len(splitted) == 2:
                    raise VCSError("Couldn't parse diff result:\n%s\n\n and "
                        "particularly that line: %s" % (self._diff_name_status,
                        line))
                paths.add(splitted[1].strip())
        return sorted(paths)

    @LazyProperty
    def added(self):
        """
        Returns list of added ``FileNode`` objects.
        """
        if not self.parents:
            return list(self._get_file_nodes())
        return [self.get_node(path) for path in self._get_paths_for_status('added')]

    @LazyProperty
    def changed(self):
        """
        Returns list of modified ``FileNode`` objects.
        """
        if not self.parents:
            return []
        return [self.get_node(path) for path in self._get_paths_for_status('modified')]

    @LazyProperty
    def removed(self):
        """
        Returns list of removed ``FileNode`` objects.
        """
        if not self.parents:
            return []
        return [RemovedFileNode(path) for path in self._get_paths_for_status('deleted')]

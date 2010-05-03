import logging

from pylons import request, response, session, tmpl_context as c, url, config, app_globals as g
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
log = logging.getLogger(__name__)

class FilesController(BaseController):
    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.repo_name = get_repo_slug(request)

    def index(self, repo_name, revision, f_path):
        hg_model = HgModel()
        c.repo = repo = hg_model.get_repo(c.repo_name)
        c.cur_rev = revision
        c.f_path = f_path
        c.changeset = repo.get_changeset(repo._get_revision(revision))
        
        c.files_list = c.changeset.get_node(f_path)
        
        c.file_history = self._get_history(repo, c.files_list, f_path)
        return render('files/files.html')

    def diff(self, repo_name, f_path):
        hg_model = HgModel()
        diff1 = request.GET.get('diff1')
        diff2 = request.GET.get('diff2')
        c.f_path = f_path
        c.repo = hg_model.get_repo(c.repo_name)
        c.changeset_1 = c.repo.get_changeset(diff1)
        c.changeset_2 = c.repo.get_changeset(diff2)
        
        c.file_1 = c.changeset_1.get_node(f_path).content
        c.file_2 = c.changeset_2.get_node(f_path).content
        c.diff1 = 'r%s:%s' % (c.changeset_1.revision, c.changeset_1._short)
        c.diff2 = 'r%s:%s' % (c.changeset_2.revision, c.changeset_2._short)
        from difflib import unified_diff
        d = unified_diff(c.file_1.splitlines(1), c.file_2.splitlines(1))
        c.diff = ''.join(d)
        return render('files/file_diff.html')
    
    def _get_history(self, repo, node, f_path):
        from vcs.nodes import NodeKind
        if not node.kind is NodeKind.FILE:
            return []
        changesets = node.history
        hist_l = []
        for chs in changesets:
            n_desc = 'r%s:%s' % (chs.revision, chs._short)
            hist_l.append((chs._short, n_desc,))
        return hist_l

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


    def _get_history(self, repo, node, f_path):
        from vcs.nodes import NodeKind
        if not node.kind is NodeKind.FILE:
            return []
        changesets = list(node.history)
        changesets.reverse()
        hist_l = []
        for chs in changesets:
            n_desc = 'r%s:%s' % (chs.revision, chs._short)
            hist_l.append((chs._short, n_desc,))
        return hist_l

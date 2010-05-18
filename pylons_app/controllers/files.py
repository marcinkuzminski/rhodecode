import logging

from pylons import request, response, session, tmpl_context as c, url, config, app_globals as g
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
from vcs.utils import diffs as differ
from vcs.exceptions import RepositoryError, ChangesetError
        
log = logging.getLogger(__name__)

class FilesController(BaseController):
    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.repo_name = get_repo_slug(request)

    def index(self, repo_name, revision, f_path):
        hg_model = HgModel()
        c.repo = repo = hg_model.get_repo(c.repo_name)
        revision = request.POST.get('at_rev', None) or revision
        
        def get_next_rev(cur):
            max_rev = len(c.repo.revisions) - 1
            r = cur + 1
            if r > max_rev:
                r = max_rev
            return r
            
        def get_prev_rev(cur):
            r = cur - 1
            return r

        c.f_path = f_path
     
        
        try:
            cur_rev = repo.get_changeset(revision).revision
            prev_rev = repo.get_changeset(get_prev_rev(cur_rev)).raw_id
            next_rev = repo.get_changeset(get_next_rev(cur_rev)).raw_id
                    
            c.url_prev = url('files_home', repo_name=c.repo_name,
                             revision=prev_rev, f_path=f_path) 
            c.url_next = url('files_home', repo_name=c.repo_name,
                             revision=next_rev, f_path=f_path)   
                    
            c.changeset = repo.get_changeset(revision)
            try:
                c.file_msg = c.changeset.get_file_message(f_path)
            except:
                c.file_msg = None
                        
            c.cur_rev = c.changeset.raw_id
            c.rev_nr = c.changeset.revision
            c.files_list = c.changeset.get_node(f_path)
            c.file_history = self._get_history(repo, c.files_list, f_path)
            
        except (RepositoryError, ChangesetError):
            c.files_list = None
        
        return render('files/files.html')

    def rawfile(self, repo_name, revision, f_path):
        hg_model = HgModel()
        c.repo = hg_model.get_repo(c.repo_name)
        file_node = c.repo.get_changeset(revision).get_node(f_path)
        response.content_type = file_node.mimetype
        response.content_disposition = 'attachment; filename=%s' \
                                                    % f_path.split('/')[-1] 
        return file_node.content
    
    def archivefile(self, repo_name, revision, fileformat):
        return '%s %s %s' % (repo_name, revision, fileformat)
    
    def diff(self, repo_name, f_path):
        hg_model = HgModel()
        diff1 = request.GET.get('diff1')
        diff2 = request.GET.get('diff2')
        c.action = action = request.GET.get('diff')
        c.no_changes = diff1 == diff2
        c.f_path = f_path
        c.repo = hg_model.get_repo(c.repo_name)
        c.changeset_1 = c.repo.get_changeset(diff1)
        c.changeset_2 = c.repo.get_changeset(diff2)

        c.diff1 = 'r%s:%s' % (c.changeset_1.revision, c.changeset_1._short)
        c.diff2 = 'r%s:%s' % (c.changeset_2.revision, c.changeset_2._short)
        f_udiff = differ.get_udiff(c.changeset_1.get_node(f_path),
                            c.changeset_2.get_node(f_path))
        
        diff = differ.DiffProcessor(f_udiff)
                                
        if action == 'download':
            diff_name = '%s_vs_%s.diff' % (diff1, diff2)
            response.content_type = 'text/plain'
            response.content_disposition = 'attachment; filename=%s' \
                                                    % diff_name             
            return diff.raw_diff()
        
        elif action == 'raw':
            c.cur_diff = '<pre class="raw">%s</pre>' % diff.raw_diff()
        elif action == 'diff':
            c.cur_diff = diff.as_html()

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

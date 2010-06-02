from pylons import tmpl_context as c, request
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.model.hg_model import HgModel, _full_changelog_cached
import logging

log = logging.getLogger(__name__)

class SummaryController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        super(SummaryController, self).__before__()
        
    def index(self):
        hg_model = HgModel()
        c.repo_info = hg_model.get_repo(c.repo_name)
        c.repo_changesets = _full_changelog_cached(c.repo_name)[:10]
        e = request.environ
        uri = u'%(protocol)s://%(user)s@%(host)s/%(repo_name)s' % {
                                        'protocol': e.get('wsgi.url_scheme'),
                                        'user':str(c.hg_app_user.username),
                                        'host':e.get('HTTP_HOST'),
                                        'repo_name':c.repo_name, }
        c.clone_repo_url = uri
        c.repo_tags = c.repo_info.tags[:10]
        c.repo_branches = c.repo_info.branches[:10]
        return render('summary/summary.html')

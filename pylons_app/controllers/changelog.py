from mercurial.graphmod import revisions as graph_rev, colored, CHANGESET
from mercurial.node import short
from pylons import request, response, session, tmpl_context as c, url, config, \
    app_globals as g
from pylons.controllers.util import abort, redirect
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render, _full_changelog_cached
from pylons_app.lib.filters import age as _age, person
from simplejson import dumps
from webhelpers.paginate import Page
import logging
log = logging.getLogger(__name__)     

class ChangelogController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        super(ChangelogController, self).__before__()
                
    def index(self):
        limit = 100
        default = 20
        if request.params.get('size'):
            try:
                int_size = int(request.params.get('size'))
            except ValueError:
                int_size = default
            int_size = int_size if int_size <= limit else limit 
            c.size = int_size
            session['changelog_size'] = c.size
            session.save()
        else:
            c.size = session.get('changelog_size', default)

        changesets = _full_changelog_cached(c.repo_name)
            
        p = int(request.params.get('page', 1))
        c.pagination = Page(changesets, page=p, item_count=len(changesets),
                            items_per_page=c.size)
            
        #self._graph(c.repo, c.size,p)
        
        return render('changelog/changelog.html')


    def _graph(self, repo, size, p):
        revcount = size
        if not repo.revisions:return dumps([]), 0
        
        max_rev = repo.revisions[-1]
        offset = 1 if p == 1 else  ((p - 1) * revcount)
        rev_start = repo.revisions[(-1 * offset)]
        c.bg_height = 120
        
        revcount = min(max_rev, revcount)
        rev_end = max(0, rev_start - revcount)
        dag = graph_rev(repo.repo, rev_start, rev_end)
        
        c.dag = tree = list(colored(dag))
        canvasheight = (len(tree) + 1) * c.bg_height - 27
        data = []
        for (id, type, ctx, vtx, edges) in tree:
            if type != CHANGESET:
                continue
            node = short(ctx.node())
            age = _age(ctx.date())
            desc = ctx.description()
            user = person(ctx.user())
            branch = ctx.branch()
            branch = branch, repo.repo.branchtags().get(branch) == ctx.node()
            data.append((node, vtx, edges, desc, user, age, branch, ctx.tags()))
    
        c.jsdata = dumps(data) 
        c.canvasheight = canvasheight 


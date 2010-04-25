from pylons import request, response, session, tmpl_context as c, url, config, \
    app_globals as g
from pylons.controllers.util import abort, redirect
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
import logging


log = logging.getLogger(__name__)

class GraphController(BaseController):
    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.repo_name = get_repo_slug(request)
        
    def index(self):
        # Return a rendered template
        hg_model = HgModel()
        if request.POST.get('size'):
            c.size = int(request.params.get('size', 20))
        else:
            c.size = int(request.params.get('size', 20))
        c.jsdata, c.canvasheight = self.graph(hg_model.get_repo(c.repo_name), c.size)
        
        return render('/graph.html')


    def graph(self, repo, size):
        from mercurial.graphmod import revisions as graph_rev, colored, CHANGESET
        from pylons_app.lib.filters import age as _age, person
        from simplejson import dumps
        from mercurial.node import short
        from webhelpers.paginate import Page
        revcount = size
        p = int(request.params.get('page', 1))
        c.pagination = Page(repo.revisions, page=p, item_count=len(repo.revisions), items_per_page=revcount)
        max_rev = repo.revisions[-1]
        offset = 1 if p == 1 else  ((p - 1) * revcount)
        rev_start = repo.revisions[(-1 * offset)]
        bg_height = 39
        
        revcount = min(max_rev, revcount)
        rev_end = max(0, rev_start - revcount)
        print rev_start, rev_end
        print 'x' * 100
        dag = graph_rev(repo.repo, rev_start, rev_end)
        tree = list(colored(dag))
        canvasheight = (len(tree) + 1) * bg_height - 27
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
    
        return dumps(data), canvasheight

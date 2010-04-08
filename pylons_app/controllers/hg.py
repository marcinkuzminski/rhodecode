#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import os
from pylons_app.lib.base import BaseController
from pylons import tmpl_context as c, app_globals as g, session, request, config
from pylons_app.lib import helpers as h
from mako.template import Template
from pylons.controllers.util import abort
from pylons_app.lib.base import BaseController, render
try:
    from vcs.backends.hg import get_repositories
except ImportError:
    print 'You have to import vcs module'
from mercurial.util import matchdate, Abort, makedate
from mercurial.hgweb.common import get_contact
from mercurial.templatefilters import age
log = logging.getLogger(__name__)

class HgController(BaseController):

    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.staticurl = g.statics

    def index(self):
        c.repos_list = []
        
        def get_mtime(spath):
            cl_path = os.path.join(spath, "00changelog.i")
            if os.path.exists(cl_path):
                return os.stat(cl_path).st_mtime
            else:
                return os.stat(spath).st_mtime   
        
        def archivelist(ui, nodeid, url):
            allowed = g.baseui.configlist("web", "allow_archive", untrusted=True)
            for i in [('zip', '.zip'), ('gz', '.tar.gz'), ('bz2', '.tar.bz2')]:
                if i[0] in allowed or ui.configbool("web", "allow" + i[0],
                                                    untrusted=True):
                    yield {"type" : i[0], "extension": i[1],
                           "node": nodeid, "url": url}
                                    
        for name, r in get_repositories(g.paths[0][0], g.paths[0][1]).items():
            last_change = (get_mtime(r.spath), makedate()[1])
            tip = r.changectx('tip')
            tmp_d = {}
            tmp_d['name'] = name
            tmp_d['desc'] = r.ui.config('web', 'description', 'Unknown', untrusted=True)
            tmp_d['last_change'] = age(last_change)
            tmp_d['tip'] = str(tip)
            tmp_d['rev'] = tip.rev()
            tmp_d['contact'] = get_contact(r.ui.config)
            tmp_d['repo_archives'] = archivelist(r.ui, "tip", 'sa')
            
            c.repos_list.append(tmp_d)
        return render('/index.html')

    def view(self, *args, **kwargs):
        #TODO: reimplement this not tu use hgwebdir
        response = g.hgapp(request.environ, self.start_response)
        
        http_accept = request.environ.get('HTTP_ACCEPT', False)
        if not http_accept:
            return abort(status_code=400, detail='no http accept in header')
        
        #for mercurial protocols and raw files we can't wrap into mako
        if http_accept.find("mercurial") != -1 or \
        request.environ['PATH_INFO'].find('raw-file') != -1:
                    return response
        try:
            tmpl = u''.join(response)
            template = Template(tmpl, lookup=request.environ['pylons.pylons']\
                            .config['pylons.app_globals'].mako_lookup)
                        
        except (RuntimeError, UnicodeDecodeError):
            log.info('disabling unicode due to encoding error')
            response = g.hgapp(request.environ, self.start_response)
            tmpl = ''.join(response)
            template = Template(tmpl, lookup=request.environ['pylons.pylons']\
                            .config['pylons.app_globals'].mako_lookup, disable_unicode=True)


        return template.render(g=g, c=c, session=session, h=h)

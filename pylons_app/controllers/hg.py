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
                
        for name, r in get_repositories(g.paths[0][0], g.paths[0][1]).items():
            last_change = (get_mtime(r.spath), makedate()[1])
            tmp = {}
            tmp['name'] = name
            tmp['desc'] = r.ui.config('web', 'description', 'Unknown', untrusted=True)
            tmp['last_change'] = last_change,
            tip = r.changectx('tip')
            tmp['tip'] = tip.__str__(),
            tmp['rev'] = tip.rev()
            tmp['contact'] = get_contact(r.ui.config)
            c.repos_list.append(tmp)
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

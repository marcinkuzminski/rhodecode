#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
from pylons_app.lib.base import BaseController, render
from pylons import c, g, session, request
from pylons_app.lib import helpers as h
from mako.template import Template
from pprint import pprint
import os
from mercurial import ui, hg
from mercurial.error import RepoError
from ConfigParser import ConfigParser
import encodings
log = logging.getLogger(__name__)

class HgController(BaseController):

    def __before__(self):
        c.repos_prefix = 'etelko'

    def view(self, *args, **kwargs):
        response = g.hgapp(request.environ, self.start_response)
        #for mercurial protocols and raw files we can't wrap into mako
        if request.environ['HTTP_ACCEPT'].find("mercurial") != -1 or \
        request.environ['PATH_INFO'].find('raw-file') != -1:
                    return response

        tmpl = ''.join(response)

        template = Template(tmpl, lookup=request.environ['pylons.pylons']\
                            .config['pylons.g'].mako_lookup)

        return template.render(g=g, c=c, session=session, h=h)


    def manage_hgrc(self):
        pass

    def hgrc(self, dirname):
        filename = os.path.join(dirname, '.hg', 'hgrc')
        return filename

    def add_repo(self, new_repo):
        c.staticurl = g.statics

        #extra check it can be add since it's the command
        if new_repo == 'add':
            c.msg = 'you basstard ! this repo is a command'
            c.new_repo = ''
            return render('add.html')

        new_repo = new_repo.replace(" ", "_")
        new_repo = new_repo.replace("-", "_")

        try:
            self._create_repo(new_repo)
            c.new_repo = new_repo
            c.msg = 'added repo'
        except Exception as e:
            c.new_repo = 'Exception when adding: %s' % new_repo
            c.msg = str(e)

        return render('add.html')

    def _check_repo(self, repo_name):
        p = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(p, 'hgwebdir.config')

        cp = ConfigParser()

        cp.read(config_path)
        repos_path = cp.get('paths', '/').replace("**", '')

        if not repos_path:
            raise Exception('Could not read config !')

        self.repo_path = os.path.join(repos_path, repo_name)

        try:
            r = hg.repository(ui.ui(), self.repo_path)
            hg.verify(r)
            #here we hnow that repo exists it was verified
            log.info('%s repo is already created', repo_name)
            raise Exception('Repo exists')
        except RepoError:
            log.info('%s repo is free for creation', repo_name)
            #it means that there is no valid repo there...
            return True


    def _create_repo(self, repo_name):
        if repo_name in [None, '', 'add']:
            raise Exception('undefined repo_name of repo')

        if self._check_repo(repo_name):
            log.info('creating repo %s in %s', repo_name, self.repo_path)
            cmd = """mkdir %s && hg init %s""" \
                    % (self.repo_path, self.repo_path)
            os.popen(cmd)

#def _make_app():
#    #for single a repo
#    #return hgweb("/path/to/repo", "Name")
#    repos = "hgwebdir.config"
#    return  hgwebdir(repos)
#

#    def view(self, environ, start_response):
#        #the following is only needed when using hgwebdir
#        app = _make_app()
#        #return wsgi_app(environ, start_response)
#        response = app(request.environ, self.start_response)
#
#        if environ['PATH_INFO'].find("static") != -1:
#            return response
#        else:
#            #wrap the murcurial response in a mako template.
#            template = Template("".join(response),
#                                lookup = environ['pylons.pylons']\
#                                .config['pylons.g'].mako_lookup)
#
#            return template.render(g = g, c = c, session = session, h = h)

#!/usr/bin/env python
# encoding: utf-8
# repos controller for pylons
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
"""
Created on April 7, 2010
admin controller for pylons
@author: marcink
"""
from formencode import htmlfill
from operator import itemgetter
from paste.httpexceptions import HTTPInternalServerError
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator, \
    HasPermissionAnyDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils import invalidate_cache, action_logger
from rhodecode.model.db import User
from rhodecode.model.forms import RepoForm
from rhodecode.model.scm import ScmModel
from rhodecode.model.repo import RepoModel
import formencode
import logging
import traceback

log = logging.getLogger(__name__)

class ReposController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('repo', 'repos')

    @LoginRequired()
    @HasPermissionAnyDecorator('hg.admin', 'hg.create.repository')
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(ReposController, self).__before__()

    @HasPermissionAllDecorator('hg.admin')
    def index(self, format='html'):
        """GET /repos: All items in the collection"""
        # url('repos')
        cached_repo_list = ScmModel().get_repos()
        c.repos_list = sorted(cached_repo_list, key=itemgetter('name_sort'))
        return render('admin/repos/repos.html')

    @HasPermissionAnyDecorator('hg.admin', 'hg.create.repository')
    def create(self):
        """POST /repos: Create a new item"""
        # url('repos')
        repo_model = RepoModel()
        _form = RepoForm()()
        form_result = {}
        try:
            form_result = _form.to_python(dict(request.POST))
            repo_model.create(form_result, c.rhodecode_user)
            h.flash(_('created repository %s') % form_result['repo_name'],
                    category='success')

            if request.POST.get('user_created'):
                action_logger(self.rhodecode_user, 'user_created_repo',
                              form_result['repo_name'], '', self.sa)
            else:
                action_logger(self.rhodecode_user, 'admin_created_repo',
                              form_result['repo_name'], '', self.sa)

        except formencode.Invalid, errors:
            c.new_repo = errors.value['repo_name']

            if request.POST.get('user_created'):
                r = render('admin/repos/repo_add_create_repository.html')
            else:
                r = render('admin/repos/repo_add.html')

            return htmlfill.render(
                r,
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")

        except Exception:
            log.error(traceback.format_exc())
            msg = _('error occured during creation of repository %s') \
                    % form_result.get('repo_name')
            h.flash(msg, category='error')
        if request.POST.get('user_created'):
            return redirect(url('home'))
        return redirect(url('repos'))

    @HasPermissionAllDecorator('hg.admin')
    def new(self, format='html'):
        """GET /repos/new: Form to create a new item"""
        new_repo = request.GET.get('repo', '')
        c.new_repo = h.repo_name_slug(new_repo)

        return render('admin/repos/repo_add.html')

    @HasPermissionAllDecorator('hg.admin')
    def update(self, repo_name):
        """PUT /repos/repo_name: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('repo', repo_name=ID),
        #           method='put')
        # url('repo', repo_name=ID)
        repo_model = RepoModel()
        changed_name = repo_name
        _form = RepoForm(edit=True, old_data={'repo_name':repo_name})()

        try:
            form_result = _form.to_python(dict(request.POST))
            repo_model.update(repo_name, form_result)
            invalidate_cache('get_repo_cached_%s' % repo_name)
            h.flash(_('Repository %s updated successfully' % repo_name),
                    category='success')
            changed_name = form_result['repo_name']
            action_logger(self.rhodecode_user, 'admin_updated_repo',
                              changed_name, '', self.sa)

        except formencode.Invalid, errors:
            c.repo_info = repo_model.get_by_repo_name(repo_name)
            c.users_array = repo_model.get_users_js()
            errors.value.update({'user':c.repo_info.user.username})
            return htmlfill.render(
                render('admin/repos/repo_edit.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")

        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during update of repository %s') \
                    % repo_name, category='error')

        return redirect(url('edit_repo', repo_name=changed_name))

    @HasPermissionAllDecorator('hg.admin')
    def delete(self, repo_name):
        """DELETE /repos/repo_name: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('repo', repo_name=ID),
        #           method='delete')
        # url('repo', repo_name=ID)

        repo_model = RepoModel()
        repo = repo_model.get_by_repo_name(repo_name)
        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps'
                      ' it was moved or renamed  from the filesystem'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')

            return redirect(url('repos'))
        try:
            action_logger(self.rhodecode_user, 'admin_deleted_repo',
                              repo_name, '', self.sa)
            repo_model.delete(repo)
            invalidate_cache('get_repo_cached_%s' % repo_name)
            h.flash(_('deleted repository %s') % repo_name, category='success')

        except Exception, e:
            log.error(traceback.format_exc())
            h.flash(_('An error occured during deletion of %s') % repo_name,
                    category='error')

        return redirect(url('repos'))

    @HasPermissionAllDecorator('hg.admin')
    def delete_perm_user(self, repo_name):
        """
        DELETE an existing repository permission user
        :param repo_name:
        """

        try:
            repo_model = RepoModel()
            repo_model.delete_perm_user(request.POST, repo_name)
        except Exception, e:
            h.flash(_('An error occured during deletion of repository user'),
                    category='error')
            raise HTTPInternalServerError()

    @HasPermissionAllDecorator('hg.admin')
    def repo_stats(self, repo_name):
        """
        DELETE an existing repository statistics
        :param repo_name:
        """

        try:
            repo_model = RepoModel()
            repo_model.delete_stats(repo_name)
        except Exception, e:
            h.flash(_('An error occured during deletion of repository stats'),
                    category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasPermissionAllDecorator('hg.admin')
    def repo_cache(self, repo_name):
        """
        INVALIDATE exisitings repository cache
        :param repo_name:
        """

        try:
            ScmModel().mark_for_invalidation(repo_name)
        except Exception, e:
            h.flash(_('An error occurred during cache invalidation'),
                    category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasPermissionAllDecorator('hg.admin')
    def show(self, repo_name, format='html'):
        """GET /repos/repo_name: Show a specific item"""
        # url('repo', repo_name=ID)

    @HasPermissionAllDecorator('hg.admin')
    def edit(self, repo_name, format='html'):
        """GET /repos/repo_name/edit: Form to edit an existing item"""
        # url('edit_repo', repo_name=ID)
        repo_model = RepoModel()
        c.repo_info = repo = repo_model.get_by_repo_name(repo_name)
        if repo.stats:
            last_rev = repo.stats.stat_on_revision
        else:
            last_rev = 0
        c.stats_revision = last_rev
        r = ScmModel().get(repo_name)
        c.repo_last_rev = r.revisions[-1] if r.revisions else 0

        if last_rev == 0:
            c.stats_percentage = 0
        else:
            c.stats_percentage = '%.2f' % ((float((last_rev)) / c.repo_last_rev) * 100)


        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps'
                      ' it was created or renamed from the filesystem'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')

            return redirect(url('repos'))
        defaults = c.repo_info.__dict__
        if c.repo_info.user:
            defaults.update({'user':c.repo_info.user.username})
        else:
            replacement_user = self.sa.query(User)\
            .filter(User.admin == True).first().username
            defaults.update({'user':replacement_user})

        c.users_array = repo_model.get_users_js()

        for p in c.repo_info.repo_to_perm:
            defaults.update({'perm_%s' % p.user.username:
                             p.permission.permission_name})

        return htmlfill.render(
            render('admin/repos/repo_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

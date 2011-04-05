# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Settings controller for rhodecode
    
    :created_on: Jun 30, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>    
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import traceback
import formencode

from formencode import htmlfill

from pylons import tmpl_context as c, request, url
from pylons.controllers.util import redirect
from pylons.i18n.translation import _

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAllDecorator, \
    HasRepoPermissionAnyDecorator, NotAnonymous
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils import invalidate_cache, action_logger
from rhodecode.model.forms import RepoSettingsForm, RepoForkForm
from rhodecode.model.repo import RepoModel

log = logging.getLogger(__name__)

class SettingsController(BaseController):

    @LoginRequired()
    def __before__(self):
        super(SettingsController, self).__before__()

    @HasRepoPermissionAllDecorator('repository.admin')
    def index(self, repo_name):
        repo_model = RepoModel()
        c.repo_info = repo = repo_model.get_by_repo_name(repo_name)
        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps'
                      ' it was created or renamed from the file system'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')

            return redirect(url('home'))
        defaults = c.repo_info.get_dict()
        defaults.update({'user':c.repo_info.user.username})
        c.users_array = repo_model.get_users_js()

        for p in c.repo_info.repo_to_perm:
            defaults.update({'perm_%s' % p.user.username:
                             p.permission.permission_name})

        return htmlfill.render(
            render('settings/repo_settings.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    @HasRepoPermissionAllDecorator('repository.admin')
    def update(self, repo_name):
        repo_model = RepoModel()
        changed_name = repo_name
        _form = RepoSettingsForm(edit=True, old_data={'repo_name':repo_name})()
        try:
            form_result = _form.to_python(dict(request.POST))
            repo_model.update(repo_name, form_result)
            invalidate_cache('get_repo_cached_%s' % repo_name)
            h.flash(_('Repository %s updated successfully' % repo_name),
                    category='success')
            changed_name = form_result['repo_name']
            action_logger(self.rhodecode_user, 'user_updated_repo',
                              changed_name, '', self.sa)
        except formencode.Invalid, errors:
            c.repo_info = repo_model.get_by_repo_name(repo_name)
            c.users_array = repo_model.get_users_js()
            errors.value.update({'user':c.repo_info.user.username})
            return htmlfill.render(
                render('settings/repo_settings.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during update of repository %s') \
                    % repo_name, category='error')

        return redirect(url('repo_settings_home', repo_name=changed_name))


    @HasRepoPermissionAllDecorator('repository.admin')
    def delete(self, repo_name):
        """DELETE /repos/repo_name: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('repo_settings_delete', repo_name=ID),
        #           method='delete')
        # url('repo_settings_delete', repo_name=ID)

        repo_model = RepoModel()
        repo = repo_model.get_by_repo_name(repo_name)
        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps'
                      ' it was moved or renamed  from the filesystem'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')

            return redirect(url('home'))
        try:
            action_logger(self.rhodecode_user, 'user_deleted_repo',
                              repo_name, '', self.sa)
            repo_model.delete(repo)
            invalidate_cache('get_repo_cached_%s' % repo_name)
            h.flash(_('deleted repository %s') % repo_name, category='success')
        except Exception:
            h.flash(_('An error occurred during deletion of %s') % repo_name,
                    category='error')

        return redirect(url('home'))

    @NotAnonymous()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def fork(self, repo_name):
        repo_model = RepoModel()
        c.repo_info = repo = repo_model.get_by_repo_name(repo_name)
        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps'
                      ' it was created or renamed from the file system'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')

            return redirect(url('home'))

        return render('settings/repo_fork.html')

    @NotAnonymous()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def fork_create(self, repo_name):
        repo_model = RepoModel()
        c.repo_info = repo_model.get_by_repo_name(repo_name)
        _form = RepoForkForm(old_data={'repo_type':c.repo_info.repo_type})()
        form_result = {}
        try:
            form_result = _form.to_python(dict(request.POST))
            form_result.update({'repo_name':repo_name})
            repo_model.create_fork(form_result, c.rhodecode_user)
            h.flash(_('forked %s repository as %s') \
                      % (repo_name, form_result['fork_name']),
                    category='success')
            action_logger(self.rhodecode_user,
                          'user_forked_repo:%s' % form_result['fork_name'],
                           repo_name, '', self.sa)
        except formencode.Invalid, errors:
            c.new_repo = errors.value['fork_name']
            r = render('settings/repo_fork.html')

            return htmlfill.render(
                r,
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        return redirect(url('home'))

# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.repos
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Repositories controller for RhodeCode

    :created_on: Apr 7, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
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

from paste.httpexceptions import HTTPInternalServerError
from pylons import request, session, tmpl_context as c, url
from pylons.controllers.util import redirect
from pylons.i18n.translation import _
from sqlalchemy.exc import IntegrityError

from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator, \
    HasPermissionAnyDecorator, HasRepoPermissionAllDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils import invalidate_cache, action_logger, repo_name_slug
from rhodecode.lib.helpers import get_token
from rhodecode.model.meta import Session
from rhodecode.model.db import User, Repository, UserFollowing, RepoGroup
from rhodecode.model.forms import RepoForm
from rhodecode.model.scm import ScmModel
from rhodecode.model.repo import RepoModel

log = logging.getLogger(__name__)


class ReposController(BaseController):
    """
    REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('repo', 'repos')

    @LoginRequired()
    @HasPermissionAnyDecorator('hg.admin', 'hg.create.repository')
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(ReposController, self).__before__()

    def __load_defaults(self):
        c.repo_groups = RepoGroup.groups_choices()
        c.repo_groups_choices = map(lambda k: unicode(k[0]), c.repo_groups)

        repo_model = RepoModel()
        c.users_array = repo_model.get_users_js()
        c.users_groups_array = repo_model.get_users_groups_js()

    def __load_data(self, repo_name=None):
        """
        Load defaults settings for edit, and update

        :param repo_name:
        """
        self.__load_defaults()

        c.repo_info = db_repo = Repository.get_by_repo_name(repo_name)
        repo = db_repo.scm_instance

        if c.repo_info is None:
            h.flash(_('%s repository is not mapped to db perhaps'
                      ' it was created or renamed from the filesystem'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')

            return redirect(url('repos'))

        c.default_user_id = User.get_by_username('default').user_id
        c.in_public_journal = UserFollowing.query()\
            .filter(UserFollowing.user_id == c.default_user_id)\
            .filter(UserFollowing.follows_repository == c.repo_info).scalar()

        if c.repo_info.stats:
            # this is on what revision we ended up so we add +1 for count
            last_rev = c.repo_info.stats.stat_on_revision + 1
        else:
            last_rev = 0
        c.stats_revision = last_rev

        c.repo_last_rev = repo.count() if repo.revisions else 0

        if last_rev == 0 or c.repo_last_rev == 0:
            c.stats_percentage = 0
        else:
            c.stats_percentage = '%.2f' % ((float((last_rev)) /
                                            c.repo_last_rev) * 100)

        defaults = RepoModel()._get_defaults(repo_name)

        c.repos_list = [('', _('--REMOVE FORK--'))]
        c.repos_list += [(x.repo_id, x.repo_name) for x in
                   Repository.query().order_by(Repository.repo_name).all()]
        return defaults

    @HasPermissionAllDecorator('hg.admin')
    def index(self, format='html'):
        """GET /repos: All items in the collection"""
        # url('repos')

        c.repos_list = ScmModel().get_repos(Repository.query()
                                            .order_by(Repository.repo_name)
                                            .all(), sort_key='name_sort')
        return render('admin/repos/repos.html')

    @HasPermissionAnyDecorator('hg.admin', 'hg.create.repository')
    def create(self):
        """
        POST /repos: Create a new item"""
        # url('repos')

        self.__load_defaults()
        form_result = {}
        try:
            form_result = RepoForm(repo_groups=c.repo_groups_choices)()\
                            .to_python(dict(request.POST))
            RepoModel().create(form_result, self.rhodecode_user)
            if form_result['clone_uri']:
                h.flash(_('created repository %s from %s') \
                    % (form_result['repo_name'], form_result['clone_uri']),
                    category='success')
            else:
                h.flash(_('created repository %s') % form_result['repo_name'],
                    category='success')

            if request.POST.get('user_created'):
                # created by regular non admin user
                action_logger(self.rhodecode_user, 'user_created_repo',
                              form_result['repo_name_full'], '', self.sa)
            else:
                action_logger(self.rhodecode_user, 'admin_created_repo',
                              form_result['repo_name_full'], '', self.sa)
            Session.commit()
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
            msg = _('error occurred during creation of repository %s') \
                    % form_result.get('repo_name')
            h.flash(msg, category='error')
        if request.POST.get('user_created'):
            return redirect(url('home'))
        return redirect(url('repos'))

    @HasPermissionAllDecorator('hg.admin')
    def new(self, format='html'):
        """GET /repos/new: Form to create a new item"""
        new_repo = request.GET.get('repo', '')
        c.new_repo = repo_name_slug(new_repo)
        self.__load_defaults()
        return render('admin/repos/repo_add.html')

    @HasPermissionAllDecorator('hg.admin')
    def update(self, repo_name):
        """
        PUT /repos/repo_name: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('repo', repo_name=ID),
        #           method='put')
        # url('repo', repo_name=ID)
        self.__load_defaults()
        repo_model = RepoModel()
        changed_name = repo_name
        _form = RepoForm(edit=True, old_data={'repo_name': repo_name},
                         repo_groups=c.repo_groups_choices)()
        try:
            form_result = _form.to_python(dict(request.POST))
            repo = repo_model.update(repo_name, form_result)
            invalidate_cache('get_repo_cached_%s' % repo_name)
            h.flash(_('Repository %s updated successfully' % repo_name),
                    category='success')
            changed_name = repo.repo_name
            action_logger(self.rhodecode_user, 'admin_updated_repo',
                              changed_name, '', self.sa)
            Session.commit()
        except formencode.Invalid, errors:
            defaults = self.__load_data(repo_name)
            defaults.update(errors.value)
            return htmlfill.render(
                render('admin/repos/repo_edit.html'),
                defaults=defaults,
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
        """
        DELETE /repos/repo_name: Delete an existing item"""
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
            Session.commit()
        except IntegrityError, e:
            if e.message.find('repositories_fork_id_fkey') != -1:
                log.error(traceback.format_exc())
                h.flash(_('Cannot delete %s it still contains attached '
                          'forks') % repo_name,
                        category='warning')
            else:
                log.error(traceback.format_exc())
                h.flash(_('An error occurred during '
                          'deletion of %s') % repo_name,
                        category='error')

        except Exception, e:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during deletion of %s') % repo_name,
                    category='error')

        return redirect(url('repos'))

    @HasRepoPermissionAllDecorator('repository.admin')
    def delete_perm_user(self, repo_name):
        """
        DELETE an existing repository permission user

        :param repo_name:
        """

        try:
            RepoModel().revoke_user_permission(repo=repo_name,
                                               user=request.POST['user_id'])
            Session.commit()
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during deletion of repository user'),
                    category='error')
            raise HTTPInternalServerError()

    @HasRepoPermissionAllDecorator('repository.admin')
    def delete_perm_users_group(self, repo_name):
        """
        DELETE an existing repository permission users group

        :param repo_name:
        """

        try:
            RepoModel().revoke_users_group_permission(
                repo=repo_name, group_name=request.POST['users_group_id']
            )
            Session.commit()
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during deletion of repository'
                      ' users groups'),
                    category='error')
            raise HTTPInternalServerError()

    @HasPermissionAllDecorator('hg.admin')
    def repo_stats(self, repo_name):
        """
        DELETE an existing repository statistics

        :param repo_name:
        """

        try:
            RepoModel().delete_stats(repo_name)
            Session.commit()
        except Exception, e:
            h.flash(_('An error occurred during deletion of repository stats'),
                    category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasPermissionAllDecorator('hg.admin')
    def repo_cache(self, repo_name):
        """
        INVALIDATE existing repository cache

        :param repo_name:
        """

        try:
            ScmModel().mark_for_invalidation(repo_name)
            Session.commit()
        except Exception, e:
            h.flash(_('An error occurred during cache invalidation'),
                    category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasPermissionAllDecorator('hg.admin')
    def repo_public_journal(self, repo_name):
        """
        Set's this repository to be visible in public journal,
        in other words assing default user to follow this repo

        :param repo_name:
        """

        cur_token = request.POST.get('auth_token')
        token = get_token()
        if cur_token == token:
            try:
                repo_id = Repository.get_by_repo_name(repo_name).repo_id
                user_id = User.get_by_username('default').user_id
                self.scm_model.toggle_following_repo(repo_id, user_id)
                h.flash(_('Updated repository visibility in public journal'),
                        category='success')
                Session.commit()
            except:
                h.flash(_('An error occurred during setting this'
                          ' repository in public journal'),
                        category='error')

        else:
            h.flash(_('Token mismatch'), category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasPermissionAllDecorator('hg.admin')
    def repo_pull(self, repo_name):
        """
        Runs task to update given repository with remote changes,
        ie. make pull on remote location

        :param repo_name:
        """
        try:
            ScmModel().pull_changes(repo_name, self.rhodecode_user.username)
            h.flash(_('Pulled from remote location'), category='success')
        except Exception, e:
            h.flash(_('An error occurred during pull from remote location'),
                    category='error')

        return redirect(url('edit_repo', repo_name=repo_name))

    @HasPermissionAllDecorator('hg.admin')
    def repo_as_fork(self, repo_name):
        """
        Mark given repository as a fork of another

        :param repo_name:
        """
        try:
            fork_id = request.POST.get('id_fork_of')
            repo = ScmModel().mark_as_fork(repo_name, fork_id,
                                    self.rhodecode_user.username)
            fork = repo.fork.repo_name if repo.fork else _('Nothing')
            Session.commit()
            h.flash(_('Marked repo %s as fork of %s' % (repo_name,fork)),
                    category='success')
        except Exception, e:
            raise
            h.flash(_('An error occurred during this operation'),
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
        defaults = self.__load_data(repo_name)

        return htmlfill.render(
            render('admin/repos/repo_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

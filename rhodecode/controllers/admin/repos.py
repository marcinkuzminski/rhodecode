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

from webob.exc import HTTPInternalServerError, HTTPForbidden
from pylons import request, session, tmpl_context as c, url
from pylons.controllers.util import redirect
from pylons.i18n.translation import _
from sqlalchemy.exc import IntegrityError

import rhodecode
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator, \
    HasPermissionAnyDecorator, HasRepoPermissionAllDecorator, NotAnonymous,\
    HasPermissionAny, HasReposGroupPermissionAny, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.utils import action_logger, repo_name_slug
from rhodecode.lib.helpers import get_token
from rhodecode.model.meta import Session
from rhodecode.model.db import User, Repository, UserFollowing, RepoGroup,\
    RhodeCodeSetting, RepositoryField
from rhodecode.model.forms import RepoForm, RepoFieldForm, RepoPermsForm
from rhodecode.model.scm import ScmModel, RepoGroupList, RepoList
from rhodecode.model.repo import RepoModel
from rhodecode.lib.compat import json
from sqlalchemy.sql.expression import func
from rhodecode.lib.exceptions import AttachedForksError
from rhodecode.lib.utils2 import safe_int

log = logging.getLogger(__name__)


class ReposController(BaseRepoController):
    """
    REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('repo', 'repos')

    @LoginRequired()
    def __before__(self):
        super(ReposController, self).__before__()

    def __load_defaults(self):
        acl_groups = RepoGroupList(RepoGroup.query().all(),
                               perm_set=['group.write', 'group.admin'])
        c.repo_groups = RepoGroup.groups_choices(groups=acl_groups)
        c.repo_groups_choices = map(lambda k: unicode(k[0]), c.repo_groups)

        repo_model = RepoModel()
        c.users_array = repo_model.get_users_js()
        c.users_groups_array = repo_model.get_users_groups_js()
        choices, c.landing_revs = ScmModel().get_repo_landing_revs()
        c.landing_revs_choices = choices

    def __load_data(self, repo_name=None):
        """
        Load defaults settings for edit, and update

        :param repo_name:
        """
        self.__load_defaults()

        c.repo_info = db_repo = Repository.get_by_repo_name(repo_name)
        repo = db_repo.scm_instance

        if c.repo_info is None:
            h.not_mapped_error(repo_name)
            return redirect(url('repos'))

        ##override defaults for exact repo info here git/hg etc
        choices, c.landing_revs = ScmModel().get_repo_landing_revs(c.repo_info)
        c.landing_revs_choices = choices

        c.default_user_id = User.get_default_user().user_id
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

        c.repo_fields = RepositoryField.query()\
            .filter(RepositoryField.repository == db_repo).all()

        defaults = RepoModel()._get_defaults(repo_name)

        _repos = Repository.query().order_by(Repository.repo_name).all()
        read_access_repos = RepoList(_repos)
        c.repos_list = [('', _('--REMOVE FORK--'))]
        c.repos_list += [(x.repo_id, x.repo_name)
                         for x in read_access_repos
                         if x.repo_id != c.repo_info.repo_id]

        defaults['id_fork_of'] = db_repo.fork.repo_id if db_repo.fork else ''
        return defaults

    def index(self, format='html'):
        """GET /repos: All items in the collection"""
        # url('repos')
        repo_list = Repository.query()\
                                .order_by(func.lower(Repository.repo_name))\
                                .all()

        c.repos_list = RepoList(repo_list, perm_set=['repository.admin'])
        repos_data = RepoModel().get_repos_as_dict(repos_list=c.repos_list,
                                                   admin=True,
                                                   super_user_actions=True)
        #json used to render the grid
        c.data = json.dumps(repos_data)

        return render('admin/repos/repos.html')

    @NotAnonymous()
    def create(self):
        """
        POST /repos: Create a new item"""
        # url('repos')

        self.__load_defaults()
        form_result = {}
        try:
            form_result = RepoForm(repo_groups=c.repo_groups_choices,
                                   landing_revs=c.landing_revs_choices)()\
                            .to_python(dict(request.POST))

            new_repo = RepoModel().create(form_result,
                                          self.rhodecode_user.user_id)
            if form_result['clone_uri']:
                h.flash(_('Created repository %s from %s') \
                    % (form_result['repo_name'], form_result['clone_uri']),
                    category='success')
            else:
                repo_url = h.link_to(form_result['repo_name'],
                    h.url('summary_home', repo_name=form_result['repo_name_full']))
                h.flash(h.literal(_('Created repository %s') % repo_url),
                        category='success')

            if request.POST.get('user_created'):
                # created by regular non admin user
                action_logger(self.rhodecode_user, 'user_created_repo',
                              form_result['repo_name_full'], self.ip_addr,
                              self.sa)
            else:
                action_logger(self.rhodecode_user, 'admin_created_repo',
                              form_result['repo_name_full'], self.ip_addr,
                              self.sa)
            Session().commit()
        except formencode.Invalid, errors:
            return htmlfill.render(
                render('admin/repos/repo_add.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")

        except Exception:
            log.error(traceback.format_exc())
            msg = _('Error creating repository %s') \
                    % form_result.get('repo_name')
            h.flash(msg, category='error')
            if c.rhodecode_user.is_admin:
                return redirect(url('repos'))
            return redirect(url('home'))
        #redirect to our new repo !
        return redirect(url('summary_home', repo_name=new_repo.repo_name))

    @NotAnonymous()
    def create_repository(self):
        """GET /_admin/create_repository: Form to create a new item"""
        new_repo = request.GET.get('repo', '')
        parent_group = request.GET.get('parent_group')
        if not HasPermissionAny('hg.admin', 'hg.create.repository')():
            #you're not super admin nor have global create permissions,
            #but maybe you have at least write permission to a parent group ?
            _gr = RepoGroup.get(parent_group)
            gr_name = _gr.group_name if _gr else None
            if not HasReposGroupPermissionAny('group.admin', 'group.write')(group_name=gr_name):
                raise HTTPForbidden

        acl_groups = RepoGroupList(RepoGroup.query().all(),
                               perm_set=['group.write', 'group.admin'])
        c.repo_groups = RepoGroup.groups_choices(groups=acl_groups)
        c.repo_groups_choices = map(lambda k: unicode(k[0]), c.repo_groups)
        choices, c.landing_revs = ScmModel().get_repo_landing_revs()

        c.new_repo = repo_name_slug(new_repo)

        ## apply the defaults from defaults page
        defaults = RhodeCodeSetting.get_default_repo_settings(strip_prefix=True)
        if parent_group:
            defaults.update({'repo_group': parent_group})

        return htmlfill.render(
            render('admin/repos/repo_add.html'),
            defaults=defaults,
            errors={},
            prefix_error=False,
            encoding="UTF-8"
        )

    @HasRepoPermissionAllDecorator('repository.admin')
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
        #override the choices with extracted revisions !
        choices, c.landing_revs = ScmModel().get_repo_landing_revs(repo_name)
        c.landing_revs_choices = choices
        repo = Repository.get_by_repo_name(repo_name)
        old_data = {
            'repo_name': repo_name,
            'repo_group': repo.group.get_dict() if repo.group else {},
            'repo_type': repo.repo_type,
        }
        _form = RepoForm(edit=True, old_data=old_data,
                         repo_groups=c.repo_groups_choices,
                         landing_revs=c.landing_revs_choices)()

        try:
            form_result = _form.to_python(dict(request.POST))
            repo = repo_model.update(repo_name, **form_result)
            ScmModel().mark_for_invalidation(repo_name)
            h.flash(_('Repository %s updated successfully') % repo_name,
                    category='success')
            changed_name = repo.repo_name
            action_logger(self.rhodecode_user, 'admin_updated_repo',
                              changed_name, self.ip_addr, self.sa)
            Session().commit()
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
            h.flash(_('Error occurred during update of repository %s') \
                    % repo_name, category='error')
        return redirect(url('edit_repo', repo_name=changed_name))

    @HasRepoPermissionAllDecorator('repository.admin')
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
            h.not_mapped_error(repo_name)
            return redirect(url('repos'))
        try:
            _forks = repo.forks.count()
            handle_forks = None
            if _forks and request.POST.get('forks'):
                do = request.POST['forks']
                if do == 'detach_forks':
                    handle_forks = 'detach'
                    h.flash(_('Detached %s forks') % _forks, category='success')
                elif do == 'delete_forks':
                    handle_forks = 'delete'
                    h.flash(_('Deleted %s forks') % _forks, category='success')
            repo_model.delete(repo, forks=handle_forks)
            action_logger(self.rhodecode_user, 'admin_deleted_repo',
                  repo_name, self.ip_addr, self.sa)
            ScmModel().mark_for_invalidation(repo_name)
            h.flash(_('Deleted repository %s') % repo_name, category='success')
            Session().commit()
        except AttachedForksError:
            h.flash(_('Cannot delete %s it still contains attached forks')
                        % repo_name, category='warning')

        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during deletion of %s') % repo_name,
                    category='error')

        return redirect(url('repos'))

    @HasRepoPermissionAllDecorator('repository.admin')
    def set_repo_perm_member(self, repo_name):
        form = RepoPermsForm()().to_python(request.POST)
        RepoModel()._update_permissions(repo_name, form['perms_new'],
                                        form['perms_updates'])
        #TODO: implement this
        #action_logger(self.rhodecode_user, 'admin_changed_repo_permissions',
        #              repo_name, self.ip_addr, self.sa)
        Session().commit()
        h.flash(_('Repository permissions updated'), category='success')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasRepoPermissionAllDecorator('repository.admin')
    def delete_repo_perm_member(self, repo_name):
        """
        DELETE an existing repository permission user

        :param repo_name:
        """
        try:
            obj_type = request.POST.get('obj_type')
            obj_id = None
            if obj_type == 'user':
                obj_id = safe_int(request.POST.get('user_id'))
            elif obj_type == 'user_group':
                obj_id = safe_int(request.POST.get('user_group_id'))

            if obj_type == 'user':
                RepoModel().revoke_user_permission(repo=repo_name, user=obj_id)
            elif obj_type == 'user_group':
                RepoModel().revoke_users_group_permission(
                    repo=repo_name, group_name=obj_id
                )
            #TODO: implement this
            #action_logger(self.rhodecode_user, 'admin_revoked_repo_permissions',
            #              repo_name, self.ip_addr, self.sa)
            Session().commit()
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during revoking of permission'),
                    category='error')
            raise HTTPInternalServerError()

    @HasRepoPermissionAllDecorator('repository.admin')
    def repo_stats(self, repo_name):
        """
        DELETE an existing repository statistics

        :param repo_name:
        """

        try:
            RepoModel().delete_stats(repo_name)
            Session().commit()
        except Exception, e:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during deletion of repository stats'),
                    category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasRepoPermissionAllDecorator('repository.admin')
    def repo_cache(self, repo_name):
        """
        INVALIDATE existing repository cache

        :param repo_name:
        """

        try:
            ScmModel().mark_for_invalidation(repo_name)
            Session().commit()
        except Exception, e:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during cache invalidation'),
                    category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasRepoPermissionAllDecorator('repository.admin')
    def repo_locking(self, repo_name):
        """
        Unlock repository when it is locked !

        :param repo_name:
        """

        try:
            repo = Repository.get_by_repo_name(repo_name)
            if request.POST.get('set_lock'):
                Repository.lock(repo, c.rhodecode_user.user_id)
            elif request.POST.get('set_unlock'):
                Repository.unlock(repo)
        except Exception, e:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during unlocking'),
                    category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasRepoPermissionAnyDecorator('repository.write', 'repository.admin')
    def toggle_locking(self, repo_name):
        """
        Toggle locking of repository by simple GET call to url

        :param repo_name:
        """

        try:
            repo = Repository.get_by_repo_name(repo_name)

            if repo.enable_locking:
                if repo.locked[0]:
                    Repository.unlock(repo)
                    action = _('Unlocked')
                else:
                    Repository.lock(repo, c.rhodecode_user.user_id)
                    action = _('Locked')

                h.flash(_('Repository has been %s') % action,
                        category='success')
        except Exception, e:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during unlocking'),
                    category='error')
        return redirect(url('summary_home', repo_name=repo_name))

    @HasRepoPermissionAllDecorator('repository.admin')
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
                user_id = User.get_default_user().user_id
                self.scm_model.toggle_following_repo(repo_id, user_id)
                h.flash(_('Updated repository visibility in public journal'),
                        category='success')
                Session().commit()
            except Exception:
                h.flash(_('An error occurred during setting this'
                          ' repository in public journal'),
                        category='error')

        else:
            h.flash(_('Token mismatch'), category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasRepoPermissionAllDecorator('repository.admin')
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
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during pull from remote location'),
                    category='error')

        return redirect(url('edit_repo', repo_name=repo_name))

    @HasRepoPermissionAllDecorator('repository.admin')
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
            Session().commit()
            h.flash(_('Marked repo %s as fork of %s') % (repo_name, fork),
                    category='success')
        except Exception, e:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during this operation'),
                    category='error')

        return redirect(url('edit_repo', repo_name=repo_name))

    @HasPermissionAllDecorator('hg.admin')
    def show(self, repo_name, format='html'):
        """GET /repos/repo_name: Show a specific item"""
        # url('repo', repo_name=ID)

    @HasRepoPermissionAllDecorator('repository.admin')
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

    @HasPermissionAllDecorator('hg.admin')
    def create_repo_field(self, repo_name):
        try:
            form_result = RepoFieldForm()().to_python(dict(request.POST))
            new_field = RepositoryField()
            new_field.repository = Repository.get_by_repo_name(repo_name)
            new_field.field_key = form_result['new_field_key']
            new_field.field_type = form_result['new_field_type']  # python type
            new_field.field_value = form_result['new_field_value']  # set initial blank value
            new_field.field_desc = form_result['new_field_desc']
            new_field.field_label = form_result['new_field_label']
            Session().add(new_field)
            Session().commit()

        except Exception, e:
            log.error(traceback.format_exc())
            msg = _('An error occurred during creation of field')
            if isinstance(e, formencode.Invalid):
                msg += ". " + e.msg
            h.flash(msg, category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

    @HasPermissionAllDecorator('hg.admin')
    def delete_repo_field(self, repo_name, field_id):
        field = RepositoryField.get_or_404(field_id)
        try:
            Session().delete(field)
            Session().commit()
        except Exception, e:
            log.error(traceback.format_exc())
            msg = _('An error occurred during removal of field')
            h.flash(msg, category='error')
        return redirect(url('edit_repo', repo_name=repo_name))

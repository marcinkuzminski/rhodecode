# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    settings controller for rhodecode admin

    :created_on: Jul 14, 2010
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
import pkg_resources
import platform

from sqlalchemy import func
from formencode import htmlfill
from pylons import request, session, tmpl_context as c, url, config
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator, \
    HasPermissionAnyDecorator, NotAnonymous
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.celerylib import tasks, run_task
from rhodecode.lib.utils import repo2db_mapper, invalidate_cache, \
    set_rhodecode_config, repo_name_slug
from rhodecode.model.db import RhodeCodeUi, Repository, RepoGroup, \
    RhodeCodeSetting, PullRequest, PullRequestReviewers
from rhodecode.model.forms import UserForm, ApplicationSettingsForm, \
    ApplicationUiSettingsForm
from rhodecode.model.scm import ScmModel
from rhodecode.model.user import UserModel
from rhodecode.model.db import User
from rhodecode.model.notification import EmailNotificationModel
from rhodecode.model.meta import Session
from pylons.decorators import jsonify
from rhodecode.model.pull_request import PullRequestModel

log = logging.getLogger(__name__)


class SettingsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('setting', 'settings', controller='admin/settings',
    #         path_prefix='/admin', name_prefix='admin_')

    @LoginRequired()
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        c.modules = sorted([(p.project_name, p.version)
                            for p in pkg_resources.working_set],
                           key=lambda k: k[0].lower())
        c.py_version = platform.python_version()
        c.platform = platform.platform()
        super(SettingsController, self).__before__()

    @HasPermissionAllDecorator('hg.admin')
    def index(self, format='html'):
        """GET /admin/settings: All items in the collection"""
        # url('admin_settings')

        defaults = RhodeCodeSetting.get_app_settings()
        defaults.update(self.get_hg_ui_settings())

        return htmlfill.render(
            render('admin/settings/settings.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    @HasPermissionAllDecorator('hg.admin')
    def create(self):
        """POST /admin/settings: Create a new item"""
        # url('admin_settings')

    @HasPermissionAllDecorator('hg.admin')
    def new(self, format='html'):
        """GET /admin/settings/new: Form to create a new item"""
        # url('admin_new_setting')

    @HasPermissionAllDecorator('hg.admin')
    def update(self, setting_id):
        """PUT /admin/settings/setting_id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('admin_setting', setting_id=ID),
        #           method='put')
        # url('admin_setting', setting_id=ID)
        if setting_id == 'mapping':
            rm_obsolete = request.POST.get('destroy', False)
            log.debug('Rescanning directories with destroy=%s' % rm_obsolete)
            initial = ScmModel().repo_scan()
            log.debug('invalidating all repositories')
            for repo_name in initial.keys():
                invalidate_cache('get_repo_cached_%s' % repo_name)

            added, removed = repo2db_mapper(initial, rm_obsolete)

            h.flash(_('Repositories successfully'
                      ' rescanned added: %s,removed: %s') % (added, removed),
                    category='success')

        if setting_id == 'whoosh':
            repo_location = self.get_hg_ui_settings()['paths_root_path']
            full_index = request.POST.get('full_index', False)
            run_task(tasks.whoosh_index, repo_location, full_index)

            h.flash(_('Whoosh reindex task scheduled'), category='success')
        if setting_id == 'global':

            application_form = ApplicationSettingsForm()()
            try:
                form_result = application_form.to_python(dict(request.POST))

                try:
                    hgsettings1 = RhodeCodeSetting.get_by_name('title')
                    hgsettings1.app_settings_value = \
                        form_result['rhodecode_title']

                    hgsettings2 = RhodeCodeSetting.get_by_name('realm')
                    hgsettings2.app_settings_value = \
                        form_result['rhodecode_realm']

                    hgsettings3 = RhodeCodeSetting.get_by_name('ga_code')
                    hgsettings3.app_settings_value = \
                        form_result['rhodecode_ga_code']

                    self.sa.add(hgsettings1)
                    self.sa.add(hgsettings2)
                    self.sa.add(hgsettings3)
                    self.sa.commit()
                    set_rhodecode_config(config)
                    h.flash(_('Updated application settings'),
                            category='success')

                except Exception:
                    log.error(traceback.format_exc())
                    h.flash(_('error occurred during updating '
                              'application settings'),
                            category='error')

                    self.sa.rollback()

            except formencode.Invalid, errors:
                return htmlfill.render(
                     render('admin/settings/settings.html'),
                     defaults=errors.value,
                     errors=errors.error_dict or {},
                     prefix_error=False,
                     encoding="UTF-8")

        if setting_id == 'mercurial':
            application_form = ApplicationUiSettingsForm()()
            try:
                form_result = application_form.to_python(dict(request.POST))
                # fix namespaces for hooks
                _f = lambda s: s.replace('.', '_')
                try:

                    hgsettings1 = self.sa.query(RhodeCodeUi)\
                    .filter(RhodeCodeUi.ui_key == 'push_ssl').one()
                    hgsettings1.ui_value = form_result['web_push_ssl']

                    hgsettings2 = self.sa.query(RhodeCodeUi)\
                    .filter(RhodeCodeUi.ui_key == '/').one()
                    hgsettings2.ui_value = form_result['paths_root_path']

                    #HOOKS
                    hgsettings3 = self.sa.query(RhodeCodeUi)\
                    .filter(RhodeCodeUi.ui_key == RhodeCodeUi.HOOK_UPDATE)\
                    .one()
                    hgsettings3.ui_active = bool(form_result[_f('hooks_%s' %
                                                 RhodeCodeUi.HOOK_UPDATE)])

                    hgsettings4 = self.sa.query(RhodeCodeUi)\
                    .filter(RhodeCodeUi.ui_key == RhodeCodeUi.HOOK_REPO_SIZE)\
                    .one()
                    hgsettings4.ui_active = bool(form_result[_f('hooks_%s' %
                                                 RhodeCodeUi.HOOK_REPO_SIZE)])

                    hgsettings5 = self.sa.query(RhodeCodeUi)\
                    .filter(RhodeCodeUi.ui_key == RhodeCodeUi.HOOK_PUSH)\
                    .one()
                    hgsettings5.ui_active = bool(form_result[_f('hooks_%s' %
                                                 RhodeCodeUi.HOOK_PUSH)])

                    hgsettings6 = self.sa.query(RhodeCodeUi)\
                    .filter(RhodeCodeUi.ui_key == RhodeCodeUi.HOOK_PULL)\
                    .one()
                    hgsettings6.ui_active = bool(form_result[_f('hooks_%s' %
                                                 RhodeCodeUi.HOOK_PULL)])

                    self.sa.add(hgsettings1)
                    self.sa.add(hgsettings2)
                    self.sa.add(hgsettings3)
                    self.sa.add(hgsettings4)
                    self.sa.add(hgsettings5)
                    self.sa.add(hgsettings6)
                    self.sa.commit()

                    h.flash(_('Updated mercurial settings'),
                            category='success')

                except:
                    log.error(traceback.format_exc())
                    h.flash(_('error occurred during updating '
                              'application settings'), category='error')

                    self.sa.rollback()

            except formencode.Invalid, errors:
                return htmlfill.render(
                     render('admin/settings/settings.html'),
                     defaults=errors.value,
                     errors=errors.error_dict or {},
                     prefix_error=False,
                     encoding="UTF-8")

        if setting_id == 'hooks':
            ui_key = request.POST.get('new_hook_ui_key')
            ui_value = request.POST.get('new_hook_ui_value')
            try:

                if ui_value and ui_key:
                    RhodeCodeUi.create_or_update_hook(ui_key, ui_value)
                    h.flash(_('Added new hook'),
                            category='success')

                # check for edits
                update = False
                _d = request.POST.dict_of_lists()
                for k, v in zip(_d.get('hook_ui_key', []),
                                _d.get('hook_ui_value_new', [])):
                    RhodeCodeUi.create_or_update_hook(k, v)
                    update = True

                if update:
                    h.flash(_('Updated hooks'), category='success')
                self.sa.commit()
            except:
                log.error(traceback.format_exc())
                h.flash(_('error occurred during hook creation'),
                        category='error')

            return redirect(url('admin_edit_setting', setting_id='hooks'))

        if setting_id == 'email':
            test_email = request.POST.get('test_email')
            test_email_subj = 'RhodeCode TestEmail'
            test_email_body = 'RhodeCode Email test'

            test_email_html_body = EmailNotificationModel()\
                .get_email_tmpl(EmailNotificationModel.TYPE_DEFAULT,
                                body=test_email_body)

            recipients = [test_email] if [test_email] else None

            run_task(tasks.send_email, recipients, test_email_subj,
                     test_email_body, test_email_html_body)

            h.flash(_('Email task created'), category='success')
        return redirect(url('admin_settings'))

    @HasPermissionAllDecorator('hg.admin')
    def delete(self, setting_id):
        """DELETE /admin/settings/setting_id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('admin_setting', setting_id=ID),
        #           method='delete')
        # url('admin_setting', setting_id=ID)
        if setting_id == 'hooks':
            hook_id = request.POST.get('hook_id')
            RhodeCodeUi.delete(hook_id)
            self.sa.commit()

    @HasPermissionAllDecorator('hg.admin')
    def show(self, setting_id, format='html'):
        """
        GET /admin/settings/setting_id: Show a specific item"""
        # url('admin_setting', setting_id=ID)

    @HasPermissionAllDecorator('hg.admin')
    def edit(self, setting_id, format='html'):
        """
        GET /admin/settings/setting_id/edit: Form to
        edit an existing item"""
        # url('admin_edit_setting', setting_id=ID)

        c.hooks = RhodeCodeUi.get_builtin_hooks()
        c.custom_hooks = RhodeCodeUi.get_custom_hooks()

        return htmlfill.render(
            render('admin/settings/hooks.html'),
            defaults={},
            encoding="UTF-8",
            force_defaults=False
        )

    @NotAnonymous()
    def my_account(self):
        """
        GET /_admin/my_account Displays info about my account
        """
        # url('admin_settings_my_account')

        c.user = User.get(self.rhodecode_user.user_id)
        all_repos = self.sa.query(Repository)\
                     .filter(Repository.user_id == c.user.user_id)\
                     .order_by(func.lower(Repository.repo_name)).all()

        c.user_repos = ScmModel().get_repos(all_repos)

        if c.user.username == 'default':
            h.flash(_("You can't edit this user since it's"
              " crucial for entire application"), category='warning')
            return redirect(url('users'))

        defaults = c.user.get_dict()

        c.form = htmlfill.render(
            render('admin/users/user_edit_my_account_form.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
        return render('admin/users/user_edit_my_account.html')

    def my_account_update(self):
        """PUT /_admin/my_account_update: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('admin_settings_my_account_update'),
        #           method='put')
        # url('admin_settings_my_account_update', id=ID)
        uid = self.rhodecode_user.user_id
        email = self.rhodecode_user.email
        _form = UserForm(edit=True,
                         old_data={'user_id': uid, 'email': email})()
        form_result = {}
        try:
            form_result = _form.to_python(dict(request.POST))
            UserModel().update_my_account(uid, form_result)
            h.flash(_('Your account was updated successfully'),
                    category='success')
            Session.commit()
        except formencode.Invalid, errors:
            c.user = User.get(self.rhodecode_user.user_id)

            c.form = htmlfill.render(
                render('admin/users/user_edit_my_account_form.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
            return render('admin/users/user_edit_my_account.html')
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during update of user %s') \
                    % form_result.get('username'), category='error')

        return redirect(url('my_account'))

    def my_account_my_repos(self):
        all_repos = self.sa.query(Repository)\
            .filter(Repository.user_id == self.rhodecode_user.user_id)\
            .order_by(func.lower(Repository.repo_name))\
            .all()
        c.user_repos = ScmModel().get_repos(all_repos)
        return render('admin/users/user_edit_my_account_repos.html')

    def my_account_my_pullrequests(self):
        c.my_pull_requests = PullRequest.query()\
                                .filter(PullRequest.user_id==
                                        self.rhodecode_user.user_id)\
                                .all()
        c.participate_in_pull_requests = \
            [x.pull_request for x in PullRequestReviewers.query()\
                                    .filter(PullRequestReviewers.user_id==
                                            self.rhodecode_user.user_id)\
                                    .all()]
        return render('admin/users/user_edit_my_account_pullrequests.html')

    @NotAnonymous()
    @HasPermissionAnyDecorator('hg.admin', 'hg.create.repository')
    def create_repository(self):
        """GET /_admin/create_repository: Form to create a new item"""

        c.repo_groups = RepoGroup.groups_choices()
        c.repo_groups_choices = map(lambda k: unicode(k[0]), c.repo_groups)
        choices, c.landing_revs = ScmModel().get_repo_landing_revs()

        new_repo = request.GET.get('repo', '')
        c.new_repo = repo_name_slug(new_repo)

        return render('admin/repos/repo_add_create_repository.html')

    def get_hg_ui_settings(self):
        ret = self.sa.query(RhodeCodeUi).all()

        if not ret:
            raise Exception('Could not get application ui settings !')
        settings = {}
        for each in ret:
            k = each.ui_key
            v = each.ui_value
            if k == '/':
                k = 'root_path'

            if k.find('.') != -1:
                k = k.replace('.', '_')

            if each.ui_section == 'hooks':
                v = each.ui_active

            settings[each.ui_section + '_' + k] = v

        return settings

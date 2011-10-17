import logging
import traceback
import formencode

from formencode import htmlfill
from operator import itemgetter

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from sqlalchemy.exc import IntegrityError

from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAnyDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.model.db import Group
from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.forms import ReposGroupForm

log = logging.getLogger(__name__)


class ReposGroupsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('repos_group', 'repos_groups')

    @LoginRequired()
    def __before__(self):
        super(ReposGroupsController, self).__before__()

    def __load_defaults(self):
        c.repo_groups = Group.groups_choices()
        c.repo_groups_choices = map(lambda k: unicode(k[0]), c.repo_groups)

    def __load_data(self, group_id):
        """
        Load defaults settings for edit, and update

        :param group_id:
        """
        self.__load_defaults()

        repo_group = Group.get(group_id)

        data = repo_group.get_dict()

        data['group_name'] = repo_group.name

        return data

    @HasPermissionAnyDecorator('hg.admin')
    def index(self, format='html'):
        """GET /repos_groups: All items in the collection"""
        # url('repos_groups')

        sk = lambda g:g.parents[0].group_name if g.parents else g.group_name
        c.groups = sorted(Group.query().all(), key=sk)
        return render('admin/repos_groups/repos_groups_show.html')

    @HasPermissionAnyDecorator('hg.admin')
    def create(self):
        """POST /repos_groups: Create a new item"""
        # url('repos_groups')
        self.__load_defaults()
        repos_group_model = ReposGroupModel()
        repos_group_form = ReposGroupForm(available_groups=
                                          c.repo_groups_choices)()
        try:
            form_result = repos_group_form.to_python(dict(request.POST))
            repos_group_model.create(form_result)
            h.flash(_('created repos group %s') \
                    % form_result['group_name'], category='success')
            #TODO: in futureaction_logger(, '', '', '', self.sa)
        except formencode.Invalid, errors:

            return htmlfill.render(
                render('admin/repos_groups/repos_groups_add.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during creation of repos group %s') \
                    % request.POST.get('group_name'), category='error')

        return redirect(url('repos_groups'))


    @HasPermissionAnyDecorator('hg.admin')
    def new(self, format='html'):
        """GET /repos_groups/new: Form to create a new item"""
        # url('new_repos_group')
        self.__load_defaults()
        return render('admin/repos_groups/repos_groups_add.html')

    @HasPermissionAnyDecorator('hg.admin')
    def update(self, id):
        """PUT /repos_groups/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('repos_group', id=ID),
        #           method='put')
        # url('repos_group', id=ID)

        self.__load_defaults()
        c.repos_group = Group.get(id)

        repos_group_model = ReposGroupModel()
        repos_group_form = ReposGroupForm(edit=True,
                                          old_data=c.repos_group.get_dict(),
                                          available_groups=
                                            c.repo_groups_choices)()
        try:
            form_result = repos_group_form.to_python(dict(request.POST))
            repos_group_model.update(id, form_result)
            h.flash(_('updated repos group %s') \
                    % form_result['group_name'], category='success')
            #TODO: in futureaction_logger(, '', '', '', self.sa)
        except formencode.Invalid, errors:

            return htmlfill.render(
                render('admin/repos_groups/repos_groups_edit.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during update of repos group %s') \
                    % request.POST.get('group_name'), category='error')

        return redirect(url('repos_groups'))


    @HasPermissionAnyDecorator('hg.admin')
    def delete(self, id):
        """DELETE /repos_groups/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('repos_group', id=ID),
        #           method='delete')
        # url('repos_group', id=ID)

        repos_group_model = ReposGroupModel()
        gr = Group.get(id)
        repos = gr.repositories.all()
        if repos:
            h.flash(_('This group contains %s repositores and cannot be '
                      'deleted' % len(repos)),
                    category='error')
            return redirect(url('repos_groups'))

        try:
            repos_group_model.delete(id)
            h.flash(_('removed repos group %s' % gr.group_name), category='success')
            #TODO: in future action_logger(, '', '', '', self.sa)
        except IntegrityError, e:
            if e.message.find('groups_group_parent_id_fkey'):
                log.error(traceback.format_exc())
                h.flash(_('Cannot delete this group it still contains '
                          'subgroups'),
                        category='warning')
            else:
                log.error(traceback.format_exc())
                h.flash(_('error occurred during deletion of repos '
                          'group %s' % gr.group_name), category='error')

        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during deletion of repos '
                      'group %s' % gr.group_name), category='error')

        return redirect(url('repos_groups'))

    def show_by_name(self, group_name):
        id_ = Group.get_by_group_name(group_name).group_id
        return self.show(id_)

    def show(self, id, format='html'):
        """GET /repos_groups/id: Show a specific item"""
        # url('repos_group', id=ID)

        c.group = Group.get(id)

        if c.group:
            c.group_repos = c.group.repositories.all()
        else:
            return redirect(url('home'))

        #overwrite our cached list with current filter
        gr_filter = c.group_repos
        c.cached_repo_list = self.scm_model.get_repos(all_repos=gr_filter)

        c.repos_list = c.cached_repo_list

        c.repo_cnt = 0

        c.groups = self.sa.query(Group).order_by(Group.group_name)\
            .filter(Group.group_parent_id == id).all()

        return render('admin/repos_groups/repos_groups.html')

    @HasPermissionAnyDecorator('hg.admin')
    def edit(self, id, format='html'):
        """GET /repos_groups/id/edit: Form to edit an existing item"""
        # url('edit_repos_group', id=ID)

        id_ = int(id)

        c.repos_group = Group.get(id_)
        defaults = self.__load_data(id_)

        # we need to exclude this group from the group list for editing
        c.repo_groups = filter(lambda x:x[0] != id_, c.repo_groups)

        return htmlfill.render(
            render('admin/repos_groups/repos_groups_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )



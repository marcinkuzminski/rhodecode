# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.changeset
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    changeset controller for pylons showoing changes beetween
    revisions

    :created_on: Apr 25, 2010
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
from collections import defaultdict
from webob.exc import HTTPForbidden

from pylons import tmpl_context as c, url, request, response
from pylons.i18n.translation import _
from pylons.controllers.util import redirect
from pylons.decorators import jsonify

from rhodecode.lib.vcs.exceptions import RepositoryError, ChangesetError, \
    ChangesetDoesNotExistError
from rhodecode.lib.vcs.nodes import FileNode

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.utils import action_logger
from rhodecode.lib.compat import OrderedDict
from rhodecode.lib import diffs
from rhodecode.model.db import ChangesetComment, ChangesetStatus
from rhodecode.model.comment import ChangesetCommentsModel
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.meta import Session
from rhodecode.lib.diffs import wrapped_diff
from rhodecode.model.repo import RepoModel
from rhodecode.lib.exceptions import StatusChangeOnClosedPullRequestError
from rhodecode.lib.vcs.backends.base import EmptyChangeset

log = logging.getLogger(__name__)


def _update_with_GET(params, GET):
    for k in ['diff1', 'diff2', 'diff']:
        params[k] += GET.getall(k)


def anchor_url(revision, path, GET):
    fid = h.FID(revision, path)
    return h.url.current(anchor=fid, **dict(GET))


def get_ignore_ws(fid, GET):
    ig_ws_global = GET.get('ignorews')
    ig_ws = filter(lambda k: k.startswith('WS'), GET.getall(fid))
    if ig_ws:
        try:
            return int(ig_ws[0].split(':')[-1])
        except:
            pass
    return ig_ws_global


def _ignorews_url(GET, fileid=None):
    fileid = str(fileid) if fileid else None
    params = defaultdict(list)
    _update_with_GET(params, GET)
    lbl = _('show white space')
    ig_ws = get_ignore_ws(fileid, GET)
    ln_ctx = get_line_ctx(fileid, GET)
    # global option
    if fileid is None:
        if ig_ws is None:
            params['ignorews'] += [1]
            lbl = _('ignore white space')
        ctx_key = 'context'
        ctx_val = ln_ctx
    # per file options
    else:
        if ig_ws is None:
            params[fileid] += ['WS:1']
            lbl = _('ignore white space')

        ctx_key = fileid
        ctx_val = 'C:%s' % ln_ctx
    # if we have passed in ln_ctx pass it along to our params
    if ln_ctx:
        params[ctx_key] += [ctx_val]

    params['anchor'] = fileid
    img = h.image(h.url('/images/icons/text_strikethrough.png'), lbl, class_='icon')
    return h.link_to(img, h.url.current(**params), title=lbl, class_='tooltip')


def get_line_ctx(fid, GET):
    ln_ctx_global = GET.get('context')
    ln_ctx = filter(lambda k: k.startswith('C'), GET.getall(fid))

    if ln_ctx:
        retval = ln_ctx[0].split(':')[-1]
    else:
        retval = ln_ctx_global

    try:
        return int(retval)
    except:
        return


def _context_url(GET, fileid=None):
    """
    Generates url for context lines

    :param fileid:
    """

    fileid = str(fileid) if fileid else None
    ig_ws = get_ignore_ws(fileid, GET)
    ln_ctx = (get_line_ctx(fileid, GET) or 3) * 2

    params = defaultdict(list)
    _update_with_GET(params, GET)

    # global option
    if fileid is None:
        if ln_ctx > 0:
            params['context'] += [ln_ctx]

        if ig_ws:
            ig_ws_key = 'ignorews'
            ig_ws_val = 1

    # per file option
    else:
        params[fileid] += ['C:%s' % ln_ctx]
        ig_ws_key = fileid
        ig_ws_val = 'WS:%s' % 1

    if ig_ws:
        params[ig_ws_key] += [ig_ws_val]

    lbl = _('%s line context') % ln_ctx

    params['anchor'] = fileid
    img = h.image(h.url('/images/icons/table_add.png'), lbl, class_='icon')
    return h.link_to(img, h.url.current(**params), title=lbl, class_='tooltip')


class ChangesetController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(ChangesetController, self).__before__()
        c.affected_files_cut_off = 60
        repo_model = RepoModel()
        c.users_array = repo_model.get_users_js()
        c.users_groups_array = repo_model.get_users_groups_js()

    def index(self, revision):

        c.anchor_url = anchor_url
        c.ignorews_url = _ignorews_url
        c.context_url = _context_url
        limit_off = request.GET.get('fulldiff')
        #get ranges of revisions if preset
        rev_range = revision.split('...')[:2]
        enable_comments = True
        try:
            if len(rev_range) == 2:
                enable_comments = False
                rev_start = rev_range[0]
                rev_end = rev_range[1]
                rev_ranges = c.rhodecode_repo.get_changesets(start=rev_start,
                                                            end=rev_end)
            else:
                rev_ranges = [c.rhodecode_repo.get_changeset(revision)]

            c.cs_ranges = list(rev_ranges)
            if not c.cs_ranges:
                raise RepositoryError('Changeset range returned empty result')

        except (RepositoryError, ChangesetDoesNotExistError, Exception), e:
            log.error(traceback.format_exc())
            h.flash(str(e), category='warning')
            return redirect(url('home'))

        c.changes = OrderedDict()

        c.lines_added = 0  # count of lines added
        c.lines_deleted = 0  # count of lines removes

        cumulative_diff = 0
        c.cut_off = False  # defines if cut off limit is reached
        c.changeset_statuses = ChangesetStatus.STATUSES
        c.comments = []
        c.statuses = []
        c.inline_comments = []
        c.inline_cnt = 0
        # Iterate over ranges (default changeset view is always one changeset)
        for changeset in c.cs_ranges:

            c.statuses.extend([ChangesetStatusModel()\
                              .get_status(c.rhodecode_db_repo.repo_id,
                                          changeset.raw_id)])

            c.comments.extend(ChangesetCommentsModel()\
                              .get_comments(c.rhodecode_db_repo.repo_id,
                                            revision=changeset.raw_id))
            inlines = ChangesetCommentsModel()\
                        .get_inline_comments(c.rhodecode_db_repo.repo_id,
                                             revision=changeset.raw_id)
            c.inline_comments.extend(inlines)
            c.changes[changeset.raw_id] = []
            try:
                changeset_parent = changeset.parents[0]
            except IndexError:
                changeset_parent = None

            #==================================================================
            # ADDED FILES
            #==================================================================
            for node in changeset.added:
                fid = h.FID(revision, node.path)
                line_context_lcl = get_line_ctx(fid, request.GET)
                ign_whitespace_lcl = get_ignore_ws(fid, request.GET)
                lim = self.cut_off_limit
                if cumulative_diff > self.cut_off_limit:
                    lim = -1 if limit_off is None else None
                size, cs1, cs2, diff, st = wrapped_diff(
                    filenode_old=None,
                    filenode_new=node,
                    cut_off_limit=lim,
                    ignore_whitespace=ign_whitespace_lcl,
                    line_context=line_context_lcl,
                    enable_comments=enable_comments
                )
                cumulative_diff += size
                c.lines_added += st[0]
                c.lines_deleted += st[1]
                c.changes[changeset.raw_id].append(
                    ('added', node, diff, cs1, cs2, st)
                )

            #==================================================================
            # CHANGED FILES
            #==================================================================
            for node in changeset.changed:
                try:
                    filenode_old = changeset_parent.get_node(node.path)
                except ChangesetError:
                    log.warning('Unable to fetch parent node for diff')
                    filenode_old = FileNode(node.path, '', EmptyChangeset())

                fid = h.FID(revision, node.path)
                line_context_lcl = get_line_ctx(fid, request.GET)
                ign_whitespace_lcl = get_ignore_ws(fid, request.GET)
                lim = self.cut_off_limit
                if cumulative_diff > self.cut_off_limit:
                    lim = -1 if limit_off is None else None
                size, cs1, cs2, diff, st = wrapped_diff(
                    filenode_old=filenode_old,
                    filenode_new=node,
                    cut_off_limit=lim,
                    ignore_whitespace=ign_whitespace_lcl,
                    line_context=line_context_lcl,
                    enable_comments=enable_comments
                )
                cumulative_diff += size
                c.lines_added += st[0]
                c.lines_deleted += st[1]
                c.changes[changeset.raw_id].append(
                    ('changed', node, diff, cs1, cs2, st)
                )
            #==================================================================
            # REMOVED FILES
            #==================================================================
            for node in changeset.removed:
                c.changes[changeset.raw_id].append(
                    ('removed', node, None, None, None, (0, 0))
                )

        # count inline comments
        for __, lines in c.inline_comments:
            for comments in lines.values():
                c.inline_cnt += len(comments)

        if len(c.cs_ranges) == 1:
            c.changeset = c.cs_ranges[0]
            c.changes = c.changes[c.changeset.raw_id]

            return render('changeset/changeset.html')
        else:
            return render('changeset/changeset_range.html')

    def raw_changeset(self, revision):

        method = request.GET.get('diff', 'show')
        ignore_whitespace = request.GET.get('ignorews') == '1'
        line_context = request.GET.get('context', 3)
        try:
            c.scm_type = c.rhodecode_repo.alias
            c.changeset = c.rhodecode_repo.get_changeset(revision)
        except RepositoryError:
            log.error(traceback.format_exc())
            return redirect(url('home'))
        else:
            try:
                c.changeset_parent = c.changeset.parents[0]
            except IndexError:
                c.changeset_parent = None
            c.changes = []

            for node in c.changeset.added:
                filenode_old = FileNode(node.path, '')
                if filenode_old.is_binary or node.is_binary:
                    diff = _('binary file') + '\n'
                else:
                    f_gitdiff = diffs.get_gitdiff(filenode_old, node,
                                           ignore_whitespace=ignore_whitespace,
                                           context=line_context)
                    diff = diffs.DiffProcessor(f_gitdiff,
                                                format='gitdiff').raw_diff()

                cs1 = None
                cs2 = node.changeset.raw_id
                c.changes.append(('added', node, diff, cs1, cs2))

            for node in c.changeset.changed:
                filenode_old = c.changeset_parent.get_node(node.path)
                if filenode_old.is_binary or node.is_binary:
                    diff = _('binary file')
                else:
                    f_gitdiff = diffs.get_gitdiff(filenode_old, node,
                                           ignore_whitespace=ignore_whitespace,
                                           context=line_context)
                    diff = diffs.DiffProcessor(f_gitdiff,
                                                format='gitdiff').raw_diff()

                cs1 = filenode_old.changeset.raw_id
                cs2 = node.changeset.raw_id
                c.changes.append(('changed', node, diff, cs1, cs2))

        response.content_type = 'text/plain'

        if method == 'download':
            response.content_disposition = 'attachment; filename=%s.patch' \
                                            % revision

        c.parent_tmpl = ''.join(['# Parent  %s\n' % x.raw_id
                                 for x in c.changeset.parents])

        c.diffs = ''
        for x in c.changes:
            c.diffs += x[2]

        return render('changeset/raw_changeset.html')

    @jsonify
    def comment(self, repo_name, revision):
        status = request.POST.get('changeset_status')
        change_status = request.POST.get('change_changeset_status')

        comm = ChangesetCommentsModel().create(
            text=request.POST.get('text'),
            repo=c.rhodecode_db_repo.repo_id,
            user=c.rhodecode_user.user_id,
            revision=revision,
            f_path=request.POST.get('f_path'),
            line_no=request.POST.get('line'),
            status_change=(ChangesetStatus.get_status_lbl(status)
                           if status and change_status else None)
        )

        # get status if set !
        if status and change_status:
            # if latest status was from pull request and it's closed
            # disallow changing status ! 
            # dont_allow_on_closed_pull_request = True !

            try:
                ChangesetStatusModel().set_status(
                    c.rhodecode_db_repo.repo_id,
                    status,
                    c.rhodecode_user.user_id,
                    comm,
                    revision=revision,
                    dont_allow_on_closed_pull_request=True
                )
            except StatusChangeOnClosedPullRequestError:
                log.error(traceback.format_exc())
                msg = _('Changing status on a changeset associated with'
                        'a closed pull request is not allowed')
                h.flash(msg, category='warning')
                return redirect(h.url('changeset_home', repo_name=repo_name,
                                      revision=revision))
        action_logger(self.rhodecode_user,
                      'user_commented_revision:%s' % revision,
                      c.rhodecode_db_repo, self.ip_addr, self.sa)

        Session().commit()

        if not request.environ.get('HTTP_X_PARTIAL_XHR'):
            return redirect(h.url('changeset_home', repo_name=repo_name,
                                  revision=revision))

        data = {
           'target_id': h.safeid(h.safe_unicode(request.POST.get('f_path'))),
        }
        if comm:
            c.co = comm
            data.update(comm.get_dict())
            data.update({'rendered_text':
                         render('changeset/changeset_comment_block.html')})

        return data

    @jsonify
    def delete_comment(self, repo_name, comment_id):
        co = ChangesetComment.get(comment_id)
        owner = lambda: co.author.user_id == c.rhodecode_user.user_id
        if h.HasPermissionAny('hg.admin', 'repository.admin')() or owner:
            ChangesetCommentsModel().delete(comment=co)
            Session().commit()
            return True
        else:
            raise HTTPForbidden()

# -*- coding: utf-8 -*-
"""
    rhodecode.model.pull_reuquest
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pull request model for RhodeCode

    :created_on: Jun 6, 2012
    :author: marcink
    :copyright: (C) 2012-2012 Marcin Kuzminski <marcin@python-works.com>
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
import binascii
from pylons.i18n.translation import _

from rhodecode.lib import helpers as h
from rhodecode.model import BaseModel
from rhodecode.model.db import PullRequest, PullRequestReviewers, Notification,\
    ChangesetStatus
from rhodecode.model.notification import NotificationModel
from rhodecode.lib.utils2 import safe_unicode

from rhodecode.lib.vcs.utils.hgcompat import discovery
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.comment import ChangesetCommentsModel
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class PullRequestModel(BaseModel):

    cls = PullRequest

    def get_all(self, repo):
        repo = self._get_repo(repo)
        return PullRequest.query().filter(PullRequest.other_repo == repo).all()

    def create(self, created_by, org_repo, org_ref, other_repo,
               other_ref, revisions, reviewers, title, description=None):

        created_by_user = self._get_user(created_by)
        org_repo = self._get_repo(org_repo)
        other_repo = self._get_repo(other_repo)

        new = PullRequest()
        new.org_repo = org_repo
        new.org_ref = org_ref
        new.other_repo = other_repo
        new.other_ref = other_ref
        new.revisions = revisions
        new.title = title
        new.description = description
        new.author = created_by_user
        self.sa.add(new)
        Session().flush()
        #members
        for member in reviewers:
            _usr = self._get_user(member)
            reviewer = PullRequestReviewers(_usr, new)
            self.sa.add(reviewer)

        #notification to reviewers
        notif = NotificationModel()

        subject = safe_unicode(
            h.link_to(
              _('%(user)s wants you to review pull request #%(pr_id)s') % \
                {'user': created_by_user.username,
                 'pr_id': new.pull_request_id},
              h.url('pullrequest_show', repo_name=other_repo.repo_name,
                    pull_request_id=new.pull_request_id,
                    qualified=True,
              )
            )
        )
        body = description
        notif.create(created_by=created_by_user, subject=subject, body=body,
                     recipients=reviewers,
                     type_=Notification.TYPE_PULL_REQUEST,)

        return new

    def _get_changesets(self, org_repo, org_ref, other_repo, other_ref,
                        discovery_data):
        """
        Returns a list of changesets that are incoming from org_repo@org_ref
        to other_repo@other_ref

        :param org_repo:
        :type org_repo:
        :param org_ref:
        :type org_ref:
        :param other_repo:
        :type other_repo:
        :param other_ref:
        :type other_ref:
        :param tmp:
        :type tmp:
        """
        changesets = []
        #case two independent repos
        if org_repo != other_repo:
            common, incoming, rheads = discovery_data

            if not incoming:
                revs = []
            else:
                revs = org_repo._repo.changelog.findmissing(common, rheads)

            for cs in reversed(map(binascii.hexlify, revs)):
                changesets.append(org_repo.get_changeset(cs))
        else:
            revs = ['ancestors(%s) and not ancestors(%s)' % (org_ref[1],
                                                             other_ref[1])]
            from mercurial import scmutil
            out = scmutil.revrange(org_repo._repo, revs)
            for cs in reversed(out):
                changesets.append(org_repo.get_changeset(cs))

        return changesets

    def _get_discovery(self, org_repo, org_ref, other_repo, other_ref):
        """
        Get's mercurial discovery data used to calculate difference between
        repos and refs

        :param org_repo:
        :type org_repo:
        :param org_ref:
        :type org_ref:
        :param other_repo:
        :type other_repo:
        :param other_ref:
        :type other_ref:
        """

        other = org_repo._repo
        repo = other_repo._repo
        tip = other[org_ref[1]]
        log.debug('Doing discovery for %s@%s vs %s@%s' % (
                        org_repo, org_ref, other_repo, other_ref)
        )
        log.debug('Filter heads are %s[%s]' % (tip, org_ref[1]))
        tmp = discovery.findcommonincoming(
                  repo=repo,  # other_repo we check for incoming
                  remote=other,  # org_repo source for incoming
                  heads=[tip.node()],
                  force=False
        )
        return tmp

    def get_compare_data(self, org_repo, org_ref, other_repo, other_ref):
        """
        Returns a tuple of incomming changesets, and discoverydata cache

        :param org_repo:
        :type org_repo:
        :param org_ref:
        :type org_ref:
        :param other_repo:
        :type other_repo:
        :param other_ref:
        :type other_ref:
        """

        if len(org_ref) != 2 or not isinstance(org_ref, (list, tuple)):
            raise Exception('org_ref must be a two element list/tuple')

        if len(other_ref) != 2 or not isinstance(org_ref, (list, tuple)):
            raise Exception('other_ref must be a two element list/tuple')

        discovery_data = self._get_discovery(org_repo.scm_instance,
                                           org_ref,
                                           other_repo.scm_instance,
                                           other_ref)
        cs_ranges = self._get_changesets(org_repo.scm_instance,
                                           org_ref,
                                           other_repo.scm_instance,
                                           other_ref,
                                           discovery_data)
        return cs_ranges, discovery_data

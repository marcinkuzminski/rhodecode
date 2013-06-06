# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.admin
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Controller for Admin panel of Rhodecode

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

from pylons import request, tmpl_context as c, url
from sqlalchemy.orm import joinedload
from whoosh.qparser.default import QueryParser
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh import query
from sqlalchemy.sql.expression import or_, and_, func

from rhodecode.model.db import UserLog, User
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils2 import safe_int, remove_prefix, remove_suffix
from rhodecode.lib.indexers import JOURNAL_SCHEMA
from rhodecode.lib.helpers import Page


log = logging.getLogger(__name__)


def _journal_filter(user_log, search_term):
    """
    Filters sqlalchemy user_log based on search_term with whoosh Query language
    http://packages.python.org/Whoosh/querylang.html

    :param user_log:
    :param search_term:
    """
    log.debug('Initial search term: %r' % search_term)
    qry = None
    if search_term:
        qp = QueryParser('repository', schema=JOURNAL_SCHEMA)
        qp.add_plugin(DateParserPlugin())
        qry = qp.parse(unicode(search_term))
        log.debug('Filtering using parsed query %r' % qry)

    def wildcard_handler(col, wc_term):
        if wc_term.startswith('*') and not wc_term.endswith('*'):
            #postfix == endswith
            wc_term = remove_prefix(wc_term, prefix='*')
            return func.lower(col).endswith(wc_term)
        elif wc_term.startswith('*') and wc_term.endswith('*'):
            #wildcard == ilike
            wc_term = remove_prefix(wc_term, prefix='*')
            wc_term = remove_suffix(wc_term, suffix='*')
            return func.lower(col).contains(wc_term)

    def get_filterion(field, val, term):

        if field == 'repository':
            field = getattr(UserLog, 'repository_name')
        elif field == 'ip':
            field = getattr(UserLog, 'user_ip')
        elif field == 'date':
            field = getattr(UserLog, 'action_date')
        elif field == 'username':
            field = getattr(UserLog, 'username')
        else:
            field = getattr(UserLog, field)
        log.debug('filter field: %s val=>%s' % (field, val))

        #sql filtering
        if isinstance(term, query.Wildcard):
            return wildcard_handler(field, val)
        elif isinstance(term, query.Prefix):
            return func.lower(field).startswith(func.lower(val))
        elif isinstance(term, query.DateRange):
            return and_(field >= val[0], field <= val[1])
        return func.lower(field) == func.lower(val)

    if isinstance(qry, (query.And, query.Term, query.Prefix, query.Wildcard,
                        query.DateRange)):
        if not isinstance(qry, query.And):
            qry = [qry]
        for term in qry:
            field = term.fieldname
            val = (term.text if not isinstance(term, query.DateRange)
                   else [term.startdate, term.enddate])
            user_log = user_log.filter(get_filterion(field, val, term))
    elif isinstance(qry, query.Or):
        filters = []
        for term in qry:
            field = term.fieldname
            val = (term.text if not isinstance(term, query.DateRange)
                   else [term.startdate, term.enddate])
            filters.append(get_filterion(field, val, term))
        user_log = user_log.filter(or_(*filters))

    return user_log


class AdminController(BaseController):

    @LoginRequired()
    def __before__(self):
        super(AdminController, self).__before__()

    @HasPermissionAllDecorator('hg.admin')
    def index(self):
        users_log = UserLog.query()\
                .options(joinedload(UserLog.user))\
                .options(joinedload(UserLog.repository))

        #FILTERING
        c.search_term = request.GET.get('filter')
        try:
            users_log = _journal_filter(users_log, c.search_term)
        except Exception:
            # we want this to crash for now
            raise

        users_log = users_log.order_by(UserLog.action_date.desc())

        p = safe_int(request.GET.get('page', 1), 1)

        def url_generator(**kw):
            return url.current(filter=c.search_term, **kw)

        c.users_log = Page(users_log, page=p, items_per_page=10, url=url_generator)
        c.log_data = render('admin/admin_log.html')

        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            return c.log_data
        return render('admin/admin.html')

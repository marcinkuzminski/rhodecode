import logging
import os

from pylons import request, response, session, tmpl_context as c, url, app_globals as g
from pylons.controllers.util import abort, redirect
from pylons_app.lib.base import BaseController, render
from pylons_app.model import meta
from pylons_app.model.db import UserLog
from webhelpers.paginate import Page
from pylons_app.lib.auth import LoginRequired

log = logging.getLogger(__name__)

class AdminController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        user = session['hg_app_user']
        c.admin_user = user.is_admin
        c.admin_username = user.username
        super(AdminController, self).__before__()
        
    def index(self):
        sa = meta.Session
                         
        users_log = sa.query(UserLog).order_by(UserLog.action_date.desc())
        p = int(request.params.get('page', 1))
        c.users_log = Page(users_log, page=p, items_per_page=10)
        c.log_data = render('admin/admin_log.html')
        if request.params.get('partial'):
            return c.log_data
        return render('admin/admin.html')    
                

from pylons_app.model.meta import Base
from sqlalchemy import *
from sqlalchemy.orm import relation, backref
from sqlalchemy.orm.session import Session
from vcs.utils.lazy import LazyProperty
import logging

log = logging.getLogger(__name__)

class HgAppSettings(Base):
    __tablename__ = 'hg_app_settings'
    __table_args__ = (UniqueConstraint('app_settings_name'), {'useexisting':True})
    app_settings_id = Column("app_settings_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=True)
    app_settings_name = Column("app_settings_name", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    app_settings_value = Column("app_settings_value", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

class HgAppUi(Base):
    __tablename__ = 'hg_app_ui'
    __table_args__ = {'useexisting':True}
    ui_id = Column("ui_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=True)
    ui_section = Column("ui_section", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_key = Column("ui_key", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_value = Column("ui_value", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_active = Column("ui_active", BOOLEAN(), nullable=True, unique=None, default=True)
    
    
class User(Base): 
    __tablename__ = 'users'
    __table_args__ = {'useexisting':True}
    user_id = Column("user_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=True)
    username = Column("username", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    password = Column("password", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    active = Column("active", BOOLEAN(), nullable=True, unique=None, default=None)
    admin = Column("admin", BOOLEAN(), nullable=True, unique=None, default=False)
    name = Column("name", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    lastname = Column("lastname", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    email = Column("email", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    last_login = Column("last_login", DATETIME(timezone=False), nullable=True, unique=None, default=None)
    
    user_log = relation('UserLog')
    user_perms = relation('UserToPerm', primaryjoin="User.user_id==UserToPerm.user_id")
    
    @LazyProperty
    def full_contact(self):
        return '%s %s <%s>' % (self.name, self.lastname, self.email)
        
    def __repr__(self):
        return "<User('id:%s:%s')>" % (self.user_id, self.username)
    
    def update_lastlogin(self):
        """Update user lastlogin"""
        import datetime
        
        try:
            session = Session.object_session(self)
            self.last_login = datetime.datetime.now()
            session.add(self)
            session.commit()
            log.debug('updated user %s lastlogin',self)
        except Exception:
            session.rollback()        
    
      
class UserLog(Base): 
    __tablename__ = 'user_logs'
    __table_args__ = {'useexisting':True}
    user_log_id = Column("user_log_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", INTEGER(), ForeignKey(u'users.user_id'), nullable=False, unique=None, default=None)
    user_ip = Column("user_ip", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None) 
    repository = Column("repository", TEXT(length=None, convert_unicode=False, assert_unicode=None), ForeignKey(u'repositories.repo_name'), nullable=False, unique=None, default=None)
    action = Column("action", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DATETIME(timezone=False), nullable=True, unique=None, default=None)
    
    user = relation('User')
    
class Repository(Base):
    __tablename__ = 'repositories'
    __table_args__ = (UniqueConstraint('repo_name'), {'useexisting':True},)
    repo_id = Column("repo_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=True)
    repo_name = Column("repo_name", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    user_id = Column("user_id", INTEGER(), ForeignKey(u'users.user_id'), nullable=False, unique=False, default=None)
    private = Column("private", BOOLEAN(), nullable=True, unique=None, default=None)
    description = Column("description", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    
    user = relation('User')
    repo_to_perm = relation('RepoToPerm', cascade='all')
    
    def __repr__(self):
        return "<Repository('id:%s:%s')>" % (self.repo_id, self.repo_name)
        
class Permission(Base):
    __tablename__ = 'permissions'
    __table_args__ = {'useexisting':True}
    permission_id = Column("permission_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=True)
    permission_name = Column("permission_name", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    permission_longname = Column("permission_longname", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    
    def __repr__(self):
        return "<Permission('%s:%s')>" % (self.permission_id, self.permission_name)

class RepoToPerm(Base):
    __tablename__ = 'repo_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'repository_id'), {'useexisting':True})
    repo_to_perm_id = Column("repo_to_perm_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", INTEGER(), ForeignKey(u'users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", INTEGER(), ForeignKey(u'permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", INTEGER(), ForeignKey(u'repositories.repo_id'), nullable=False, unique=None, default=None) 
    
    user = relation('User')
    permission = relation('Permission')
    repository = relation('Repository')

class UserToPerm(Base):
    __tablename__ = 'user_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'permission_id'), {'useexisting':True})
    user_to_perm_id = Column("user_to_perm_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", INTEGER(), ForeignKey(u'users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", INTEGER(), ForeignKey(u'permissions.permission_id'), nullable=False, unique=None, default=None)
    
    user = relation('User')
    permission = relation('Permission')





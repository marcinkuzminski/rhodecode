from pylons_app.model.meta import Base
from sqlalchemy.orm import relation, backref
from sqlalchemy import *
from vcs.utils.lazy import LazyProperty

class User(Base): 
    __tablename__ = 'users'
    __table_args__ = {'useexisting':True}
    user_id = Column("user_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=True)
    username = Column("username", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    password = Column("password", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    active = Column("active", BOOLEAN(), nullable=True, unique=None, default=None)
    admin = Column("admin", BOOLEAN(), nullable=True, unique=None, default=None)
    name = Column("name", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    lastname = Column("lastname", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    email = Column("email", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    last_login = Column("last_login", DATETIME(timezone=False), nullable=True, unique=None, default=None)
    
    user_log = relation('UserLog')
    
    @LazyProperty
    def full_contact(self):
        return '%s %s <%s>' % (self.name, self.lastname, self.email)
        
    def __repr__(self):
        return "<User('%s:%s')>" % (self.user_id, self.username)
      
class UserLog(Base): 
    __tablename__ = 'user_logs'
    __table_args__ = {'useexisting':True}
    user_log_id = Column("user_log_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=1)
    user_id = Column("user_id", INTEGER(), ForeignKey(u'users.user_id'), nullable=False, unique=None, default=None)
    repository = Column("repository", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action = Column("action", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DATETIME(timezone=False), nullable=True, unique=None, default=None)
    
    user = relation('User')

class Repository(Base):
    __tablename__ = 'repositories'
    repo_name = Column("repo_name", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", INTEGER(), ForeignKey(u'users.user_id'), nullable=False, unique=False, default=None)
    private = Column("private", BOOLEAN(), nullable=True, unique=None, default=None)
    description = Column("description", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    user = relation('User')
    
class Permission(Base):
    __tablename__ = 'permissions'
    __table_args__ = {'useexisting':True}
    permission_id = Column("id", INTEGER(), nullable=False, unique=True, default=None, primary_key=1)
    permission_name = Column("permission_name", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    permission_longname = Column("permission_longname", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    
    def __repr__(self):
        return "<Permission('%s:%s')>" % (self.permission_id, self.permission_name)

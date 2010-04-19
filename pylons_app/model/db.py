import sqlalchemy
from pylons_app.model.meta import Base
from sqlalchemy import ForeignKey, Column
from sqlalchemy.orm import relation, backref

if sqlalchemy.__version__ == '0.6.0':
    from sqlalchemy.dialects.sqlite import *
else:
    from sqlalchemy.databases.sqlite import SLBoolean as BOOLEAN, \
    SLInteger as INTEGER, SLText as TEXT, SLDateTime as DATETIME

class Users(Base): 
    __tablename__ = 'users'
    __table_args__ = {'useexisting':True}
    user_id = Column("user_id", INTEGER(), nullable=False, unique=True, default=None, primary_key=1)
    username = Column("username", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    password = Column("password", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    active = Column("active", BOOLEAN(), nullable=True, unique=None, default=None)
    admin = Column("admin", BOOLEAN(), nullable=True, unique=None, default=None)
    action_log = relation('UserLogs')
      
class UserLogs(Base): 
    __tablename__ = 'user_logs'
    __table_args__ = {'useexisting':True}
    id = Column("id", INTEGER(), nullable=False, unique=True, default=None, primary_key=1)
    user_id = Column("user_id", INTEGER(), ForeignKey(u'users.user_id'), nullable=True, unique=None, default=None)
    repository = Column("repository", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action = Column("action", TEXT(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DATETIME(timezone=False), nullable=True, unique=None, default=None)
    user = relation('Users')

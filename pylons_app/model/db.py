from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref
from sqlalchemy import ForeignKey, Column, Table, Sequence
from sqlalchemy.types import *
from sqlalchemy.databases.sqlite import *
from pylons_app.model.meta import Base


class Users(Base): 
    __tablename__ = 'users'
    __table_args__ = {'useexisting':True}
    user_id = Column("user_id", SLInteger(), nullable=False, unique=True, default=None, primary_key=1)
    username = Column("username", SLText(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    password = Column("password", SLText(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    active = Column("active", SLBoolean(), nullable=True, unique=None, default=None)
    admin = Column("admin", SLBoolean(), nullable=True, unique=None, default=None)
    action_log = relation('UserLogs')
      
class UserLogs(Base): 
    __tablename__ = 'user_logs'
    __table_args__ = {'useexisting':True}
    id = Column("id", SLInteger(), nullable=False, unique=True, default=None, primary_key=1)
    user_id = Column("user_id", SLInteger(), ForeignKey(u'users.user_id'), nullable=True, unique=None, default=None)
    repository = Column("repository", SLText(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action = Column("action", SLText(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", SLDateTime(timezone=False), nullable=True, unique=None, default=None)
    user = relation('Users')

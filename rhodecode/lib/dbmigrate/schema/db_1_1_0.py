from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relation, backref, class_mapper
from sqlalchemy.orm.session import Session
from rhodecode.model.meta import Base

class BaseModel(object):
    """Base Model for all classess

    """

    @classmethod
    def _get_keys(cls):
        """return column names for this model """
        return class_mapper(cls).c.keys()

    def get_dict(self):
        """return dict with keys and values corresponding
        to this model data """

        d = {}
        for k in self._get_keys():
            d[k] = getattr(self, k)
        return d

    def get_appstruct(self):
        """return list with keys and values tupples corresponding
        to this model data """

        l = []
        for k in self._get_keys():
            l.append((k, getattr(self, k),))
        return l

    def populate_obj(self, populate_dict):
        """populate model with data from given populate_dict"""

        for k in self._get_keys():
            if k in populate_dict:
                setattr(self, k, populate_dict[k])

    @classmethod
    def query(cls):
        return Session.query(cls)

    @classmethod
    def get(cls, id_):
        if id_:
            return cls.query().get(id_)

    @classmethod
    def getAll(cls):
        return cls.query().all()

    @classmethod
    def delete(cls, id_):
        obj = cls.query().get(id_)
        Session.delete(obj)
        Session.commit()


class UserFollowing(Base, BaseModel):
    __tablename__ = 'user_followings'
    __table_args__ = (UniqueConstraint('user_id', 'follows_repository_id'),
                      UniqueConstraint('user_id', 'follows_user_id')
                      , {'useexisting':True})

    user_following_id = Column("user_following_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey(u'users.user_id'), nullable=False, unique=None, default=None)
    follows_repo_id = Column("follows_repository_id", Integer(), ForeignKey(u'repositories.repo_id'), nullable=True, unique=None, default=None)
    follows_user_id = Column("follows_user_id", Integer(), ForeignKey(u'users.user_id'), nullable=True, unique=None, default=None)

    user = relation('User', primaryjoin='User.user_id==UserFollowing.user_id')

    follows_user = relation('User', primaryjoin='User.user_id==UserFollowing.follows_user_id')
    follows_repository = relation('Repository')


class CacheInvalidation(Base, BaseModel):
    __tablename__ = 'cache_invalidation'
    __table_args__ = (UniqueConstraint('cache_key'), {'useexisting':True})
    cache_id = Column("cache_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    cache_key = Column("cache_key", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    cache_args = Column("cache_args", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    cache_active = Column("cache_active", Boolean(), nullable=True, unique=None, default=False)


    def __init__(self, cache_key, cache_args=''):
        self.cache_key = cache_key
        self.cache_args = cache_args
        self.cache_active = False

    def __repr__(self):
        return "<CacheInvalidation('%s:%s')>" % (self.cache_id, self.cache_key)

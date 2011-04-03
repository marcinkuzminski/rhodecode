"""SQLAlchemy Metadata and Session object"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, class_mapper
from beaker import cache

from rhodecode.model import caching_query


# Beaker CacheManager.  A home base for cache configurations.
cache_manager = cache.CacheManager()

__all__ = ['Base', 'Session']
#
# SQLAlchemy session manager. Updated by model.init_model()
#
Session = scoped_session(
                sessionmaker(
                    query_cls=caching_query.query_callable(cache_manager)
                )
          )

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
        return Session.query(cls).get(id_)


# The declarative Base
Base = declarative_base(cls=BaseModel)

#to use cache use this in query
#.options(FromCache("sqlalchemy_cache_type", "cachekey"))

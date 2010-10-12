"""SQLAlchemy Metadata and Session object"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from rhodecode.model import caching_query
from beaker import cache

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

# The declarative Base
Base = declarative_base()
#For another db...
#Base2 = declarative_base()

#to use cache use this in query
#.options(FromCache("sqlalchemy_cache_type", "cachekey"))

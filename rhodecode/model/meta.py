"""SQLAlchemy Metadata and Session object"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from rhodecode.model import caching_query
from beaker import cache
import os
from os.path import join as jn, dirname as dn, abspath
import time

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

#===============================================================================
# CACHE OPTIONS
#===============================================================================
cache_dir = jn(dn(dn(dn(abspath(__file__)))), 'data', 'cache')
if not os.path.isdir(cache_dir):
    os.mkdir(cache_dir)
# set start_time to current time
# to re-cache everything
# upon application startup
start_time = time.time()
# configure the "sqlalchemy" cache region.
cache_manager.regions['sql_cache_short'] = {
        'type':'memory',
        'data_dir':cache_dir,
        'expire':10,
        'start_time':start_time
    }
cache_manager.regions['sql_cache_med'] = {
        'type':'memory',
        'data_dir':cache_dir,
        'expire':360,
        'start_time':start_time
    }
cache_manager.regions['sql_cache_long'] = {
        'type':'file',
        'data_dir':cache_dir,
        'expire':3600,
        'start_time':start_time
    }
#to use cache use this in query
#.options(FromCache("sqlalchemy_cache_type", "cachekey"))

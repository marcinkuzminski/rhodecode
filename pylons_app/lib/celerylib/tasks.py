from celery.decorators import task
from datetime import datetime, timedelta
from pylons_app.lib.helpers import person
from pylons_app.lib.utils import OrderedDict
from time import mktime
import calendar
import logging
from vcs.backends.hg import MercurialRepository

log = logging.getLogger(__name__)

@task()
def whoosh_index(repo_location,full_index):
    from pylons_app.lib.indexers import DaemonLock
    from pylons_app.lib.indexers.daemon import WhooshIndexingDaemon,LockHeld
    try:
        l = DaemonLock()
        WhooshIndexingDaemon(repo_location=repo_location)\
            .run(full_index=full_index)
        l.release()
        return 'Done'
    except LockHeld:
        log.info('LockHeld')
        return 'LockHeld'    

@task()
def get_commits_stats(repo):
    aggregate = OrderedDict()
    repo = MercurialRepository('/home/marcink/hg_repos/'+repo)
    #graph range
    td = datetime.today() + timedelta(days=1) 
    y, m, d = td.year, td.month, td.day
    ts_min = mktime((y, (td - timedelta(days=calendar.mdays[m])).month,
                        d, 0, 0, 0, 0, 0, 0,))
    ts_max = mktime((y, m, d, 0, 0, 0, 0, 0, 0,))
    
    def author_key_cleaner(k):
        k = person(k)
        k = k.replace('"', "'") #for js data compatibilty
        return k
            
    for cs in repo[:200]:#added limit 200 until fix #29 is made
        k = '%s-%s-%s' % (cs.date.timetuple()[0], cs.date.timetuple()[1],
                          cs.date.timetuple()[2])
        timetupple = [int(x) for x in k.split('-')]
        timetupple.extend([0 for _ in xrange(6)])
        k = mktime(timetupple)
        if aggregate.has_key(author_key_cleaner(cs.author)):
            if aggregate[author_key_cleaner(cs.author)].has_key(k):
                aggregate[author_key_cleaner(cs.author)][k]["commits"] += 1
                aggregate[author_key_cleaner(cs.author)][k]["added"] += len(cs.added)
                aggregate[author_key_cleaner(cs.author)][k]["changed"] += len(cs.changed)
                aggregate[author_key_cleaner(cs.author)][k]["removed"] += len(cs.removed)
                
            else:
                #aggregate[author_key_cleaner(cs.author)].update(dates_range)
                if k >= ts_min and k <= ts_max:
                    aggregate[author_key_cleaner(cs.author)][k] = {}
                    aggregate[author_key_cleaner(cs.author)][k]["commits"] = 1
                    aggregate[author_key_cleaner(cs.author)][k]["added"] = len(cs.added)
                    aggregate[author_key_cleaner(cs.author)][k]["changed"] = len(cs.changed)
                    aggregate[author_key_cleaner(cs.author)][k]["removed"] = len(cs.removed) 
                                        
        else:
            if k >= ts_min and k <= ts_max:
                aggregate[author_key_cleaner(cs.author)] = OrderedDict()
                #aggregate[author_key_cleaner(cs.author)].update(dates_range)
                aggregate[author_key_cleaner(cs.author)][k] = {}
                aggregate[author_key_cleaner(cs.author)][k]["commits"] = 1
                aggregate[author_key_cleaner(cs.author)][k]["added"] = len(cs.added)
                aggregate[author_key_cleaner(cs.author)][k]["changed"] = len(cs.changed)
                aggregate[author_key_cleaner(cs.author)][k]["removed"] = len(cs.removed)                 
    
    d = ''
    tmpl0 = u""""%s":%s"""
    tmpl1 = u"""{label:"%s",data:%s,schema:["commits"]},"""
    for author in aggregate:
        
        d += tmpl0 % (author,
                      tmpl1 \
                      % (author,
                    [{"time":x,
                      "commits":aggregate[author][x]['commits'],
                      "added":aggregate[author][x]['added'],
                      "changed":aggregate[author][x]['changed'],
                      "removed":aggregate[author][x]['removed'],
                      } for x in aggregate[author]]))
    if d == '':
        d = '"%s":{label:"%s",data:[[0,1],]}' \
            % (author_key_cleaner(repo.contact),
               author_key_cleaner(repo.contact))
    return (ts_min, ts_max, d)    

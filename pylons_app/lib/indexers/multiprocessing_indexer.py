from multiprocessing import Process, Queue, cpu_count, Lock
import socket, sys
import time
import os
import sys
from os.path import dirname as dn
from multiprocessing.dummy import current_process
from shutil import rmtree

sys.path.append(dn(dn(dn(os.path.realpath(__file__)))))

from pylons_app.model.hg_model import HgModel
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter
from whoosh.fields import TEXT, ID, STORED, Schema
from whoosh.index import create_in, open_dir
from datetime import datetime
from multiprocessing.process import current_process
from multiprocessing import Array, Value

root = dn(dn(os.path.dirname(os.path.abspath(__file__))))
idx_location = os.path.join(root, 'data', 'index')
root_path = '/home/marcink/python_workspace_dirty/*'

exclude_extensions = ['pyc', 'mo', 'png', 'jpg', 'jpeg', 'gif', 'swf',
                       'dll', 'ttf', 'psd', 'svg', 'pdf', 'bmp', 'dll']

my_analyzer = RegexTokenizer() | LowercaseFilter()
def scan_paths(root_location):
    return HgModel.repo_scan('/', root_location, None, True)

def index_paths(root_dir):
    index_paths_ = set()
    for path, dirs, files in os.walk(root_dir):
        if path.find('.hg') == -1:
        #if path.find('.hg') == -1 and path.find('bel-epa') != -1:    
            for f in files:
                index_paths_.add(os.path.join(path, f))

    return index_paths_
                    
def get_schema():
    return Schema(owner=TEXT(),
                repository=TEXT(stored=True),
                path=ID(stored=True, unique=True),
                content=TEXT(stored=True, analyzer=my_analyzer),
                modtime=STORED())

def add_doc(writer, path, repo_name, contact):
    """
    Adding doc to writer
    @param writer:
    @param path:
    @param repo:
    @param fname:
    """
    
    #we don't won't to read excluded file extensions just index them
    if path.split('/')[-1].split('.')[-1].lower() not in exclude_extensions:
        fobj = open(path, 'rb')
        content = fobj.read()
        fobj.close()
        try:
            u_content = unicode(content)
        except UnicodeDecodeError:
            #incase we have a decode error just represent as byte string
            u_content = unicode(str(content).encode('string_escape'))
    else:
        u_content = u''    
    writer.add_document(repository=u"%s" % repo_name,
                        owner=unicode(contact),
                        path=u"%s" % path,
                        content=u_content,
                        modtime=os.path.getmtime(path)) 


class MultiProcessIndexer(object):
    """ multiprocessing whoosh indexer """

    def __init__(self, idx, work_set=set(), nr_processes=cpu_count()):
        q = Queue()
        l = Lock()
        work_set = work_set
        writer = None
        #writer = idx.writer()
        
        for q_task in work_set:
            q.put(q_task)

        q.put('COMMIT')
        
        #to stop all processes we have to put STOP to queue and 
        #break the loop for each process
        for _ in xrange(nr_processes):
            q.put('STOP')

        
        for _ in xrange(nr_processes):
            p = Process(target=self.work_func, args=(q, l, idx, writer))
            p.start()
        
        

    def work_func(self, q, l, idx, writer):
        """ worker class invoked by process """
        

        writer = idx.writer()

        while True:
            q_task = q.get()
            proc = current_process()
            
#            if q_task == 'COMMIT':
#                l.acquire()
#                sys.stdout.write('%s commiting and STOP\n' % proc._name)
#                writer.commit(merge=False)
#                l.release()               
#                break
#            l.acquire()
#            writer = idx.writer()
#            l.release() 
                        
            if q_task == 'STOP':
                sys.stdout.write('%s STOP\n' % proc._name)  
                break
            
            if q_task != 'COMMIT':
                l.acquire()
                
                sys.stdout.write('    >> %s %s %s @ ' % q_task)
                sys.stdout.write(' %s \n' % proc._name)
                
                l.release()
                add_doc(writer, q_task[0], q_task[1], q_task[2])
                
            l.acquire()
            writer.commit(merge=True)
            l.release()
            

if __name__ == "__main__":
    #build queue
    do = True if len(sys.argv) > 1 else False
    q_tasks = []
    
    if os.path.exists(idx_location):
        rmtree(idx_location)
        
    if not os.path.exists(idx_location):
        os.mkdir(idx_location)
                    
    idx = create_in(idx_location, get_schema() , indexname='HG_INDEX')    
    
    
    if do:
        sys.stdout.write('Building queue...')
        for cnt, repo in enumerate(scan_paths(root_path).values()):
            if repo.name != 'evoice_py':
                continue            
            q_tasks.extend([(idx_path, repo.name, repo.contact) for idx_path in index_paths(repo.path)])
            if cnt == 4:
                break
            
        sys.stdout.write('done\n')
        
        mpi = MultiProcessIndexer(idx, q_tasks)

    
    else:
        print 'checking index'
        reader = idx.reader()
        all = reader.all_stored_fields()
        #print all
        for fields in all:
            print fields['path']
    

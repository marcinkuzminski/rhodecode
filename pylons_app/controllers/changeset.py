from pylons import tmpl_context as c
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.model.hg_model import HgModel
from vcs.utils import diffs as differ
import logging
from vcs.nodes import FileNode


log = logging.getLogger(__name__)

class ChangesetController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        super(ChangesetController, self).__before__()
        
    def index(self, revision):
        hg_model = HgModel()
        c.changeset = hg_model.get_repo(c.repo_name).get_changeset(revision)
        c.changeset_old = c.changeset.parents[0]
        c.changes = []
        
                
        for node in c.changeset.added:
            filenode_old = FileNode(node.path, '')
            f_udiff = differ.get_udiff(filenode_old, node)
            diff = differ.DiffProcessor(f_udiff).as_html()
            c.changes.append(('added', node, diff))
            
        for node in c.changeset.changed:
            filenode_old = c.changeset_old.get_node(node.path)
            f_udiff = differ.get_udiff(filenode_old, node)
            diff = differ.DiffProcessor(f_udiff).as_html()
            c.changes.append(('changed', node, diff))
            
        for node in c.changeset.removed:
            c.changes.append(('removed', node, None))            
            
        return render('changeset/changeset.html')

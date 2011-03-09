.. _general:

General RhodeCode usage
=======================


Repository deleting
-------------------

Currently when admin/owner deletes a repository, RhodeCode does not physically
delete a repository from filesystem, it renames it in a special way so it's
not possible to push,clone or access repository. It's worth a notice that,
even if someone will be given administrative access to RhodeCode and will 
delete a repository You can easy restore such action by restoring `rm__<date>`
from the repository name, and internal repository storage (.hg/.git)

Follow current branch in file view
----------------------------------

In file view when this checkbox is checked the << and >> arrows will jump
to changesets within the same branch currently viewing. So for example
if someone is viewing files at 'beta' branch and marks `follow current branch`
checkbox the << and >> buttons will only show him revisions for 'beta' branch


Compare view from changelog
---------------------------

Checkboxes in compare view allow users to view combined compare view. You can
only show the range between the first and last checkbox (no cherry pick).
Clicking more than one checkbox will activate a link in top saying
`Show selected changes <from-rev> -> <to-rev>` clicking this will bring
compare view

Compare view is also available from the journal on pushes having more than
one changeset



Mailing
-------

When administrator will fill up the mailing settings in .ini files
RhodeCode will send mails on user registration, or when RhodeCode errors occur
on errors the mails will have a detailed traceback of error.


Trending source files
---------------------

Trending source files are calculated based on pre defined dict of known
types and extensions. If You miss some extension or Would like to scan some
custom files it's possible to add new types in `LANGUAGES_EXTENSIONS_MAP` dict
located in `/rhodecode/lib/celerylib/tasks.py`
.. _general:

=======================
General RhodeCode usage
=======================


Repository deleting
-------------------

Currently when admin/owner deletes a repository, RhodeCode does not physically
delete a repository from filesystem, it renames it in a special way so it's
not possible to push,clone or access repository. It's worth a notice that,
even if someone will be given administrative access to RhodeCode and will
delete a repository You can easy restore such action by restoring `rm__<date>`
from the repository name, and internal repository storage (.hg/.git). There
is also a special command for cleaning such archived repos::

    paster cleanup-repos --older-than=30d production.ini

This command will scan for archived repositories that are older than 30d,
display them and ask if you want to delete them (there's a --dont-ask flag also)
If you host big amount of repositories with forks that are constantly deleted
it's recommended that you run such command via crontab.

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
`Show selected changesets <from-rev> -> <to-rev>` clicking this will bring
compare view. In this view also it's possible to switch to combined compare.

Compare view is also available from the journal on pushes having more than
one changeset


Non changeable repository urls
------------------------------

Due to complicated nature of repository grouping, often urls of repositories
can change.

example::

  #before
  http://server.com/repo_name
  # after insertion to test_group group the url will be
  http://server.com/test_group/repo_name

This can be an issue for build systems and any other hardcoded scripts, moving
repository to a group leads to a need for changing external systems. To
overcome this RhodeCode introduces a non changable replacement url. It's
simply an repository ID prefixed with `_` above urls are also accessible as::

  http://server.com/_<ID>

Since ID are always the same moving the repository will not affect such url.
the _<ID> syntax can be used anywhere in the system so urls with repo_name
for changelogs, files and other can be exchanged with _<ID> syntax.


Mailing
-------

When administrator will fill up the mailing settings in .ini files
RhodeCode will send mails on user registration, or when RhodeCode errors occur
on errors the mails will have a detailed traceback of error.


Mails are also sent for code comments. If someone comments on a changeset
mail is sent to all participants, the person who commited the changeset
(if present in RhodeCode), and to all people mentioned with @mention system.


Trending source files
---------------------

Trending source files are calculated based on pre defined dict of known
types and extensions. If You miss some extension or Would like to scan some
custom files it's possible to add new types in `LANGUAGES_EXTENSIONS_MAP` dict
located in `/rhodecode/lib/celerylib/tasks.py`


Cloning remote repositories
---------------------------

RhodeCode has an ability to clone remote repos from given remote locations.
Currently it support following options:

- hg  -> hg clone
- svn -> hg clone
- git -> git clone


.. note::

    - *`svn -> hg` cloning requires `hgsubversion` library to be installed.*

If you need to clone repositories that are protected via basic auth, you
might pass the url with stored credentials inside eg.
`http://user:passw@remote.server/repo`, RhodeCode will try to login and clone
using given credentials. Please take a note that they will be stored as
plaintext inside the database. RhodeCode will remove auth info when showing the
clone url in summary page.



Visual settings in admin pannel
-------------------------------


Visualisation settings in RhodeCode settings view are extra customizations
of server behavior. There are 3 main section in the settings.

General
~~~~~~~
    
`Use repository extra fields` option allows to set a custom fields for each
repository in the system. Each new field consists of 3 attributes `field key`,
`field label`, `field description`. Example usage of such fields would be to
define company specific information into repositories eg. defining repo_manager
key that would add give info about a manager of each repository. There's no
limit for adding custom fields. Newly created fields are accessible via API.


Icons
~~~~~

Show public repo icon / Show private repo icon on repositories - defines if
public/private icons should be shown in the UI.


Meta-Tagging
~~~~~~~~~~~~

With this option enabled, special metatags that are recognisible by RhodeCode
will be turned into colored tags. Currently available tags are::

    [featured]
    [stale]
    [dead]
    [lang => lang]
    [license => License]
    [requires => Repo]
    [recommends => Repo]
    [see => URI]



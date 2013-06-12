.. _changelog:

=========
Changelog
=========

1.7.1 (**2013-06-13**)
----------------------

news
++++

- Apply to children flag on repository group also adds users to private
  repositories, this is now consistent with user groups. Private repos default
  permissions are not affected by apply to children flag.
- Removed unionrepo code as it's part of Mercurial 2.6
- RhodeCode accepts now read only paths for serving repositories.

fixes
+++++

- Fixed issues with how mysql handles float values. Caused gists with
  expiration dates not work properly on mysql.
- Fixed issue with ldap enable/disable flag

1.7.0 (**2013-06-08**)
----------------------

news
++++

- Manage User’s Groups(teams): create, delete, rename, add/remove users inside.
  by delegated user group admins.
- Implemented simple Gist functionality.
- External authentication got special flag to controll user activation.
- Created whitelist for API access. Each view can now be accessed by api_key
  if added to whitelist.
- Added dedicated file history page.
- Added compare option into bookmarks
- Improved diff display for binary files and renames.
- Archive downloading are now stored in main action journal.
- Switch gravatar to always use ssl.
- Implements #842 RhodeCode version disclosure.
- Allow underscore to be the optionally first character of username.

fixes
+++++

- #818: Bookmarks Do Not Display on Changeset View.
- Fixed default permissions population during upgrades.
- Fixed overwrite default user group permission flag.
- Fixed issue with h.person() function returned prematurly giving only email
  info from changeset metadata.
- get_changeset uses now mercurial revrange to filter out branches.
  Switch to branch it's around 20% faster this way.
- Fixed some issues with paginators on chrome.
- Forbid changing of repository type.
- Adde missing permission checks in list of forks in repository settings.
- Fixes #834 hooks error on remote pulling.
- Fixes issues #849. Web Commits functionality failed for non-ascii files.
- Fixed #850. Whoosh indexer should use the default revision when doing index.
- Fixed #851 and #563 make-index crashes on non-ascii files.
- Fixes #852, flash messages had issies with non-ascii messages

1.6.0 (**2013-05-12**)
----------------------

news
++++

fixes
+++++

- #818: Bookmarks Do Not Display on Changeset View
- Fixed issue with forks form errors rendering
- #819 review status is showed in the main changelog
- Permission update function is idempotent, and doesn't override default
  permissions when doing upgrades
- Fixed some unicode problems with git file path
- Fixed broken handling of adding an htsts headers.
- Fixed redirection loop on changelog for empty repository
- Fixed issue with web-editor that didn't preserve executable bit
  after editing files

1.6.0rc1 (**2013-04-07**)
-------------------------

news
++++

 - Redesign UI, with lots of small improvements.
 - Group management delegation. Group admin can manage a group, and repos
   under it, admin can create child groups inside group he manages.
 - Repository extra fields. Optional unlimited extra fields can be defined for
   each repository to store custom data.
 - API get_repo call includes repo followers now.
 - Large amounts of improvements in pull requests.
 - #734 repo switcher is available in all pages.
 - #733 API invalidate_cache function.
 - Added option to turn on HSTS headers when using SSL.
 - #83 show repo size on summary page.
 - #745 added show full diff link into to big diff message.
 - Deprecated RSS links - ATOM is the present and the future.
 - Add option to define custom lexers for custom extensions for code highlight
   in rcextension module.
 - Git executable is now configurable via .ini files.
 - #689 repositories now has optional detach/delete option for connected forks.
 - Obfuscate password when cloning a remote repo with credentials.
 - #788 tarball cache. zip or compressed tarballs can be optionally cached for
   faster serving.
 - Speed up of last_changeset extraction in VCS.
 - API get_locks function.
 - Configurable HTTP codes for repository locking.
 - Possible to use closed branches in ?branch= in changelog.
 - Linaro's ldap sync scripts.
 - #797 git refs filter is now configurable via .ini file.
 - New ishell paster command for easier administrative tasks.

fixes
+++++

 - #654 switch to handles `/` in branch/tag/bookmark names.
 - #572 moved out password reset tasks from celery.
 - #730 filter out repo groups choices to only ones that you have write+ access.
 - #462 disable file editing when not on branch head.
 - #731 update-repoinfo sometimes failed to update data when changesets were
   initial commits.
 - #749,#805 and #516 Removed duplication of repo settings for rhodecode admins
   and repo admins.
 - Global permission update with "overwrite existing settings" shouldn't
   override private repositories.
 - #642 added recursion limit for stats gathering.
 - #739 Delete/Edit repositories should only point to admin links if the user
   is an super admin.
 - Fixed escaping of html in "patch" view for GIT repos.
 - #747 load changeset cache after forking to refresh lightweight dashboard caches.
 - Quick repo list: public/private icon control should only control icons,
   not repo visibility.
 - #746 UnicodeDedode errors on feed controllers.
 - #756 cleanup repos didn't properly compose paths of repos to be cleaned up.
 - #763 gravatar helper function should fallback into default image if somehow
   email provided is empty.
 - Fixes #762, LDAP and container created users are now activated based on
   the registration settings in permissions.
 - Cleanup would recurse into every leaf and could thus not be used on lots of
   large repositories.
 - Better detection of deleting groups with subgroups inside.
 - Fixed issue with renaming repos group together with changing parents with
   multiple nested trees.
 - #594 web interface file committing executes push hooks.
 - Disallow cloning from different URI's that http[s]/svn/git/hg.
 - Handling of RhodeCode extra params in consistent way.
 - Don't normalize path if it's empty on adding a file through web interface.
 - #808 missing changesets and files should return 404 not redirect
 - #809 added url quote in clone url.
 - Fixed issues with importing non-ascii repo names.
 - Automatically assign instance_id for host and process if it has been set to *
 - Fixed multiple IP addresses in each of extracted IP.
 - Lot of other small bug fixes and improvements.

1.5.4 (**2013-03-13**)
----------------------

news
++++


fixes
+++++

- fixed webtest dependency issues
- fixed issues with celery tasks for password reset
- fixed #763 gravatar helper function should fallback into default image
  if email is empty
- fixes #762 user global activation flag is also respected for LDAP created
  accounts
- use password obfuscate when clonning a remote repo with credentials inside
- fixed issue with renaming repository group together with changing parents
- disallow cloning from file:/// URIs
- handle all cases with multiple IP addresses in proxy headers

1.5.3 (**2013-02-12**)
----------------------

news
++++

- IP restrictions now also enabled for IPv6

fixes
+++++

- fixed issues with private checkbox not always working
- fixed #746 unicodeDedode errors on feed controllers
- fixes issue #756 cleanup repos didn't properly compose paths of repos to be cleaned up.
- fixed cache invalidation issues together with vcs_full_cache option
- repo scan should skip directories with starting with '.'
- fixes for issue #731, update-repoinfo sometimes failed to update data when changesets
  were initial commits
- recursive mode of setting permission skips private repositories

1.5.2 (**2013-01-14**)
----------------------

news
++++

- IP restrictions for users. Each user can get a set of whitelist IP+mask for
  extra protection. Useful for buildbots etc.
- added full last changeset info to lightweight dashboard. lightweight dashboard
  is now fully functional replacement of original dashboard.
- implemented certain API calls for non-admin users.
- enabled all Markdown Extra plugins
- implemented #725 Pull Request View - Show origin repo URL
- show comments from pull requests into associated changesets

fixes
+++++

- update repoinfo script is more failsafe
- fixed #687  Lazy loaded tooltip bug with simultaneous ajax requests
- fixed #691: Notifications for pull requests: move link to top for better
  readability
- fixed #699: fix missing fork docs for API
- fixed #693 Opening changeset from pull request fails
- fixed #710 File view stripping empty lines from beginning and end of file
- fixed issues with getting repos by path on windows, caused GIT hooks to fail
- fixed issues with groups paginator on main dashboard
- improved fetch/pull command for git repos, now pulling all refs
- fixed issue #719 Journal revision ID tooltip AJAX query path is incorrect
  when running in a subdir
- fixed issue #702 API methods without arguments fail when "args":null
- set the status of changesets initially on pull request. Fixes issues #690 and #587

1.5.1 (**2012-12-13**)
----------------------

news
++++

- implements #677: Don't allow to close pull requests when they are
  under-review status
- implemented #670 Implementation of Roles in Pull Request

fixes
+++++

- default permissions can get duplicated after migration
- fixed changeset status labels, they now select radio buttons
- #682 translation difficult for multi-line text
- #683 fixed difference between messages about not mapped repositories
- email: fail nicely when no SMTP server has been configured

1.5.0 (**2012-12-12**)
----------------------

news
++++

- new rewritten from scratch diff engine. 10x faster in edge cases. Handling
  of file renames, copies, change flags and binary files
- added lightweight dashboard option. ref #500. New version of dashboard
  page that doesn't use any VCS data and is super fast to render. Recommended
  for large amount of repositories.
- implements #648 write Script for updating last modification time for
  lightweight dashboard
- implemented compare engine for git repositories.
- LDAP failover, option to specify multiple servers
- added Errormator and Sentry support for monitoring RhodeCode
- implemented #628: Pass server URL to rc-extensions hooks
- new tooltip implementation - added lazy loading of changesets from journal
  pages. This can significantly improve speed of rendering the page
- implements #632,added branch/tag/bookmarks info into feeds
  added changeset link to body of message
- implemented #638 permissions overview to groups
- implements #636, lazy loading of history and authors to speed up source
  pages rendering
- implemented #647, option to pass list of default encoding used to
  encode to/decode from unicode
- added caching layer into RSS/ATOM feeds.
- basic implementation of cherry picking changesets for pull request, ref #575
- implemented #661 Add option to include diff in RSS feed
- implemented file history page for showing detailed changelog for a given file
- implemented #663 Admin/permission: specify default repogroup perms
- implemented #379 defaults settings page for creation of repositories, locking
  statistics, downloads, repository type
- implemented #210 filtering of admin journal based on Whoosh Query language
- added parents/children links in changeset viewref #650

fixes
+++++

- fixed git version checker
- #586 patched basic auth handler to fix issues with git behind proxy
- #589 search urlgenerator didn't properly escape special characters
- fixed issue #614 Include repo name in delete confirmation dialog
- fixed #623: Lang meta-tag doesn't work with C#/C++
- fixes #612 Double quotes to Single quotes result in bad html in diff
- fixes #630 git statistics do too much work making them slow.
- fixes #625 Git-Tags are not displayed in Shortlog
- fix for issue #602, enforce str when setting mercurial UI object.
  When this is used together with mercurial internal translation system
  it can lead to UnicodeDecodeErrors
- fixes #645 Fix git handler when doing delete remote branch
- implements #649 added two seperate method for author and committer to VCS
  changeset class switch author for git backed to be the real author not committer
- fix issue #504 RhodeCode is showing different versions of README on
  different summary page loads
- implemented #658 Changing username in LDAP-Mode should not be allowed.
- fixes #652 switch to generator approach when doing file annotation to prevent
  huge memory consumption
- fixes #666 move lockkey path location to cache_dir to ensure this path is
  always writable for rhodecode server
- many more small fixes and improvements
- fixed issues with recursive scans on removed repositories that could take
  long time on instance start

1.4.4 (**2012-10-08**)
----------------------

news
++++

- obfuscate db password in logs for engine connection string
- #574 Show pull request status also in shortlog (if any)
- remember selected tab in my account page
- Bumped mercurial version to 2.3.2
- #595 rcextension hook for repository delete

fixes
+++++

- Add git version detection to warn users that Git used in system is to
  old. Ref #588 - also show git version in system details in settings page
- fixed files quick filter links
- #590 Add GET flag that controls the way the diff are generated, for pull
  requests we want to use non-bundle based diffs, That are far better for
  doing code reviews. The /compare url still uses bundle compare for full
  comparison including the incoming changesets
- Fixed #585, checks for status of revision where to strict, and made
  opening pull request with those revision impossible due to previously set
  status. Checks now are made also for the repository.
- fixes #591 git backend was causing encoding errors when handling binary
  files - added a test case for VCS lib tests
- fixed #597 commits in future get negative age.
- fixed #598 API docs methods had wrong members parameter as returned data

1.4.3 (**2012-09-28**)
----------------------

news
++++

- #558 Added config file to hooks extra data
- bumped mercurial version to 2.3.1
- #518 added possibility of specifying multiple patterns for issues
- update codemirror to latest version

fixes
+++++

- fixed #570 explicit user group permissions can overwrite owner permissions
- fixed #578 set proper PATH with current Python for Git
  hooks to execute within same Python as RhodeCode
- fixed issue with Git bare repos that ends with .git in name

1.4.2 (**2012-09-12**)
----------------------

news
++++

- added option to menu to quick lock/unlock repository for users that have
  write access to
- Implemented permissions for writing to repo
  groups. Now only write access to group allows to create a repostiory
  within that group
- #565 Add support for {netloc} and {scheme} to alternative_gravatar_url
- updated translation for zh_CN

fixes
+++++

- fixed visual permissions check on repository groups inside groups
- fixed issues with non-ascii search terms in search, and indexers
- fixed parsing of page number in GET parameters
- fixed issues with generating pull-request overview for repos with
  bookmarks and tags, also preview doesn't loose chosen revision from
  select dropdown

1.4.1 (**2012-09-07**)
----------------------

news
++++

- always put a comment about code-review status change even if user send
  empty data
- modified_on column saves repository update and it's going to be used
  later for light version of main page ref #500
- pull request notifications send much nicer emails with details about pull
  request
- #551 show breadcrumbs in summary view for repositories inside a group

fixes
+++++

- fixed migrations of permissions that can lead to inconsistency.
  Some users sent feedback that after upgrading from older versions issues
  with updating default permissions occurred. RhodeCode detects that now and
  resets default user permission to initial state if there is a need for that.
  Also forces users to set the default value for new forking permission.
- #535 improved apache wsgi example configuration in docs
- fixes #550 mercurial repositories comparision failed when origin repo had
  additional not-common changesets
- fixed status of code-review in preview windows of pull request
- git forks were not initialized at bare repos
- fixes #555 fixes issues with comparing non-related repositories
- fixes #557 follower counter always counts up
- fixed issue #560 require push ssl checkbox wasn't shown when option was
  enabled
- fixed #559
- fixed issue #559 fixed bug in routing that mapped repo names with <name>_<num> in name as
  if it was a request to url by repository ID

1.4.0 (**2012-09-03**)
----------------------

news
++++

- new codereview system
- email map, allowing users to have multiple email addresses mapped into
  their accounts
- improved git-hook system. Now all actions for git are logged into journal
  including pushed revisions, user and IP address
- changed setup-app into setup-rhodecode and added default options to it.
- new git repos are created as bare now by default
- #464 added links to groups in permission box
- #465 mentions autocomplete inside comments boxes
- #469 added --update-only option to whoosh to re-index only given list
  of repos in index
- rhodecode-api CLI client
- new git http protocol replaced buggy dulwich implementation.
  Now based on pygrack & gitweb
- Improved RSS/ATOM feeds. Discoverable by browsers using proper headers, and
  reformated based on user suggestions. Additional rss/atom feeds for user
  journal
- various i18n improvements
- #478 permissions overview for admin in user edit view
- File view now displays small gravatars off all authors of given file
- Implemented landing revisions. Each repository will get landing_rev attribute
  that defines 'default' revision/branch for generating readme files
- Implemented #509, RhodeCode enforces SSL for push/pulling if requested at
  earliest possible call.
- Import remote svn repositories to mercurial using hgsubversion.
- Fixed #508 RhodeCode now has a option to explicitly set forking permissions
- RhodeCode can use alternative server for generating avatar icons
- implemented repositories locking. Pull locks, push unlocks. Also can be done
  via API calls
- #538 form for permissions can handle multiple users at once

fixes
+++++

- improved translations
- fixes issue #455 Creating an archive generates an exception on Windows
- fixes #448 Download ZIP archive keeps file in /tmp open and results
  in out of disk space
- fixes issue #454 Search results under Windows include proceeding
  backslash
- fixed issue #450. Rhodecode no longer will crash when bad revision is
  present in journal data.
- fix for issue #417, git execution was broken on windows for certain
  commands.
- fixed #413. Don't disable .git directory for bare repos on deleting
- fixed issue #459. Changed the way of obtaining logger in reindex task.
- fixed #453 added ID field in whoosh SCHEMA that solves the issue of
  reindexing modified files
- fixed #481 rhodecode emails are sent without Date header
- fixed #458 wrong count when no repos are present
- fixed issue #492 missing `\ No newline at end of file` test at the end of
  new chunk in html diff
- full text search now works also for commit messages

1.3.6 (**2012-05-17**)
----------------------

news
++++

- chinese traditional translation
- changed setup-app into setup-rhodecode and added arguments for auto-setup
  mode that doesn't need user interaction

fixes
+++++

- fixed no scm found warning
- fixed __future__ import error on rcextensions
- made simplejson required lib for speedup on JSON encoding
- fixes #449 bad regex could get more than revisions from parsing history
- don't clear DB session when CELERY_EAGER is turned ON

1.3.5 (**2012-05-10**)
----------------------

news
++++

- use ext_json for json module
- unified annotation view with file source view
- notification improvements, better inbox + css
- #419 don't strip passwords for login forms, make rhodecode
  more compatible with LDAP servers
- Added HTTP_X_FORWARDED_FOR as another method of extracting
  IP for pull/push logs. - moved all to base controller
- #415: Adding comment to changeset causes reload.
  Comments are now added via ajax and doesn't reload the page
- #374 LDAP config is discarded when LDAP can't be activated
- limited push/pull operations are now logged for git in the journal
- bumped mercurial to 2.2.X series
- added support for displaying submodules in file-browser
- #421 added bookmarks in changelog view

fixes
+++++

- fixed dev-version marker for stable when served from source codes
- fixed missing permission checks on show forks page
- #418 cast to unicode fixes in notification objects
- #426 fixed mention extracting regex
- fixed remote-pulling for git remotes remopositories
- fixed #434: Error when accessing files or changesets of a git repository
  with submodules
- fixed issue with empty APIKEYS for users after registration ref. #438
- fixed issue with getting README files from git repositories

1.3.4 (**2012-03-28**)
----------------------

news
++++

- Whoosh logging is now controlled by the .ini files logging setup
- added clone-url into edit form on /settings page
- added help text into repo add/edit forms
- created rcextensions module with additional mappings (ref #322) and
  post push/pull/create repo hooks callbacks
- implemented #377 Users view for his own permissions on account page
- #399 added inheritance of permissions for user group on repository groups
- #401 repository group is automatically pre-selected when adding repos
  inside a repository group
- added alternative HTTP 403 response when client failed to authenticate. Helps
  solving issues with Mercurial and LDAP
- #402 removed group prefix from repository name when listing repositories
  inside a group
- added gravatars into permission view and permissions autocomplete
- #347 when running multiple RhodeCode instances, properly invalidates cache
  for all registered servers

fixes
+++++

- fixed #390 cache invalidation problems on repos inside group
- fixed #385 clone by ID url was loosing proxy prefix in URL
- fixed some unicode problems with waitress
- fixed issue with escaping < and > in changeset commits
- fixed error occurring during recursive group creation in API
  create_repo function
- fixed #393 py2.5 fixes for routes url generator
- fixed #397 Private repository groups shows up before login
- fixed #396 fixed problems with revoking users in nested groups
- fixed mysql unicode issues + specified InnoDB as default engine with
  utf8 charset
- #406 trim long branch/tag names in changelog to not break UI

1.3.3 (**2012-03-02**)
----------------------

news
++++


fixes
+++++

- fixed some python2.5 compatibility issues
- fixed issues with removed repos was accidentally added as groups, after
  full rescan of paths
- fixes #376 Cannot edit user (using container auth)
- fixes #378 Invalid image urls on changeset screen with proxy-prefix
  configuration
- fixed initial sorting of repos inside repo group
- fixes issue when user tried to resubmit same permission into user/user_groups
- bumped beaker version that fixes #375 leap error bug
- fixed raw_changeset for git. It was generated with hg patch headers
- fixed vcs issue with last_changeset for filenodes
- fixed missing commit after hook delete
- fixed #372 issues with git operation detection that caused a security issue
  for git repos

1.3.2 (**2012-02-28**)
----------------------

news
++++


fixes
+++++

- fixed git protocol issues with repos-groups
- fixed git remote repos validator that prevented from cloning remote git repos
- fixes #370 ending slashes fixes for repo and groups
- fixes #368 improved git-protocol detection to handle other clients
- fixes #366 When Setting Repository Group To Blank Repo Group Wont Be
  Moved To Root
- fixes #371 fixed issues with beaker/sqlalchemy and non-ascii cache keys
- fixed #373 missing cascade drop on user_group_to_perm table

1.3.1 (**2012-02-27**)
----------------------

news
++++


fixes
+++++

- redirection loop occurs when remember-me wasn't checked during login
- fixes issues with git blob history generation
- don't fetch branch for git in file history dropdown. Causes unneeded slowness

1.3.0 (**2012-02-26**)
----------------------

news
++++

- code review, inspired by github code-comments
- #215 rst and markdown README files support
- #252 Container-based and proxy pass-through authentication support
- #44 branch browser. Filtering of changelog by branches
- mercurial bookmarks support
- new hover top menu, optimized to add maximum size for important views
- configurable clone url template with possibility to specify  protocol like
  ssh:// or http:// and also manually alter other parts of clone_url.
- enabled largefiles extension by default
- optimized summary file pages and saved a lot of unused space in them
- #239 option to manually mark repository as fork
- #320 mapping of commit authors to RhodeCode users
- #304 hashes are displayed using monospace font
- diff configuration, toggle white lines and context lines
- #307 configurable diffs, whitespace toggle, increasing context lines
- sorting on branches, tags and bookmarks using YUI datatable
- improved file filter on files page
- implements #330 api method for listing nodes ar particular revision
- #73 added linking issues in commit messages to chosen issue tracker url
  based on user defined regular expression
- added linking of changesets in commit messages
- new compact changelog with expandable commit messages
- firstname and lastname are optional in user creation
- #348 added post-create repository hook
- #212 global encoding settings is now configurable from .ini files
- #227 added repository groups permissions
- markdown gets codehilite extensions
- new API methods, delete_repositories, grante/revoke permissions for groups
  and repos


fixes
+++++

- rewrote dbsession management for atomic operations, and better error handling
- fixed sorting of repo tables
- #326 escape of special html entities in diffs
- normalized user_name => username in api attributes
- fixes #298 ldap created users with mixed case emails created conflicts
  on saving a form
- fixes issue when owner of a repo couldn't revoke permissions for users
  and groups
- fixes #271 rare JSON serialization problem with statistics
- fixes #337 missing validation check for conflicting names of a group with a
  repository group
- #340 fixed session problem for mysql and celery tasks
- fixed #331 RhodeCode mangles repository names if the a repository group
  contains the "full path" to the repositories
- #355 RhodeCode doesn't store encrypted LDAP passwords

1.2.5 (**2012-01-28**)
----------------------

news
++++

fixes
+++++

- #340 Celery complains about MySQL server gone away, added session cleanup
  for celery tasks
- #341 "scanning for repositories in None" log message during Rescan was missing
  a parameter
- fixed creating archives with subrepos. Some hooks were triggered during that
  operation leading to crash.
- fixed missing email in account page.
- Reverted Mercurial to 2.0.1 for windows due to bug in Mercurial that makes
  forking on windows impossible

1.2.4 (**2012-01-19**)
----------------------

news
++++

- RhodeCode is bundled with mercurial series 2.0.X by default, with
  full support to largefiles extension. Enabled by default in new installations
- #329 Ability to Add/Remove Groups to/from a Repository via AP
- added requires.txt file with requirements

fixes
+++++

- fixes db session issues with celery when emailing admins
- #331 RhodeCode mangles repository names if the a repository group
  contains the "full path" to the repositories
- #298 Conflicting e-mail addresses for LDAP and RhodeCode users
- DB session cleanup after hg protocol operations, fixes issues with
  `mysql has gone away` errors
- #333 doc fixes for get_repo api function
- #271 rare JSON serialization problem with statistics enabled
- #337 Fixes issues with validation of repository name conflicting with
  a group name. A proper message is now displayed.
- #292 made ldap_dn in user edit readonly, to get rid of confusion that field
  doesn't work
- #316 fixes issues with web description in hgrc files

1.2.3 (**2011-11-02**)
----------------------

news
++++

- added option to manage repository group for non admin users
- added following API methods for get_users, create_user, get_users_groups,
  get_users_group, create_users_group, add_user_to_users_groups, get_repos,
  get_repo, create_repo, add_user_to_repo
- implements #237 added password confirmation for my account
  and admin edit user.
- implements #291 email notification for global events are now sent to all
  administrator users, and global config email.

fixes
+++++

- added option for passing auth method for smtp mailer
- #276 issue with adding a single user with id>10 to usergroups
- #277 fixes windows LDAP settings in which missing values breaks the ldap auth
- #288 fixes managing of repos in a group for non admin user

1.2.2 (**2011-10-17**)
----------------------

news
++++

- #226 repo groups are available by path instead of numerical id

fixes
+++++

- #259 Groups with the same name but with different parent group
- #260 Put repo in group, then move group to another group -> repo becomes unavailable
- #258 RhodeCode 1.2 assumes egg folder is writable (lockfiles problems)
- #265 ldap save fails sometimes on converting attributes to booleans,
  added getter and setter into model that will prevent from this on db model level
- fixed problems with timestamps issues #251 and #213
- fixes #266 RhodeCode allows to create repo with the same name and in
  the same parent as group
- fixes #245 Rescan of the repositories on Windows
- fixes #248 cannot edit repos inside a group on windows
- fixes #219 forking problems on windows

1.2.1 (**2011-10-08**)
----------------------

news
++++


fixes
+++++

- fixed problems with basic auth and push problems
- gui fixes
- fixed logger

1.2.0 (**2011-10-07**)
----------------------

news
++++

- implemented #47 repository groups
- implemented #89 Can setup google analytics code from settings menu
- implemented #91 added nicer looking archive urls with more download options
  like tags, branches
- implemented #44 into file browsing, and added follow branch option
- implemented #84 downloads can be enabled/disabled for each repository
- anonymous repository can be cloned without having to pass default:default
  into clone url
- fixed #90 whoosh indexer can index chooses repositories passed in command
  line
- extended journal with day aggregates and paging
- implemented #107 source code lines highlight ranges
- implemented #93 customizable changelog on combined revision ranges -
  equivalent of githubs compare view
- implemented #108 extended and more powerful LDAP configuration
- implemented #56 user groups
- major code rewrites optimized codes for speed and memory usage
- raw and diff downloads are now in git format
- setup command checks for write access to given path
- fixed many issues with international characters and unicode. It uses utf8
  decode with replace to provide less errors even with non utf8 encoded strings
- #125 added API KEY access to feeds
- #109 Repository can be created from external Mercurial link (aka. remote
  repository, and manually updated (via pull) from admin panel
- beta git support - push/pull server + basic view for git repos
- added followers page and forks page
- server side file creation (with binary file upload interface)
  and edition with commits powered by codemirror
- #111 file browser file finder, quick lookup files on whole file tree
- added quick login sliding menu into main page
- changelog uses lazy loading of affected files details, in some scenarios
  this can improve speed of changelog page dramatically especially for
  larger repositories.
- implements #214 added support for downloading subrepos in download menu.
- Added basic API for direct operations on rhodecode via JSON
- Implemented advanced hook management

fixes
+++++

- fixed file browser bug, when switching into given form revision the url was
  not changing
- fixed propagation to error controller on simplehg and simplegit middlewares
- fixed error when trying to make a download on empty repository
- fixed problem with '[' chars in commit messages in journal
- fixed #99 Unicode errors, on file node paths with non utf-8 characters
- journal fork fixes
- removed issue with space inside renamed repository after deletion
- fixed strange issue on formencode imports
- fixed #126 Deleting repository on Windows, rename used incompatible chars.
- #150 fixes for errors on repositories mapped in db but corrupted in
  filesystem
- fixed problem with ascendant characters in realm #181
- fixed problem with sqlite file based database connection pool
- whoosh indexer and code stats share the same dynamic extensions map
- fixes #188 - relationship delete of repo_to_perm entry on user removal
- fixes issue #189 Trending source files shows "show more" when no more exist
- fixes issue #197 Relative paths for pidlocks
- fixes issue #198 password will require only 3 chars now for login form
- fixes issue #199 wrong redirection for non admin users after creating a repository
- fixes issues #202, bad db constraint made impossible to attach same group
  more than one time. Affects only mysql/postgres
- fixes #218 os.kill patch for windows was missing sig param
- improved rendering of dag (they are not trimmed anymore when number of
  heads exceeds 5)

1.1.8 (**2011-04-12**)
----------------------

news
++++

- improved windows support

fixes
+++++

- fixed #140 freeze of python dateutil library, since new version is python2.x
  incompatible
- setup-app will check for write permission in given path
- cleaned up license info issue #149
- fixes for issues #137,#116 and problems with unicode and accented characters.
- fixes crashes on gravatar, when passed in email as unicode
- fixed tooltip flickering problems
- fixed came_from redirection on windows
- fixed logging modules, and sql formatters
- windows fixes for os.kill issue #133
- fixes path splitting for windows issues #148
- fixed issue #143 wrong import on migration to 1.1.X
- fixed problems with displaying binary files, thanks to Thomas Waldmann
- removed name from archive files since it's breaking ui for long repo names
- fixed issue with archive headers sent to browser, thanks to Thomas Waldmann
- fixed compatibility for 1024px displays, and larger dpi settings, thanks to
  Thomas Waldmann
- fixed issue #166 summary pager was skipping 10 revisions on second page


1.1.7 (**2011-03-23**)
----------------------

news
++++

fixes
+++++

- fixed (again) #136 installation support for FreeBSD


1.1.6 (**2011-03-21**)
----------------------

news
++++

fixes
+++++

- fixed #136 installation support for FreeBSD
- RhodeCode will check for python version during installation

1.1.5 (**2011-03-17**)
----------------------

news
++++

- basic windows support, by exchanging pybcrypt into sha256 for windows only
  highly inspired by idea of mantis406

fixes
+++++

- fixed sorting by author in main page
- fixed crashes with diffs on binary files
- fixed #131 problem with boolean values for LDAP
- fixed #122 mysql problems thanks to striker69
- fixed problem with errors on calling raw/raw_files/annotate functions
  with unknown revisions
- fixed returned rawfiles attachment names with international character
- cleaned out docs, big thanks to Jason Harris

1.1.4 (**2011-02-19**)
----------------------

news
++++

fixes
+++++

- fixed formencode import problem on settings page, that caused server crash
  when that page was accessed as first after server start
- journal fixes
- fixed option to access repository just by entering http://server/<repo_name>

1.1.3 (**2011-02-16**)
----------------------

news
++++

- implemented #102 allowing the '.' character in username
- added option to access repository just by entering http://server/<repo_name>
- celery task ignores result for better performance

fixes
+++++

- fixed ehlo command and non auth mail servers on smtp_lib. Thanks to
  apollo13 and Johan Walles
- small fixes in journal
- fixed problems with getting setting for celery from .ini files
- registration, password reset and login boxes share the same title as main
  application now
- fixed #113: to high permissions to fork repository
- fixed problem with '[' chars in commit messages in journal
- removed issue with space inside renamed repository after deletion
- db transaction fixes when filesystem repository creation failed
- fixed #106 relation issues on databases different than sqlite
- fixed static files paths links to use of url() method

1.1.2 (**2011-01-12**)
----------------------

news
++++


fixes
+++++

- fixes #98 protection against float division of percentage stats
- fixed graph bug
- forced webhelpers version since it was making troubles during installation

1.1.1 (**2011-01-06**)
----------------------

news
++++

- added force https option into ini files for easier https usage (no need to
  set server headers with this options)
- small css updates

fixes
+++++

- fixed #96 redirect loop on files view on repositories without changesets
- fixed #97 unicode string passed into server header in special cases (mod_wsgi)
  and server crashed with errors
- fixed large tooltips problems on main page
- fixed #92 whoosh indexer is more error proof

1.1.0 (**2010-12-18**)
----------------------

news
++++

- rewrite of internals for vcs >=0.1.10
- uses mercurial 1.7 with dotencode disabled for maintaining compatibility
  with older clients
- anonymous access, authentication via ldap
- performance upgrade for cached repos list - each repository has its own
  cache that's invalidated when needed.
- performance upgrades on repositories with large amount of commits (20K+)
- main page quick filter for filtering repositories
- user dashboards with ability to follow chosen repositories actions
- sends email to admin on new user registration
- added cache/statistics reset options into repository settings
- more detailed action logger (based on hooks) with pushed changesets lists
  and options to disable those hooks from admin panel
- introduced new enhanced changelog for merges that shows more accurate results
- new improved and faster code stats (based on pygments lexers mapping tables,
  showing up to 10 trending sources for each repository. Additionally stats
  can be disabled in repository settings.
- gui optimizations, fixed application width to 1024px
- added cut off (for large files/changesets) limit into config files
- whoosh, celeryd, upgrade moved to paster command
- other than sqlite database backends can be used

fixes
+++++

- fixes #61 forked repo was showing only after cache expired
- fixes #76 no confirmation on user deletes
- fixes #66 Name field misspelled
- fixes #72 block user removal when he owns repositories
- fixes #69 added password confirmation fields
- fixes #87 RhodeCode crashes occasionally on updating repository owner
- fixes #82 broken annotations on files with more than 1 blank line at the end
- a lot of fixes and tweaks for file browser
- fixed detached session issues
- fixed when user had no repos he would see all repos listed in my account
- fixed ui() instance bug when global hgrc settings was loaded for server
  instance and all hgrc options were merged with our db ui() object
- numerous small bugfixes

(special thanks for TkSoh for detailed feedback)


1.0.2 (**2010-11-12**)
----------------------

news
++++

- tested under python2.7
- bumped sqlalchemy and celery versions

fixes
+++++

- fixed #59 missing graph.js
- fixed repo_size crash when repository had broken symlinks
- fixed python2.5 crashes.


1.0.1 (**2010-11-10**)
----------------------

news
++++

- small css updated

fixes
+++++

- fixed #53 python2.5 incompatible enumerate calls
- fixed #52 disable mercurial extension for web
- fixed #51 deleting repositories don't delete it's dependent objects


1.0.0 (**2010-11-02**)
----------------------

- security bugfix simplehg wasn't checking for permissions on commands
  other than pull or push.
- fixed doubled messages after push or pull in admin journal
- templating and css corrections, fixed repo switcher on chrome, updated titles
- admin menu accessible from options menu on repository view
- permissions cached queries

1.0.0rc4  (**2010-10-12**)
--------------------------

- fixed python2.5 missing simplejson imports (thanks to Jens Bäckman)
- removed cache_manager settings from sqlalchemy meta
- added sqlalchemy cache settings to ini files
- validated password length and added second try of failure on paster setup-app
- fixed setup database destroy prompt even when there was no db


1.0.0rc3 (**2010-10-11**)
-------------------------

- fixed i18n during installation.

1.0.0rc2 (**2010-10-11**)
-------------------------

- Disabled dirsize in file browser, it's causing nasty bug when dir renames
  occure. After vcs is fixed it'll be put back again.
- templating/css rewrites, optimized css.

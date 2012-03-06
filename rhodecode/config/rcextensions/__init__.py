# Additional mappings that are not present in the pygments lexers
# used for building stats
# format is {'ext':'Name'} eg. {'py':'Python'}
# NOTE: that this will overide any mappings in LANGUAGES_EXTENSIONS_MAP
# build by pygments
EXTRA_MAPPINGS = {}

#==============================================================================
# WHOOSH INDEX EXTENSIONS
#==============================================================================
# if INDEX_EXTENSIONS is [] it'll use pygments lexers extensions by default.
# To set your own just add to this list extensions to index with content
INDEX_EXTENSIONS = []

# additional extensions for indexing besides the default from pygments
# those get's added to INDEX_EXTENSIONS
EXTRA_INDEX_EXTENSIONS = []


#==============================================================================
# POST CREATE REPOSITORY HOOK
#==============================================================================
# this function will be executed after each repository is created
def _crhook(*args, **kwargs):
    """
    Post create repository HOOK
    kwargs available:
     :param repo_name:
     :param repo_type:
     :param description:
     :param private:
     :param created_on:
     :param enable_downloads:
     :param repo_id:
     :param user_id:
     :param enable_statistics:
     :param clone_uri:
     :param fork_id:
     :param group_id:
     :param created_by:
    """
    return 0
CREATE_REPO_HOOK = _crhook


#==============================================================================
# POST PUSH HOOK
#==============================================================================

# this function will be executed after each push it's runned after the build-in
# hook that rhodecode uses for logging pushes
def _pushhook(*args, **kwargs):
    """
    Post push hook
    kwargs available:

      :param username: name of user who pushed
      :param ip: ip of who pushed
      :param action: pull
      :param repository: repository name
      :param pushed_revs: generator of pushed revisions
    """
    return 0
PUSH_HOOK = _pushhook


#==============================================================================
# POST PULL HOOK
#==============================================================================

# this function will be executed after each push it's runned after the build-in
# hook that rhodecode uses for logging pushes
def _pullhook(*args, **kwargs):
    """
    Post pull hook
    kwargs available::

      :param username: name of user who pulled
      :param ip: ip of who pushed
      :param action: pull
      :param repository: repository name
    """
    return 0
PULL_HOOK = _pullhook

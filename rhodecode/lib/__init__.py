import os


def get_current_revision(quiet=False):
    """
    Returns tuple of (number, id) from repository containing this package
    or None if repository could not be found.

    :param quiet: prints error for fetching revision if True
    """

    try:
        from rhodecode.lib.vcs import get_repo
        from rhodecode.lib.vcs.utils.helpers import get_scm
        repopath = os.path.join(os.path.dirname(__file__), '..', '..')
        scm = get_scm(repopath)[0]
        repo = get_repo(path=repopath, alias=scm)
        tip = repo.get_changeset()
        return (tip.revision, tip.short_id)
    except Exception, err:
        if not quiet:
            print ("Cannot retrieve rhodecode's revision. Original error "
                   "was: %s" % err)
        return None

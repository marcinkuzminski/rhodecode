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
        repopath = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                '..', '..'))
        scm = get_scm(repopath)[0]
        repo = get_repo(path=repopath, alias=scm)
        wk_dir = repo.workdir
        cur_rev = wk_dir.get_changeset()
        return (cur_rev.revision, cur_rev.short_id)
    except Exception, err:
        if not quiet:
            print ("WARNING: Cannot retrieve rhodecode's revision. "
                   "disregard this if you don't know what that means. "
                   "Original error was: %s" % err)
        return None

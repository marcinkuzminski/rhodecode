.. _subrepos:

=============================================
working with RhodeCode and mercurial subrepos
=============================================

example usage of Subrepos with RhodeCode::

    ## init a simple repo
    hg init repo1
    cd repo1
    echo "file1" > file1
    hg add file1
    hg ci --message "initial file 1"

    #clone subrepo we want to add
    hg clone http://rc.local/subrepo

    ## use path like url to existing repo in RhodeCode
    echo "subrepo = http://rc.local/subrepo" > .hgsub

    hg add .hgsub
    hg ci --message "added remote subrepo"



In file list of repo1 you will see a connected subrepo at revision it was
during cloning.
Clicking in subrepos link should send you to proper repository in RhodeCode

cloning repo1 will also clone attached subrepository.

Next we can edit the subrepo data, and push back to RhodeCode. This will update
both of repositories.

see http://mercurial.aragost.com/kick-start/en/subrepositories/ for more
information about subrepositories

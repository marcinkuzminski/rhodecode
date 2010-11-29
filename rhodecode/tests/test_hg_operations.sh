#!/bin/bash
repo=/tmp/vcs_test_hg_clone
repo_name=vcs_test_hg
user=test_admin
password=test12
echo 'removing repo '$repo
rm -rf '$repo'
hg clone http://$user:$password@127.0.0.1:5000/$repo_name $repo
cd $repo
echo 'some' >> $repo/setup.py && hg ci -m 'ci1' && \
echo 'some' >> $repo/setup.py && hg ci -m 'ci2' && \
echo 'some' >> $repo/setup.py && hg ci -m 'ci3' && \
echo 'some' >> $repo/setup.py && hg ci -m 'ci4' && \
hg push


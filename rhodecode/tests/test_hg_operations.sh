#!/bin/bash
repo=/tmp/vcs_test_hg_clone
echo 'removing repo'$repo
rm -rf '$repo'
hg clone http://test_admin:test12@127.0.0.1:5000/vcs_test_hg $repo
cd $repo
echo 'some' >> $repo/setup.py && hg ci -m 'ci1' && \
echo 'some' >> $repo/setup.py && hg ci -m 'ci2' && \
echo 'some' >> $repo/setup.py && hg ci -m 'ci3' && \
echo 'some' >> $repo/setup.py && hg ci -m 'ci4' && \
hg push


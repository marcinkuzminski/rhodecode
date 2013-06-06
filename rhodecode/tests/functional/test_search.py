import os
from rhodecode.tests import *


class TestSearchController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'))

        response.mustcontain('class="small" id="q" name="q" type="text"')
        # Test response...

    def test_empty_search(self):
        if os.path.isdir(self.index_location):
            raise SkipTest('skipped due to existing index')
        else:
            self.log_user()
            response = self.app.get(url(controller='search', action='index'),
                                    {'q': HG_REPO})
            response.mustcontain('There is no index to search in. '
                                 'Please run whoosh indexer')

    def test_normal_search(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                                {'q': 'def repo'})
        response.mustcontain('58 results')

    def test_repo_search(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                                {'q': 'repository:%s def test' % HG_REPO})

        response.mustcontain('18 results')

    def test_search_last(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                                {'q': 'last:t', 'type': 'commit'})

        response.mustcontain('2 results')

    def test_search_commit_message(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                    {'q': 'bother to ask where to fetch repo during tests',
                     'type': 'commit'})

        response.mustcontain('2 results')
        response.mustcontain('a00c1b6f5d7a6ae678fd553a8b81d92367f7ecf1')
        response.mustcontain('c6eb379775c578a95dad8ddab53f963b80894850')

    def test_search_commit_message_hg_repo(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index',
                                    repo_name=HG_REPO),
                    {'q': 'bother to ask where to fetch repo during tests',
                     'type': 'commit'})

        response.mustcontain('1 results')
        response.mustcontain('a00c1b6f5d7a6ae678fd553a8b81d92367f7ecf1')

    def test_search_commit_changed_file(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                                {'q': 'changed:tests/utils.py',
                                 'type': 'commit'})

        response.mustcontain('29 results')

    def test_search_commit_changed_files_get_commit(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                                {'q': 'changed:vcs/utils/lazy.py',
                                 'type': 'commit'})

        response.mustcontain('11 results')
        response.mustcontain('36e0fc9d2808c5022a24f49d6658330383ed8666')
        response.mustcontain('af182745859d779f17336241a0815d15166ae1ee')
        response.mustcontain('17438a11f72b93f56d0e08e7d1fa79a378578a82')
        response.mustcontain('33fa3223355104431402a888fa77a4e9956feb3e')
        response.mustcontain('d1f898326327e20524fe22417c22d71064fe54a1')
        response.mustcontain('fe568b4081755c12abf6ba673ba777fc02a415f3')
        response.mustcontain('bafe786f0d8c2ff7da5c1dcfcfa577de0b5e92f1')

    def test_search_commit_added_file(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                                {'q': 'added:README.rst',
                                 'type': 'commit'})

        response.mustcontain('2 results')
        #HG
        response.mustcontain('3803844fdbd3b711175fc3da9bdacfcd6d29a6fb')
        #GIT
        response.mustcontain('ff7ca51e58c505fec0dd2491de52c622bb7a806b')

    def test_search_author(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                    {'q': 'author:marcin@python-blog.com raw_id:b986218ba1c9b0d6a259fac9b050b1724ed8e545',
                     'type': 'commit'})

        response.mustcontain('1 results')

    def test_search_file_name(self):
        self.log_user()
        response = self.app.get(url(controller='search', action='index'),
                    {'q': 'README.rst', 'type': 'path'})

        response.mustcontain('2 results')

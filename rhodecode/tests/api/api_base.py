from __future__ import with_statement
import random
import mock

from rhodecode.tests import *
from rhodecode.lib.compat import json
from rhodecode.lib.auth import AuthUser
from rhodecode.model.user import UserModel
from rhodecode.model.users_group import UsersGroupModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.meta import Session

API_URL = '/_admin/api'


def _build_data(apikey, method, **kw):
    """
    Builds API data with given random ID

    :param random_id:
    :type random_id:
    """
    random_id = random.randrange(1, 9999)
    return random_id, json.dumps({
        "id": random_id,
        "api_key": apikey,
        "method": method,
        "args": kw
    })

jsonify = lambda obj: json.loads(json.dumps(obj))


def crash(*args, **kwargs):
    raise Exception('Total Crash !')


TEST_USERS_GROUP = 'test_users_group'


def make_users_group(name=TEST_USERS_GROUP):
    gr = UsersGroupModel().create(name=name)
    UsersGroupModel().add_user_to_group(users_group=gr,
                                        user=TEST_USER_ADMIN_LOGIN)
    Session().commit()
    return gr


def destroy_users_group(name=TEST_USERS_GROUP):
    UsersGroupModel().delete(users_group=name, force=True)
    Session().commit()


def create_repo(repo_name, repo_type):
    # create new repo
    form_data = dict(repo_name=repo_name,
                     repo_name_full=repo_name,
                     fork_name=None,
                     description='description %s' % repo_name,
                     repo_group=None,
                     private=False,
                     repo_type=repo_type,
                     clone_uri=None,
                     landing_rev='tip')
    cur_user = UserModel().get_by_username(TEST_USER_ADMIN_LOGIN)
    r = RepoModel().create(form_data, cur_user)
    Session().commit()
    return r


def create_fork(fork_name, fork_type, fork_of):
    fork = RepoModel(Session())._get_repo(fork_of)
    r = create_repo(fork_name, fork_type)
    r.fork = fork
    Session().add(r)
    Session().commit()
    return r


def destroy_repo(repo_name):
    RepoModel().delete(repo_name)
    Session().commit()


class BaseTestApi(object):
    REPO = None
    REPO_TYPE = None

    @classmethod
    def setUpClass(self):
        self.usr = UserModel().get_by_username(TEST_USER_ADMIN_LOGIN)
        self.apikey = self.usr.api_key
        self.TEST_USER = UserModel().create_or_update(
            username='test-api',
            password='test',
            email='test@api.rhodecode.org',
            firstname='first',
            lastname='last'
        )
        Session().commit()
        self.TEST_USER_LOGIN = self.TEST_USER.username

    @classmethod
    def teardownClass(self):
        pass

    def setUp(self):
        self.maxDiff = None
        make_users_group()

    def tearDown(self):
        destroy_users_group()

    def _compare_ok(self, id_, expected, given):
        expected = jsonify({
            'id': id_,
            'error': None,
            'result': expected
        })
        given = json.loads(given)
        self.assertEqual(expected, given)

    def _compare_error(self, id_, expected, given):
        expected = jsonify({
            'id': id_,
            'error': expected,
            'result': None
        })
        given = json.loads(given)
        self.assertEqual(expected, given)

#    def test_Optional(self):
#        from rhodecode.controllers.api.api import Optional
#        option1 = Optional(None)
#        self.assertEqual('<Optional:%s>' % None, repr(option1))
#
#        self.assertEqual(1, Optional.extract(Optional(1)))
#        self.assertEqual('trololo', Optional.extract('trololo'))

    def test_api_wrong_key(self):
        id_, params = _build_data('trololo', 'get_user')
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'Invalid API KEY'
        self._compare_error(id_, expected, given=response.body)

    def test_api_missing_non_optional_param(self):
        id_, params = _build_data(self.apikey, 'get_user')
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'Missing non optional `userid` arg in JSON DATA'
        self._compare_error(id_, expected, given=response.body)

    def test_api_get_users(self):
        id_, params = _build_data(self.apikey, 'get_users',)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        ret_all = []
        for usr in UserModel().get_all():
            ret = usr.get_api_data()
            ret_all.append(jsonify(ret))
        expected = ret_all
        self._compare_ok(id_, expected, given=response.body)

    def test_api_get_user(self):
        id_, params = _build_data(self.apikey, 'get_user',
                                  userid=TEST_USER_ADMIN_LOGIN)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        usr = UserModel().get_by_username(TEST_USER_ADMIN_LOGIN)
        ret = usr.get_api_data()
        ret['permissions'] = AuthUser(usr.user_id).permissions

        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    def test_api_get_user_that_does_not_exist(self):
        id_, params = _build_data(self.apikey, 'get_user',
                                  userid='trololo')
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = "user `%s` does not exist" % 'trololo'
        self._compare_error(id_, expected, given=response.body)

    def test_api_pull(self):
        #TODO: issues with rhodecode_extras here.. not sure why !
        pass

#        repo_name = 'test_pull'
#        r = create_repo(repo_name, self.REPO_TYPE)
#        r.clone_uri = TEST_self.REPO
#        Session.add(r)
#        Session.commit()
#
#        id_, params = _build_data(self.apikey, 'pull',
#                                  repoid=repo_name,)
#        response = self.app.post(API_URL, content_type='application/json',
#                                 params=params)
#
#        expected = 'Pulled from `%s`' % repo_name
#        self._compare_ok(id_, expected, given=response.body)
#
#        destroy_repo(repo_name)

    def test_api_pull_error(self):
        id_, params = _build_data(self.apikey, 'pull',
                                  repoid=self.REPO,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'Unable to pull changes from `%s`' % self.REPO
        self._compare_error(id_, expected, given=response.body)

    def test_api_create_existing_user(self):
        id_, params = _build_data(self.apikey, 'create_user',
                                  username=TEST_USER_ADMIN_LOGIN,
                                  email='test@foo.com',
                                  password='trololo')
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = "user `%s` already exist" % TEST_USER_ADMIN_LOGIN
        self._compare_error(id_, expected, given=response.body)

    def test_api_create_user_with_existing_email(self):
        id_, params = _build_data(self.apikey, 'create_user',
                                  username=TEST_USER_ADMIN_LOGIN + 'new',
                                  email=TEST_USER_REGULAR_EMAIL,
                                  password='trololo')
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = "email `%s` already exist" % TEST_USER_REGULAR_EMAIL
        self._compare_error(id_, expected, given=response.body)

    def test_api_create_user(self):
        username = 'test_new_api_user'
        email = username + "@foo.com"

        id_, params = _build_data(self.apikey, 'create_user',
                                  username=username,
                                  email=email,
                                  password='trololo')
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        usr = UserModel().get_by_username(username)
        ret = dict(
            msg='created new user `%s`' % username,
            user=jsonify(usr.get_api_data())
        )

        expected = ret
        self._compare_ok(id_, expected, given=response.body)

        UserModel().delete(usr.user_id)
        self.Session().commit()

    @mock.patch.object(UserModel, 'create_or_update', crash)
    def test_api_create_user_when_exception_happened(self):

        username = 'test_new_api_user'
        email = username + "@foo.com"

        id_, params = _build_data(self.apikey, 'create_user',
                                  username=username,
                                  email=email,
                                  password='trololo')
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        expected = 'failed to create user `%s`' % username
        self._compare_error(id_, expected, given=response.body)

    def test_api_delete_user(self):
        usr = UserModel().create_or_update(username=u'test_user',
                                           password=u'qweqwe',
                                           email=u'u232@rhodecode.org',
                                           firstname=u'u1', lastname=u'u1')
        self.Session().commit()
        username = usr.username
        email = usr.email
        usr_id = usr.user_id
        ## DELETE THIS USER NOW

        id_, params = _build_data(self.apikey, 'delete_user',
                                  userid=username,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        ret = {'msg': 'deleted user ID:%s %s' % (usr_id, username),
               'user': None}
        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    @mock.patch.object(UserModel, 'delete', crash)
    def test_api_delete_user_when_exception_happened(self):
        usr = UserModel().create_or_update(username=u'test_user',
                                           password=u'qweqwe',
                                           email=u'u232@rhodecode.org',
                                           firstname=u'u1', lastname=u'u1')
        self.Session().commit()
        username = usr.username

        id_, params = _build_data(self.apikey, 'delete_user',
                                  userid=username,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        ret = 'failed to delete ID:%s %s' % (usr.user_id,
                                             usr.username)
        expected = ret
        self._compare_error(id_, expected, given=response.body)

    @parameterized.expand([('firstname', 'new_username'),
                           ('lastname', 'new_username'),
                           ('email', 'new_username'),
                           ('admin', True),
                           ('admin', False),
                           ('ldap_dn', 'test'),
                           ('ldap_dn', None),
                           ('active', False),
                           ('active', True),
                           ('password', 'newpass')
                           ])
    def test_api_update_user(self, name, expected):
        usr = UserModel().get_by_username(self.TEST_USER_LOGIN)
        kw = {name: expected,
              'userid': usr.user_id}
        id_, params = _build_data(self.apikey, 'update_user', **kw)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        ret = {
        'msg': 'updated user ID:%s %s' % (usr.user_id, self.TEST_USER_LOGIN),
        'user': jsonify(UserModel()\
                            .get_by_username(self.TEST_USER_LOGIN)\
                            .get_api_data())
        }

        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    def test_api_update_user_no_changed_params(self):
        usr = UserModel().get_by_username(TEST_USER_ADMIN_LOGIN)
        ret = jsonify(usr.get_api_data())
        id_, params = _build_data(self.apikey, 'update_user',
                                  userid=TEST_USER_ADMIN_LOGIN)

        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        ret = {
        'msg': 'updated user ID:%s %s' % (usr.user_id, TEST_USER_ADMIN_LOGIN),
        'user': ret
        }
        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    def test_api_update_user_by_user_id(self):
        usr = UserModel().get_by_username(TEST_USER_ADMIN_LOGIN)
        ret = jsonify(usr.get_api_data())
        id_, params = _build_data(self.apikey, 'update_user',
                                  userid=usr.user_id)

        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        ret = {
        'msg': 'updated user ID:%s %s' % (usr.user_id, TEST_USER_ADMIN_LOGIN),
        'user': ret
        }
        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    @mock.patch.object(UserModel, 'update_user', crash)
    def test_api_update_user_when_exception_happens(self):
        usr = UserModel().get_by_username(TEST_USER_ADMIN_LOGIN)
        ret = jsonify(usr.get_api_data())
        id_, params = _build_data(self.apikey, 'update_user',
                                  userid=usr.user_id)

        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        ret = 'failed to update user `%s`' % usr.user_id

        expected = ret
        self._compare_error(id_, expected, given=response.body)

    def test_api_get_repo(self):
        new_group = 'some_new_group'
        make_users_group(new_group)
        RepoModel().grant_users_group_permission(repo=self.REPO,
                                                 group_name=new_group,
                                                 perm='repository.read')
        self.Session().commit()
        id_, params = _build_data(self.apikey, 'get_repo',
                                  repoid=self.REPO)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        repo = RepoModel().get_by_repo_name(self.REPO)
        ret = repo.get_api_data()

        members = []
        for user in repo.repo_to_perm:
            perm = user.permission.permission_name
            user = user.user
            user_data = user.get_api_data()
            user_data['type'] = "user"
            user_data['permission'] = perm
            members.append(user_data)

        for users_group in repo.users_group_to_perm:
            perm = users_group.permission.permission_name
            users_group = users_group.users_group
            users_group_data = users_group.get_api_data()
            users_group_data['type'] = "users_group"
            users_group_data['permission'] = perm
            members.append(users_group_data)

        ret['members'] = members

        expected = ret
        self._compare_ok(id_, expected, given=response.body)
        destroy_users_group(new_group)

    def test_api_get_repo_that_doesn_not_exist(self):
        id_, params = _build_data(self.apikey, 'get_repo',
                                  repoid='no-such-repo')
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        ret = 'repository `%s` does not exist' % 'no-such-repo'
        expected = ret
        self._compare_error(id_, expected, given=response.body)

    def test_api_get_repos(self):
        id_, params = _build_data(self.apikey, 'get_repos')
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        result = []
        for repo in RepoModel().get_all():
            result.append(repo.get_api_data())
        ret = jsonify(result)

        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    @parameterized.expand([('all', 'all'),
                           ('dirs', 'dirs'),
                           ('files', 'files'), ])
    def test_api_get_repo_nodes(self, name, ret_type):
        rev = 'tip'
        path = '/'
        id_, params = _build_data(self.apikey, 'get_repo_nodes',
                                  repoid=self.REPO, revision=rev,
                                  root_path=path,
                                  ret_type=ret_type)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        # we don't the actual return types here since it's tested somewhere
        # else
        expected = json.loads(response.body)['result']
        self._compare_ok(id_, expected, given=response.body)

    def test_api_get_repo_nodes_bad_revisions(self):
        rev = 'i-dont-exist'
        path = '/'
        id_, params = _build_data(self.apikey, 'get_repo_nodes',
                                  repoid=self.REPO, revision=rev,
                                  root_path=path,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to get repo: `%s` nodes' % self.REPO
        self._compare_error(id_, expected, given=response.body)

    def test_api_get_repo_nodes_bad_path(self):
        rev = 'tip'
        path = '/idontexits'
        id_, params = _build_data(self.apikey, 'get_repo_nodes',
                                  repoid=self.REPO, revision=rev,
                                  root_path=path,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to get repo: `%s` nodes' % self.REPO
        self._compare_error(id_, expected, given=response.body)

    def test_api_get_repo_nodes_bad_ret_type(self):
        rev = 'tip'
        path = '/'
        ret_type = 'error'
        id_, params = _build_data(self.apikey, 'get_repo_nodes',
                                  repoid=self.REPO, revision=rev,
                                  root_path=path,
                                  ret_type=ret_type)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'ret_type must be one of %s' % (['files', 'dirs', 'all'])
        self._compare_error(id_, expected, given=response.body)

    def test_api_create_repo(self):
        repo_name = 'api-repo'
        id_, params = _build_data(self.apikey, 'create_repo',
                                    repo_name=repo_name,
                                    owner=TEST_USER_ADMIN_LOGIN,
                                    repo_type='hg',
                                  )
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        repo = RepoModel().get_by_repo_name(repo_name)
        ret = {
            'msg': 'Created new repository `%s`' % repo_name,
            'repo': jsonify(repo.get_api_data())
        }
        expected = ret
        self._compare_ok(id_, expected, given=response.body)
        destroy_repo(repo_name)

    def test_api_create_repo_unknown_owner(self):
        repo_name = 'api-repo'
        owner = 'i-dont-exist'
        id_, params = _build_data(self.apikey, 'create_repo',
                                    repo_name=repo_name,
                                    owner=owner,
                                    repo_type='hg',
                                  )
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        expected = 'user `%s` does not exist' % owner
        self._compare_error(id_, expected, given=response.body)

    def test_api_create_repo_exists(self):
        repo_name = self.REPO
        id_, params = _build_data(self.apikey, 'create_repo',
                                    repo_name=repo_name,
                                    owner=TEST_USER_ADMIN_LOGIN,
                                    repo_type='hg',
                                  )
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        expected = "repo `%s` already exist" % repo_name
        self._compare_error(id_, expected, given=response.body)

    @mock.patch.object(RepoModel, 'create_repo', crash)
    def test_api_create_repo_exception_occurred(self):
        repo_name = 'api-repo'
        id_, params = _build_data(self.apikey, 'create_repo',
                                    repo_name=repo_name,
                                    owner=TEST_USER_ADMIN_LOGIN,
                                    repo_type='hg',
                                  )
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        expected = 'failed to create repository `%s`' % repo_name
        self._compare_error(id_, expected, given=response.body)

    def test_api_delete_repo(self):
        repo_name = 'api_delete_me'
        create_repo(repo_name, self.REPO_TYPE)

        id_, params = _build_data(self.apikey, 'delete_repo',
                                  repoid=repo_name,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        ret = {
            'msg': 'Deleted repository `%s`' % repo_name,
            'success': True
        }
        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    def test_api_delete_repo_exception_occurred(self):
        repo_name = 'api_delete_me'
        create_repo(repo_name, self.REPO_TYPE)
        try:
            with mock.patch.object(RepoModel, 'delete', crash):
                id_, params = _build_data(self.apikey, 'delete_repo',
                                          repoid=repo_name,)
                response = self.app.post(API_URL, content_type='application/json',
                                         params=params)

                expected = 'failed to delete repository `%s`' % repo_name
                self._compare_error(id_, expected, given=response.body)
        finally:
            destroy_repo(repo_name)

    def test_api_fork_repo(self):
        fork_name = 'api-repo-fork'
        id_, params = _build_data(self.apikey, 'fork_repo',
                                    repoid=self.REPO,
                                    fork_name=fork_name,
                                    owner=TEST_USER_ADMIN_LOGIN,
                                  )
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        ret = {
            'msg': 'Created fork of `%s` as `%s`' % (self.REPO,
                                                     fork_name),
            'success': True
        }
        expected = ret
        self._compare_ok(id_, expected, given=response.body)
        destroy_repo(fork_name)

    def test_api_fork_repo_unknown_owner(self):
        fork_name = 'api-repo-fork'
        owner = 'i-dont-exist'
        id_, params = _build_data(self.apikey, 'fork_repo',
                                    repoid=self.REPO,
                                    fork_name=fork_name,
                                    owner=owner,
                                  )
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)
        expected = 'user `%s` does not exist' % owner
        self._compare_error(id_, expected, given=response.body)

    def test_api_fork_repo_fork_exists(self):
        fork_name = 'api-repo-fork'
        create_fork(fork_name, self.REPO_TYPE, self.REPO)

        try:
            fork_name = 'api-repo-fork'

            id_, params = _build_data(self.apikey, 'fork_repo',
                                        repoid=self.REPO,
                                        fork_name=fork_name,
                                        owner=TEST_USER_ADMIN_LOGIN,
                                      )
            response = self.app.post(API_URL, content_type='application/json',
                                     params=params)

            expected = "fork `%s` already exist" % fork_name
            self._compare_error(id_, expected, given=response.body)
        finally:
            destroy_repo(fork_name)

    def test_api_fork_repo_repo_exists(self):
        fork_name = self.REPO

        id_, params = _build_data(self.apikey, 'fork_repo',
                                    repoid=self.REPO,
                                    fork_name=fork_name,
                                    owner=TEST_USER_ADMIN_LOGIN,
                                  )
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = "repo `%s` already exist" % fork_name
        self._compare_error(id_, expected, given=response.body)

    @mock.patch.object(RepoModel, 'create_fork', crash)
    def test_api_fork_repo_exception_occurred(self):
        fork_name = 'api-repo-fork'
        id_, params = _build_data(self.apikey, 'fork_repo',
                                    repoid=self.REPO,
                                    fork_name=fork_name,
                                    owner=TEST_USER_ADMIN_LOGIN,
                                  )
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to fork repository `%s` as `%s`' % (self.REPO,
                                                               fork_name)
        self._compare_error(id_, expected, given=response.body)

    def test_api_get_users_group(self):
        id_, params = _build_data(self.apikey, 'get_users_group',
                                  usersgroupid=TEST_USERS_GROUP)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        users_group = UsersGroupModel().get_group(TEST_USERS_GROUP)
        members = []
        for user in users_group.members:
            user = user.user
            members.append(user.get_api_data())

        ret = users_group.get_api_data()
        ret['members'] = members
        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    def test_api_get_users_groups(self):

        make_users_group('test_users_group2')

        id_, params = _build_data(self.apikey, 'get_users_groups',)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = []
        for gr_name in [TEST_USERS_GROUP, 'test_users_group2']:
            users_group = UsersGroupModel().get_group(gr_name)
            ret = users_group.get_api_data()
            expected.append(ret)
        self._compare_ok(id_, expected, given=response.body)

        UsersGroupModel().delete(users_group='test_users_group2')
        self.Session().commit()

    def test_api_create_users_group(self):
        group_name = 'some_new_group'
        id_, params = _build_data(self.apikey, 'create_users_group',
                                  group_name=group_name)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        ret = {
            'msg': 'created new users group `%s`' % group_name,
            'users_group': jsonify(UsersGroupModel()\
                                   .get_by_name(group_name)\
                                   .get_api_data())
        }
        expected = ret
        self._compare_ok(id_, expected, given=response.body)

        destroy_users_group(group_name)

    def test_api_get_users_group_that_exist(self):
        id_, params = _build_data(self.apikey, 'create_users_group',
                                  group_name=TEST_USERS_GROUP)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = "users group `%s` already exist" % TEST_USERS_GROUP
        self._compare_error(id_, expected, given=response.body)

    @mock.patch.object(UsersGroupModel, 'create', crash)
    def test_api_get_users_group_exception_occurred(self):
        group_name = 'exception_happens'
        id_, params = _build_data(self.apikey, 'create_users_group',
                                  group_name=group_name)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to create group `%s`' % group_name
        self._compare_error(id_, expected, given=response.body)

    def test_api_add_user_to_users_group(self):
        gr_name = 'test_group'
        UsersGroupModel().create(gr_name)
        self.Session().commit()
        id_, params = _build_data(self.apikey, 'add_user_to_users_group',
                                  usersgroupid=gr_name,
                                  userid=TEST_USER_ADMIN_LOGIN)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = {
                    'msg': 'added member `%s` to users group `%s`' % (
                                TEST_USER_ADMIN_LOGIN, gr_name
                            ),
                    'success': True}
        self._compare_ok(id_, expected, given=response.body)

        UsersGroupModel().delete(users_group=gr_name)
        self.Session().commit()

    def test_api_add_user_to_users_group_that_doesnt_exist(self):
        id_, params = _build_data(self.apikey, 'add_user_to_users_group',
                                  usersgroupid='false-group',
                                  userid=TEST_USER_ADMIN_LOGIN)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'users group `%s` does not exist' % 'false-group'
        self._compare_error(id_, expected, given=response.body)

    @mock.patch.object(UsersGroupModel, 'add_user_to_group', crash)
    def test_api_add_user_to_users_group_exception_occurred(self):
        gr_name = 'test_group'
        UsersGroupModel().create(gr_name)
        self.Session().commit()
        id_, params = _build_data(self.apikey, 'add_user_to_users_group',
                                  usersgroupid=gr_name,
                                  userid=TEST_USER_ADMIN_LOGIN)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to add member to users group `%s`' % gr_name
        self._compare_error(id_, expected, given=response.body)

        UsersGroupModel().delete(users_group=gr_name)
        self.Session().commit()

    def test_api_remove_user_from_users_group(self):
        gr_name = 'test_group_3'
        gr = UsersGroupModel().create(gr_name)
        UsersGroupModel().add_user_to_group(gr, user=TEST_USER_ADMIN_LOGIN)
        self.Session().commit()
        id_, params = _build_data(self.apikey, 'remove_user_from_users_group',
                                  usersgroupid=gr_name,
                                  userid=TEST_USER_ADMIN_LOGIN)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = {
                    'msg': 'removed member `%s` from users group `%s`' % (
                                TEST_USER_ADMIN_LOGIN, gr_name
                            ),
                    'success': True}
        self._compare_ok(id_, expected, given=response.body)

        UsersGroupModel().delete(users_group=gr_name)
        self.Session().commit()

    @mock.patch.object(UsersGroupModel, 'remove_user_from_group', crash)
    def test_api_remove_user_from_users_group_exception_occurred(self):
        gr_name = 'test_group_3'
        gr = UsersGroupModel().create(gr_name)
        UsersGroupModel().add_user_to_group(gr, user=TEST_USER_ADMIN_LOGIN)
        self.Session().commit()
        id_, params = _build_data(self.apikey, 'remove_user_from_users_group',
                                  usersgroupid=gr_name,
                                  userid=TEST_USER_ADMIN_LOGIN)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to remove member from users group `%s`' % gr_name
        self._compare_error(id_, expected, given=response.body)

        UsersGroupModel().delete(users_group=gr_name)
        self.Session().commit()

    @parameterized.expand([('none', 'repository.none'),
                           ('read', 'repository.read'),
                           ('write', 'repository.write'),
                           ('admin', 'repository.admin')])
    def test_api_grant_user_permission(self, name, perm):
        id_, params = _build_data(self.apikey, 'grant_user_permission',
                                  repoid=self.REPO,
                                  userid=TEST_USER_ADMIN_LOGIN,
                                  perm=perm)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        ret = {
                'msg': 'Granted perm: `%s` for user: `%s` in repo: `%s`' % (
                    perm, TEST_USER_ADMIN_LOGIN, self.REPO
                ),
                'success': True
            }
        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    def test_api_grant_user_permission_wrong_permission(self):
        perm = 'haha.no.permission'
        id_, params = _build_data(self.apikey, 'grant_user_permission',
                                  repoid=self.REPO,
                                  userid=TEST_USER_ADMIN_LOGIN,
                                  perm=perm)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'permission `%s` does not exist' % perm
        self._compare_error(id_, expected, given=response.body)

    @mock.patch.object(RepoModel, 'grant_user_permission', crash)
    def test_api_grant_user_permission_exception_when_adding(self):
        perm = 'repository.read'
        id_, params = _build_data(self.apikey, 'grant_user_permission',
                                  repoid=self.REPO,
                                  userid=TEST_USER_ADMIN_LOGIN,
                                  perm=perm)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to edit permission for user: `%s` in repo: `%s`' % (
                    TEST_USER_ADMIN_LOGIN, self.REPO
                )
        self._compare_error(id_, expected, given=response.body)

    def test_api_revoke_user_permission(self):
        id_, params = _build_data(self.apikey, 'revoke_user_permission',
                                  repoid=self.REPO,
                                  userid=TEST_USER_ADMIN_LOGIN,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = {
            'msg': 'Revoked perm for user: `%s` in repo: `%s`' % (
                TEST_USER_ADMIN_LOGIN, self.REPO
            ),
            'success': True
        }
        self._compare_ok(id_, expected, given=response.body)

    @mock.patch.object(RepoModel, 'revoke_user_permission', crash)
    def test_api_revoke_user_permission_exception_when_adding(self):
        id_, params = _build_data(self.apikey, 'revoke_user_permission',
                                  repoid=self.REPO,
                                  userid=TEST_USER_ADMIN_LOGIN,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to edit permission for user: `%s` in repo: `%s`' % (
                    TEST_USER_ADMIN_LOGIN, self.REPO
                )
        self._compare_error(id_, expected, given=response.body)

    @parameterized.expand([('none', 'repository.none'),
                           ('read', 'repository.read'),
                           ('write', 'repository.write'),
                           ('admin', 'repository.admin')])
    def test_api_grant_users_group_permission(self, name, perm):
        id_, params = _build_data(self.apikey, 'grant_users_group_permission',
                                  repoid=self.REPO,
                                  usersgroupid=TEST_USERS_GROUP,
                                  perm=perm)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        ret = {
            'msg': 'Granted perm: `%s` for users group: `%s` in repo: `%s`' % (
                perm, TEST_USERS_GROUP, self.REPO
            ),
            'success': True
        }
        expected = ret
        self._compare_ok(id_, expected, given=response.body)

    def test_api_grant_users_group_permission_wrong_permission(self):
        perm = 'haha.no.permission'
        id_, params = _build_data(self.apikey, 'grant_users_group_permission',
                                  repoid=self.REPO,
                                  usersgroupid=TEST_USERS_GROUP,
                                  perm=perm)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'permission `%s` does not exist' % perm
        self._compare_error(id_, expected, given=response.body)

    @mock.patch.object(RepoModel, 'grant_users_group_permission', crash)
    def test_api_grant_users_group_permission_exception_when_adding(self):
        perm = 'repository.read'
        id_, params = _build_data(self.apikey, 'grant_users_group_permission',
                                  repoid=self.REPO,
                                  usersgroupid=TEST_USERS_GROUP,
                                  perm=perm)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to edit permission for users group: `%s` in repo: `%s`' % (
                    TEST_USERS_GROUP, self.REPO
                )
        self._compare_error(id_, expected, given=response.body)

    def test_api_revoke_users_group_permission(self):
        RepoModel().grant_users_group_permission(repo=self.REPO,
                                                 group_name=TEST_USERS_GROUP,
                                                 perm='repository.read')
        self.Session().commit()
        id_, params = _build_data(self.apikey, 'revoke_users_group_permission',
                                  repoid=self.REPO,
                                  usersgroupid=TEST_USERS_GROUP,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = {
            'msg': 'Revoked perm for users group: `%s` in repo: `%s`' % (
                TEST_USERS_GROUP, self.REPO
            ),
            'success': True
        }
        self._compare_ok(id_, expected, given=response.body)

    @mock.patch.object(RepoModel, 'revoke_users_group_permission', crash)
    def test_api_revoke_users_group_permission_exception_when_adding(self):

        id_, params = _build_data(self.apikey, 'revoke_users_group_permission',
                                  repoid=self.REPO,
                                  usersgroupid=TEST_USERS_GROUP,)
        response = self.app.post(API_URL, content_type='application/json',
                                 params=params)

        expected = 'failed to edit permission for users group: `%s` in repo: `%s`' % (
                    TEST_USERS_GROUP, self.REPO
                )
        self._compare_error(id_, expected, given=response.body)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ldap
import urllib2
import uuid

try:
    from rhodecode.lib.compat import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

from ConfigParser import ConfigParser

config = ConfigParser()
config.read('ldap_sync.conf')


class InvalidResponseIDError(Exception):
    """ Request and response don't have the same UUID. """


class RhodecodeResponseError(Exception):
    """ Response has an error, something went wrong with request execution. """


class UserAlreadyInGroupError(Exception):
    """ User is already a member of the target group. """


class UserNotInGroupError(Exception):
    """ User is not a member of the target group. """


class RhodecodeAPI():

    def __init__(self, url, key):
        self.url = url
        self.key = key

    def get_api_data(self, uid, method, args):
        """Prepare dict for API post."""
        return {
            "id": uid,
            "api_key": self.key,
            "method": method,
            "args": args
        }

    def rhodecode_api_post(self, method, args):
        """Send a generic API post to Rhodecode.

        This will generate the UUID for validation check after the
        response is returned. Handle errors and get the result back.
        """
        uid = str(uuid.uuid1())
        data = self.get_api_data(uid, method, args)

        data = json.dumps(data)
        headers = {'content-type': 'text/plain'}
        req = urllib2.Request(self.url, data, headers)

        response = urllib2.urlopen(req)
        response = json.load(response)

        if uid != response["id"]:
            raise InvalidResponseIDError("UUID does not match.")

        if response["error"] != None:
            raise RhodecodeResponseError(response["error"])

        return response["result"]

    def create_group(self, name, active=True):
        """Create the Rhodecode user group."""
        args = {
            "group_name": name,
            "active": str(active)
        }
        self.rhodecode_api_post("create_users_group", args)

    def add_membership(self, group, username):
        """Add specific user to a group."""
        args = {
            "usersgroupid": group,
            "userid": username
        }
        result = self.rhodecode_api_post("add_user_to_users_group", args)
        if not result["success"]:
            raise UserAlreadyInGroupError("User %s already in group %s." %
                                          (username, group))

    def remove_membership(self, group, username):
        """Remove specific user from a group."""
        args = {
            "usersgroupid": group,
            "userid": username
        }
        result = self.rhodecode_api_post("remove_user_from_users_group", args)
        if not result["success"]:
            raise UserNotInGroupError("User %s not in group %s." %
                                      (username, group))

    def get_group_members(self, name):
        """Get the list of member usernames from a user group."""
        args = {"usersgroupid": name}
        members = self.rhodecode_api_post("get_users_group", args)['members']
        member_list = []
        for member in members:
            member_list.append(member["username"])
        return member_list

    def get_group(self, name):
        """Return group info."""
        args = {"usersgroupid": name}
        return self.rhodecode_api_post("get_users_group", args)

    def get_user(self, username):
        """Return user info."""
        args = {"userid": username}
        return self.rhodecode_api_post("get_user", args)


class LdapClient():

    def __init__(self, uri, user, key, base_dn):
        self.client = ldap.initialize(uri, trace_level=0)
        self.client.set_option(ldap.OPT_REFERRALS, 0)
        self.client.simple_bind(user, key)
        self.base_dn = base_dn

    def __del__(self):
        self.client.unbind()

    def get_groups(self):
        """Get all the groups in form of dict {group_name: group_info,...}."""
        searchFilter = "objectClass=groupOfUniqueNames"
        result = self.client.search_s(self.base_dn, ldap.SCOPE_SUBTREE,
                                      searchFilter)

        groups = {}
        for group in result:
            groups[group[1]['cn'][0]] = group[1]

        return groups

    def get_group_users(self, groups, group):
        """Returns all the users belonging to a single group.

        Based on the list of groups and memberships, returns all the
        users belonging to a single group, searching recursively.
        """
        users = []
        for member in groups[group]["uniqueMember"]:
            member = self.parse_member_string(member)
            if member[0] == "uid":
                users.append(member[1])
            elif member[0] == "cn":
                users += self.get_group_users(groups, member[1])

        return users

    def parse_member_string(self, member):
        """Parses the member string and returns a touple of type and name.

        Unique member can be either user or group. Users will have 'uid' as
        prefix while groups will have 'cn'.
        """
        member = member.split(",")[0]
        return member.split('=')


class LdapSync(object):

    def __init__(self):
        self.ldap_client = LdapClient(config.get("default", "ldap_uri"),
                                      config.get("default", "ldap_user"),
                                      config.get("default", "ldap_key"),
                                      config.get("default", "base_dn"))
        self.rhodocode_api = RhodecodeAPI(config.get("default", "api_url"),
                                          config.get("default", "api_key"))

    def update_groups_from_ldap(self):
        """Add all the groups from LDAP to Rhodecode."""
        added = existing = 0
        groups = self.ldap_client.get_groups()
        for group in groups:
            try:
                self.rhodecode_api.create_group(group)
                added += 1
            except Exception:
                existing += 1

        return added, existing

    def update_memberships_from_ldap(self, group):
        """Update memberships in rhodecode based on the LDAP groups."""
        groups = self.ldap_client.get_groups()
        group_users = self.ldap_client.get_group_users(groups, group)

        # Delete memberships first from each group which are not part
        # of the group any more.
        rhodecode_members = self.rhodecode_api.get_group_members(group)
        for rhodecode_member in rhodecode_members:
            if rhodecode_member not in group_users:
                try:
                    self.rhodocode_api.remove_membership(group,
                                                         rhodecode_member)
                except UserNotInGroupError:
                    pass

        # Add memberships.
        for member in group_users:
            try:
                self.rhodecode_api.add_membership(group, member)
            except UserAlreadyInGroupError:
                # TODO: handle somehow maybe..
                pass


if __name__ == '__main__':
    sync = LdapSync()
    print sync.update_groups_from_ldap()

    for gr in sync.ldap_client.get_groups():
        # TODO: exception when user does not exist during add membership...
        # How should we handle this.. Either sync users as well at this step,
        # or just ignore those who don't exist. If we want the second case,
        # we need to find a way to recognize the right exception (we always get
        # RhodecodeResponseError with no error code so maybe by return msg (?)
        sync.update_memberships_from_ldap(gr)

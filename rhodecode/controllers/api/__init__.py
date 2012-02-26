# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.api
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    JSON RPC controller

    :created_on: Aug 20, 2011
    :author: marcink
    :copyright: (C) 2011-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

import inspect
import logging
import types
import urllib
import traceback

from rhodecode.lib.compat import izip_longest, json

from paste.response import replace_header

from pylons.controllers import WSGIController


from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError, \
HTTPBadRequest, HTTPError

from rhodecode.model.db import User
from rhodecode.lib.auth import AuthUser

log = logging.getLogger('JSONRPC')


class JSONRPCError(BaseException):

    def __init__(self, message):
        self.message = message
        super(JSONRPCError, self).__init__()

    def __str__(self):
        return str(self.message)


def jsonrpc_error(message, code=None):
    """
    Generate a Response object with a JSON-RPC error body
    """
    from pylons.controllers.util import Response
    resp = Response(body=json.dumps(dict(id=None, result=None, error=message)),
                    status=code,
                    content_type='application/json')
    return resp


class JSONRPCController(WSGIController):
    """
     A WSGI-speaking JSON-RPC controller class

     See the specification:
     <http://json-rpc.org/wiki/specification>`.

     Valid controller return values should be json-serializable objects.

     Sub-classes should catch their exceptions and raise JSONRPCError
     if they want to pass meaningful errors to the client.

     """

    def _get_method_args(self):
        """
        Return `self._rpc_args` to dispatched controller method
        chosen by __call__
        """
        return self._rpc_args

    def __call__(self, environ, start_response):
        """
        Parse the request body as JSON, look up the method on the
        controller and if it exists, dispatch to it.
        """
        if 'CONTENT_LENGTH' not in environ:
            log.debug("No Content-Length")
            return jsonrpc_error(message="No Content-Length in request")
        else:
            length = environ['CONTENT_LENGTH'] or 0
            length = int(environ['CONTENT_LENGTH'])
            log.debug('Content-Length: %s' % length)

        if length == 0:
            log.debug("Content-Length is 0")
            return jsonrpc_error(message="Content-Length is 0")

        raw_body = environ['wsgi.input'].read(length)

        try:
            json_body = json.loads(urllib.unquote_plus(raw_body))
        except ValueError, e:
            # catch JSON errors Here
            return jsonrpc_error(message="JSON parse error ERR:%s RAW:%r" \
                                 % (e, urllib.unquote_plus(raw_body)))

        # check AUTH based on API KEY
        try:
            self._req_api_key = json_body['api_key']
            self._req_id = json_body['id']
            self._req_method = json_body['method']
            self._request_params = json_body['args']
            log.debug(
                'method: %s, params: %s' % (self._req_method,
                                            self._request_params)
            )
        except KeyError, e:
            return jsonrpc_error(message='Incorrect JSON query missing %s' % e)

        # check if we can find this session using api_key
        try:
            u = User.get_by_api_key(self._req_api_key)
            if u is None:
                return jsonrpc_error(message='Invalid API KEY')
            auth_u = AuthUser(u.user_id, self._req_api_key)
        except Exception, e:
            return jsonrpc_error(message='Invalid API KEY')

        self._error = None
        try:
            self._func = self._find_method()
        except AttributeError, e:
            return jsonrpc_error(message=str(e))

        # now that we have a method, add self._req_params to
        # self.kargs and dispatch control to WGIController
        argspec = inspect.getargspec(self._func)
        arglist = argspec[0][1:]
        defaults = map(type, argspec[3] or [])
        default_empty = types.NotImplementedType

        # kw arguments required by this method
        func_kwargs = dict(izip_longest(reversed(arglist), reversed(defaults),
                                        fillvalue=default_empty))

        # this is little trick to inject logged in user for
        # perms decorators to work they expect the controller class to have
        # rhodecode_user attribute set
        self.rhodecode_user = auth_u

        # This attribute will need to be first param of a method that uses
        # api_key, which is translated to instance of user at that name
        USER_SESSION_ATTR = 'apiuser'

        if USER_SESSION_ATTR not in arglist:
            return jsonrpc_error(message='This method [%s] does not support '
                                 'authentication (missing %s param)' %
                                 (self._func.__name__, USER_SESSION_ATTR))

        # get our arglist and check if we provided them as args
        for arg, default in func_kwargs.iteritems():
            if arg == USER_SESSION_ATTR:
                # USER_SESSION_ATTR is something translated from api key and
                # this is checked before so we don't need validate it
                continue

            # skip the required param check if it's default value is
            # NotImplementedType (default_empty)
            if (default == default_empty and arg not in self._request_params):
                return jsonrpc_error(
                    message=(
                        'Missing non optional `%s` arg in JSON DATA' % arg
                    )
                )

        self._rpc_args = {USER_SESSION_ATTR: u}
        self._rpc_args.update(self._request_params)

        self._rpc_args['action'] = self._req_method
        self._rpc_args['environ'] = environ
        self._rpc_args['start_response'] = start_response

        status = []
        headers = []
        exc_info = []

        def change_content(new_status, new_headers, new_exc_info=None):
            status.append(new_status)
            headers.extend(new_headers)
            exc_info.append(new_exc_info)

        output = WSGIController.__call__(self, environ, change_content)
        output = list(output)
        headers.append(('Content-Length', str(len(output[0]))))
        replace_header(headers, 'Content-Type', 'application/json')
        start_response(status[0], headers, exc_info[0])

        return output

    def _dispatch_call(self):
        """
        Implement dispatch interface specified by WSGIController
        """
        try:
            raw_response = self._inspect_call(self._func)
            if isinstance(raw_response, HTTPError):
                self._error = str(raw_response)
        except JSONRPCError, e:
            self._error = str(e)
        except Exception, e:
            log.error('Encountered unhandled exception: %s' \
                      % traceback.format_exc())
            json_exc = JSONRPCError('Internal server error')
            self._error = str(json_exc)

        if self._error is not None:
            raw_response = None

        response = dict(id=self._req_id, result=raw_response,
                        error=self._error)

        try:
            return json.dumps(response)
        except TypeError, e:
            log.debug('Error encoding response: %s' % e)
            return json.dumps(
                dict(
                    self._req_id,
                    result=None,
                    error="Error encoding response"
                )
            )

    def _find_method(self):
        """
        Return method named by `self._req_method` in controller if able
        """
        log.debug('Trying to find JSON-RPC method: %s' % self._req_method)
        if self._req_method.startswith('_'):
            raise AttributeError("Method not allowed")

        try:
            func = getattr(self, self._req_method, None)
        except UnicodeEncodeError:
            raise AttributeError("Problem decoding unicode in requested "
                                 "method name.")

        if isinstance(func, types.MethodType):
            return func
        else:
            raise AttributeError("No such method: %s" % self._req_method)

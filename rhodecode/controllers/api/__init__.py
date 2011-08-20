# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.api
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    JSON RPC controller
    
    :created_on: Aug 20, 2011
    :author: marcink
    :copyright: (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>    
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
import json
import logging
import types
import urllib

from paste.response import replace_header

from pylons.controllers import WSGIController
from pylons.controllers.util import Response

from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError, \
HTTPBadRequest, HTTPError

from rhodecode.model.user import User
from rhodecode.lib.auth import AuthUser

log = logging.getLogger('JSONRPC')

class JSONRPCError(BaseException):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return str(self.message)


def jsonrpc_error(message, code=None):
    """Generate a Response object with a JSON-RPC error body"""
    return Response(body=json.dumps(dict(result=None,
                                         error=message)))


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
            return jsonrpc_error(0, "No Content-Length")
        else:
            length = environ['CONTENT_LENGTH'] or 0
            length = int(environ['CONTENT_LENGTH'])
            log.debug('Content-Length: %s', length)

        if length == 0:
            log.debug("Content-Length is 0")
            return jsonrpc_error(0, "Content-Length is 0")

        raw_body = environ['wsgi.input'].read(length)

        try:
            json_body = json.loads(urllib.unquote_plus(raw_body))
        except ValueError as e:
            #catch JSON errors Here
            return jsonrpc_error("JSON parse error ERR:%s RAW:%r" \
                                 % (e, urllib.unquote_plus(raw_body)))


        #check AUTH based on API KEY

        try:
            self._req_api_key = json_body['api_key']
            self._req_method = json_body['method']
            self._req_params = json_body['args']
            log.debug('method: %s, params: %s',
                      self._req_method,
                      self._req_params)
        except KeyError as e:
            return jsonrpc_error(message='Incorrect JSON query missing %s' % e)

        #check if we can find this session using api_key
        try:
            u = User.get_by_api_key(self._req_api_key)
            auth_u = AuthUser(u.user_id, self._req_api_key)
        except Exception as e:
            return jsonrpc_error(message='Invalid API KEY')

        self._error = None
        try:
            self._func = self._find_method()
        except AttributeError, e:
            return jsonrpc_error(str(e))

        # now that we have a method, add self._req_params to
        # self.kargs and dispatch control to WGIController
        arglist = inspect.getargspec(self._func)[0][1:]

        # this is little trick to inject logged in user for 
        # perms decorators to work they expect the controller class to have
        # rhodecode_user set
        self.rhodecode_user = auth_u

        if 'user' not in arglist:
            return jsonrpc_error('This method [%s] does not support '
                                 'authentication (missing user param)' %
                                 self._func.__name__)

        # get our arglist and check if we provided them as args
        for arg in arglist:
            if arg == 'user':
                # user is something translated from api key and this is
                # checked before
                continue

            if not self._req_params or arg not in self._req_params:
                return jsonrpc_error('Missing %s arg in JSON DATA' % arg)

        self._rpc_args = dict(user=u)
        self._rpc_args.update(self._req_params)

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
            print raw_response
            if isinstance(raw_response, HTTPError):
                self._error = str(raw_response)
        except JSONRPCError as e:
            self._error = str(e)
        except Exception as e:
            log.debug('Encountered unhandled exception: %s', repr(e))
            json_exc = JSONRPCError('Internal server error')
            self._error = str(json_exc)

        if self._error is not None:
            raw_response = None

        response = dict(result=raw_response, error=self._error)

        try:
            return json.dumps(response)
        except TypeError, e:
            log.debug('Error encoding response: %s', e)
            return json.dumps(dict(result=None,
                                   error="Error encoding response"))

    def _find_method(self):
        """
        Return method named by `self._req_method` in controller if able
        """
        log.debug('Trying to find JSON-RPC method: %s', self._req_method)
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

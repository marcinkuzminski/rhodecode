import os
import socket
import logging
import subprocess
import traceback

from webob import Request, Response, exc

import rhodecode
from rhodecode.lib.vcs import subprocessio

log = logging.getLogger(__name__)


class FileWrapper(object):

    def __init__(self, fd, content_length):
        self.fd = fd
        self.content_length = content_length
        self.remain = content_length

    def read(self, size):
        if size <= self.remain:
            try:
                data = self.fd.read(size)
            except socket.error:
                raise IOError(self)
            self.remain -= size
        elif self.remain:
            data = self.fd.read(self.remain)
            self.remain = 0
        else:
            data = None
        return data

    def __repr__(self):
        return '<FileWrapper %s len: %s, read: %s>' % (
            self.fd, self.content_length, self.content_length - self.remain
        )


class GitRepository(object):
    git_folder_signature = set(['config', 'head', 'info', 'objects', 'refs'])
    commands = ['git-upload-pack', 'git-receive-pack']

    def __init__(self, repo_name, content_path, extras):
        files = set([f.lower() for f in os.listdir(content_path)])
        if  not (self.git_folder_signature.intersection(files)
                == self.git_folder_signature):
            raise OSError('%s missing git signature' % content_path)
        self.content_path = content_path
        self.valid_accepts = ['application/x-%s-result' %
                              c for c in self.commands]
        self.repo_name = repo_name
        self.extras = extras

    def _get_fixedpath(self, path):
        """
        Small fix for repo_path

        :param path:
        """
        return path.split(self.repo_name, 1)[-1].strip('/')

    def inforefs(self, request, environ):
        """
        WSGI Response producer for HTTP GET Git Smart
        HTTP /info/refs request.
        """

        git_command = request.GET.get('service')
        if git_command not in self.commands:
            log.debug('command %s not allowed' % git_command)
            return exc.HTTPMethodNotAllowed()

        # note to self:
        # please, resist the urge to add '\n' to git capture and increment
        # line count by 1.
        # The code in Git client not only does NOT need '\n', but actually
        # blows up if you sprinkle "flush" (0000) as "0001\n".
        # It reads binary, per number of bytes specified.
        # if you do add '\n' as part of data, count it.
        server_advert = '# service=%s' % git_command
        packet_len = str(hex(len(server_advert) + 4)[2:].rjust(4, '0')).lower()
        _git_path = rhodecode.CONFIG.get('git_path', 'git')
        try:
            out = subprocessio.SubprocessIOChunker(
                r'%s %s --stateless-rpc --advertise-refs "%s"' % (
                            _git_path, git_command[4:], self.content_path),
                starting_values=[
                    packet_len + server_advert + '0000'
                ]
            )
        except EnvironmentError, e:
            log.error(traceback.format_exc())
            raise exc.HTTPExpectationFailed()
        resp = Response()
        resp.content_type = 'application/x-%s-advertisement' % str(git_command)
        resp.charset = None
        resp.app_iter = out
        return resp

    def backend(self, request, environ):
        """
        WSGI Response producer for HTTP POST Git Smart HTTP requests.
        Reads commands and data from HTTP POST's body.
        returns an iterator obj with contents of git command's
        response to stdout
        """
        git_command = self._get_fixedpath(request.path_info)
        if git_command not in self.commands:
            log.debug('command %s not allowed' % git_command)
            return exc.HTTPMethodNotAllowed()

        if 'CONTENT_LENGTH' in environ:
            inputstream = FileWrapper(environ['wsgi.input'],
                                      request.content_length)
        else:
            inputstream = environ['wsgi.input']

        try:
            gitenv = os.environ
            # forget all configs
            gitenv['GIT_CONFIG_NOGLOBAL'] = '1'
            opts = dict(
                env=gitenv,
                cwd=os.getcwd()
            )
            cmd = r'git %s --stateless-rpc "%s"' % (git_command[4:],
                                                    self.content_path),
            log.debug('handling cmd %s' % cmd)
            out = subprocessio.SubprocessIOChunker(
                cmd,
                inputstream=inputstream,
                **opts
            )
        except EnvironmentError, e:
            log.error(traceback.format_exc())
            raise exc.HTTPExpectationFailed()

        if git_command in [u'git-receive-pack']:
            # updating refs manually after each push.
            # Needed for pre-1.7.0.4 git clients using regular HTTP mode.
            _git_path = rhodecode.CONFIG.get('git_path', 'git')
            cmd = (u'%s --git-dir "%s" '
                    'update-server-info' % (_git_path, self.content_path))
            log.debug('handling cmd %s' % cmd)
            subprocess.call(cmd, shell=True)

        resp = Response()
        resp.content_type = 'application/x-%s-result' % git_command.encode('utf8')
        resp.charset = None
        resp.app_iter = out
        return resp

    def __call__(self, environ, start_response):
        request = Request(environ)
        _path = self._get_fixedpath(request.path_info)
        if _path.startswith('info/refs'):
            app = self.inforefs
        elif [a for a in self.valid_accepts if a in request.accept]:
            app = self.backend
        try:
            resp = app(request, environ)
        except exc.HTTPException, e:
            resp = e
            log.error(traceback.format_exc())
        except Exception, e:
            log.error(traceback.format_exc())
            resp = exc.HTTPInternalServerError()
        return resp(environ, start_response)


class GitDirectory(object):

    def __init__(self, repo_root, repo_name, extras):
        repo_location = os.path.join(repo_root, repo_name)
        if not os.path.isdir(repo_location):
            raise OSError(repo_location)

        self.content_path = repo_location
        self.repo_name = repo_name
        self.repo_location = repo_location
        self.extras = extras

    def __call__(self, environ, start_response):
        content_path = self.content_path
        try:
            app = GitRepository(self.repo_name, content_path, self.extras)
        except (AssertionError, OSError):
            content_path = os.path.join(content_path, '.git')
            if os.path.isdir(content_path):
                app = GitRepository(self.repo_name, content_path, self.extras)
            else:
                return exc.HTTPNotFound()(environ, start_response)
        return app(environ, start_response)


def make_wsgi_app(repo_name, repo_root, extras):
    return GitDirectory(repo_root, repo_name, extras)

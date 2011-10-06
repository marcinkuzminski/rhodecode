from __future__ import with_statement

import cProfile
import pstats
import cgi
import pprint
import threading

from StringIO import StringIO


class ProfilingMiddleware(object):
    def __init__(self, app):
        self.lock = threading.Lock()
        self.app = app

    def __call__(self, environ, start_response):
        with self.lock:
            profiler = cProfile.Profile()

            def run_app(*a, **kw):
                self.response = self.app(environ, start_response)

            profiler.runcall(run_app, environ, start_response)

            profiler.snapshot_stats()

            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')

            # Redirect output
            out = StringIO()
            stats.stream = out

            stats.print_stats()

            resp = ''.join(self.response)

            # Lets at least only put this on html-like responses.
            if resp.strip().startswith('<'):
                ## The profiling info is just appended to the response.
                ##  Browsers don't mind this.
                resp += ('<pre style="text-align:left; '
                         'border-top: 4px dashed red; padding: 1em;">')
                resp += cgi.escape(out.getvalue(), True)

                output = StringIO()
                pprint.pprint(environ, output, depth=3)

                resp += cgi.escape(output.getvalue(), True)
                resp += '</pre>'

            return resp

import logging
from logging import Formatter, StreamHandler
from wsgiref.simple_server import make_server
from mercurial.hgweb.hgwebdir_mod import hgwebdir
from mercurial.hgweb.request import wsgiapplication

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = Formatter("%(asctime)s - %(levelname)s %(message)s")
console_handler = StreamHandler()
console_handler.setFormatter(formatter)
log.addHandler(console_handler)

def make_web_app():

    repos = "hgwebdir.config"
    hgwebapp = hgwebdir(repos)
    return hgwebapp

port = 8000
ip = '127.0.0.1'

log.info('Starting server on %s:%s' % (ip, port))
httpd = make_server(ip, port, wsgiapplication(make_web_app))
httpd.serve_forever()


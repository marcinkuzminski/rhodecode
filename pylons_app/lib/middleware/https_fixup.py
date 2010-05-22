class HttpsFixup(object):
    def __init__(self, app):
        self.application = app
    
    def __call__(self, environ, start_response):
        self.__fixup(environ)
        return self.application(environ, start_response)
    
    
    def __fixup(self, environ):
        """Function to fixup the environ as needed. In order to use this
        middleware you should set this header inside your 
        proxy ie. nginx, apache etc.
        """
        proto = environ.get('HTTP_X_URL_SCHEME')
            
        if proto == 'https':
            environ['wsgi.url_scheme'] = proto
        else:
            environ['wsgi.url_scheme'] = 'http'
        return None

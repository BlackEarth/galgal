
import functools
from importlib import import_module
import tornado.web
from bl.dict import Dict, StringDict
from bl.url import URL

import .session

class Handler(tornado.web.RequestHandler, Dict):

    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self.url = URL(self.request.full_url(), host=self.settings.host, scheme=self.settings.scheme)
        self.HTTPError = tornado.web.HTTPError

    def arguments(self):
        return StringDict(**self.request.arguments)

    def render(self, *args, **kwargs):
        if 'c' not in kwargs:
            kwargs['c'] = self
        super().render(self, *args, **kwargs)

    def write_error(self, status_code, **kwargs):
        self.set_status(status_code)
        self.render("http_error.html")

    # == Session management == 

    def init_session(self, new=False, reload=False, expires_days=None, **args):
        """initialize session"""
        if new==True or reload==True or 'session' not in self.__dict__.keys() or self.session is None:
            self.session_storage_class = eval(
                'amp.session.'+self.config.Site.session_storage   # use the config session_storage class
                or 'SessionStorage'                                     # default to in-memory session storage
            )
            if self.session_storage_class==amp.session.FileStorage:
                session_storage = amp.session.FileStorage(directory=self.config.Site.session_path)
            else:
                session_storage = amp.session.SessionStorage()
            if new==True: 
                session_id = None
            else: 
                session_id = self.get_secure_cookie('session_id')   # None if no session was in process
            self.session = session_storage.init_session(session_id)
            self.set_secure_cookie('session_id', self.session.id, expires_days=expires_days)
        self.session.update(**args)
        
    def clear_session(self):
        """remove the session_id cookie and init a new session."""
        self.clear_cookie('session_id')
        self.init_session(new=True)

    def save_session(self):
        if 'session' in self.__dict__.keys() and self.session is not None:
            self.session.save()

    # decorator
    def require_admin(method):
        """Decorate methods with this to require that the user be logged in with the given role.
        If the user is not logged in, they will be redirected to the configured
        `login url <RequestHandler.get_login_url>`.
        If the user is logged in and doesn't have the given role, an HTTP_UNAUTHORIZED error is raised
        """
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if self.session.user is None:
                if self.request.method in ("GET", "HEAD"):
                    url = URL(self.config.Site.url+self.request.path, host=self.request.host, scheme=self.request.protocol)
                    if self.debug==True: print(url)
                    # *TODO*: store the 'next' url in the session
                    self.redirect(self.get_login_url()+"?ret="+str(url))
                    return
                else:
                    raise tornado.web.HTTPError(403)
            elif self.session.user.role != 'admin':
                # *TODO*: check to see if the user has the given role
                raise self.HTTPError(401)
            return method(self, *args, **kwargs)
        return wrapper

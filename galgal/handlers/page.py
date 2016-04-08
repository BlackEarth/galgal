
import os
import tornado.web

from .handler import Handler

class PageHandler(Handler):
    # for now, require all users to be logged in.
    def prepare(self):
        if self.session.user is None:
            self.session.notice = "Please login before continuing."
            self.redirect('/acct/login')#?ret='+ str(self.url))
        self.db.init_session()

    def get(self, url):
        template = os.path.splitext(url)[0].lstrip('/') + '.html'
        if self.debug==True: print('trying:', template)
        template_fn = os.path.join(self.config.Tornado.template_path, template)
        if os.path.exists(template_fn):
            self.render(template)
        else:
            index = (os.path.splitext(url)[0] + '/index.html').lstrip('/')
            if self.debug==True: print('trying:', index)
            index_fn = os.path.join(self.config.Tornado.template_path, index)
            if os.path.exists(index_fn):
                self.render(index)
            else:
                raise tornado.web.HTTPError(404)

# amp.tornado - adaptor for running an app with the tornado web server
# -- tornado is the best way to create an asyncronous, real-time app in python.

import tornado.ioloop
import tornado.web
from bl.dict import Dict

class TornadoApp(Dict):
    def __init__(self, config=None, routes=None, log=None):
        self.config = config
        self.routes = routes
        self.log = log
        self.app = tornado.web.Application(
                self.routes, config=self.config, log=log, **self.config.Tornado
            )

    def __call__(self, port=None):
        self.application.listen(port or self.config.Site.port or 80)
        tornado.ioloop.IOLoop.instance().start()


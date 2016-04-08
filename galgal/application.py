# web server application
# -- tornado is the best way to create an asyncronous, real-time app in python.

import tornado.ioloop, tornado.web
from bl.dict import Dict
from bl.log import Log

class Application(tornado.web.Application, Dict):
    def __init__(self, routes=None, default_host='', transforms=None, log=Log(), **settings):
        tornado.web.Application.__init__(self, routes, default_host=default_host, transforms=transforms)
        self.log = log
        self.settings = Dict(**settings)

    def __call__(self, port=None):
        self.listen(port or (self.settings.Site or Dict()).port or 80)
        self.log(self.settings.json(indent=2))
        tornado.ioloop.IOLoop.instance().start()


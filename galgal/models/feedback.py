
from . import Model

import html

class Feedback(Model):
    relation = 'feedback'
    pk_fields = ['id']

    def insert(self, **args):
        self.body = html.escape(self.body)
        self.subject = html.escape(self.subject)
        Model.insert(self, **args)

    def update(self, **args):
        self.body = html.escape(self.body)
        self.subject = html.escape(self.subject)
        Model.update(self, **args)
    


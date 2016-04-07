from . import Model

class Tag(Model):
    relation = 'tags'
    pk_fields = ['name']

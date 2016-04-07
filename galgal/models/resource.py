
from . import Model

class Resource(Model):
    relation = 'resources'
    pk_fields = ['uri']

    def item(self, update=False):
        """resource belongs_to item"""
        from .item import Item
        if update==True or self._item is None:
            self._item = Item(self.db).select_one(where="id='%(item_id)s'" % self)
        return self._item

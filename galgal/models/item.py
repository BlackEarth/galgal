
from . import Model

class Item(Model):
    relation = 'items'
    pk_fields = ['id']

    def __init__(self, db, **args):
        Model.__init__(self, db, **args)
        self.typename = self.__class__.__name__     # the typename is whatever class name the instance was created with.

    def groups(self, update=False):
        """many-to-many relationship through groups_items"""
        from .group import Group
        if self._groups is None or update==True:
            self._groups = Group(self.db).select(where="id in (select group_id from groups_items where item_id='%(id)s')" % self)
        return self._groups

    def users(self, update=False):
        """many-to-many relationship through members_items"""
        from .user import User
        if self._users is None or update==True:
            self._users = User(self.db).select(where="email in (select email from users_items where item_id='%(id)s')" % self)
        return self._users

    def item_kind(self, update=False):
        """has-one item_kind"""
        if self._item_kind is None or update==True:
            self._item_kind = ItemType(self.db).select_one(where="id='%(typename)s'" % self)
        return self._item_kind

    def resources(self, update=False):
        """has-many resources"""
        from .resource import Resource
        if self._resources is None or update==True:
            self._resources = Resource(self.db).select(where="item_id='%(id)s'" % self)
        return self._resources


class ItemType(Model):
    """helper class for items"""
    relation = 'item_kinds'
    pk_fields = ['id']

    def items(self, update=False):
        """has-many items"""
        if self._items is None or update==True:
            self._items = Item(self.db).select(where="typename='%(name)s'" % self)
        return self._items

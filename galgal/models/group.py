
from . import Model


class Group(Model):
    relation = 'groups'
    pk_fields = ['id']

    def members(self, update=False):
        """many-to-many relationship with members through groups_memberships"""
        from .user import User
        if self._members is None or update==True:
            self._members = User(self.db).select(where="email in (select email from groups_memberships where group_id='%(name)s')" % self)
        return self._members

    def items(self, update=False):
        """many-to-many relationship with items through groups_items"""
        from .item import Item
        if self._items is None or update==True:
            self._items = Item(self.db).select(where="id in (select item_id from groups_items where group_id='%(name)s')" % self)
        return self._items


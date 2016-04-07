
from . import Model

class Relationship(Model):
    relation = 'relationships'
    pk_fields = ['user1', 'user2', 'kind']

    def users(self, update=False):
        from .user import User
        if update==True or self._users is None:
            self._users = User(self.db).select(where="email='%(user1)s' or email='%(user2)s'" % self)
        return self._users

class RelationshipKind(Model):
    relation = 'relationship_kinds'
    pk_fields = ['id']

    def relationships(self, update=False):
        """has-many relationships"""
        if update==True or self._relationships is None:
            self._relationships = Relationship(self.db).select(where="kind='%(id)s'" % self)
        return self._relationships

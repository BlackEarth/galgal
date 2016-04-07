
from . import Model

class Role(Model):
    relation = 'roles'
    pk_fields = ['id']

    def rights(self, update=False):
        """many-to-many relationship through rights_roles"""
        from .right import Right
        if update==True or self._rights is None:
            self._rights = Right(self.db).select(where="id in (select right_id from rights_roles where role_id='%(id)s')" % self)
        return self._rights

    def users(self, update=False):
        """has-many users"""
        from .user import User
        if update==True or self._users is None:
            self._users = User(self.db).select(where="role_id='%(id)s'" % self)
        return self._users

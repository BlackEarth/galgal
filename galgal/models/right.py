
from . import Model

class Right(Model):
    relation = 'rights'
    pk_fields = ['id']

    def roles(self, update=False):
        """many-to-many relationship through rights_roles"""
        from .role import Role
        if update==True or self._roles is None:
            self._roles = Role(self.db).select(where="id in (select role_id from rights_roles where right_id='%(id)s')" % self)
        return self._roles

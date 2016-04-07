# bl.session -- session handling for web apps
# by Sean A. Harrison <sah@blackearth.us>
# ---------------------------------------------------------------------------
# $Id: session.py 13 2014-05-17 22:42:48Z sah $

"""== Session and MemoryStorage classes == 
MemoryStorage   : Base class, stores sessions in a dict in memory. VERY fast, but non-persistent.
FileStorage     : Stores sessions in a filesystem directory. Fast, persistent. Needs periodic cleanup.
DatabaseStorage : Stores sessions in a table in database. Fast, persistent. Needs periodic cleanup.
CookieStorage   : Stores sessions in the client's cookie, uses symmetric encryption. A bit slow.
MemcacheStorage : Stores sessions in memcached. Very fast. Needs periodic cleanup.
---------------------------------------------------------------------------
Memory Usage:                                   Footprint:
> python                          # 1832 K
>>> from bl import session        # 2292 K      460 K

---------------------------------------------------------------------------
"""

DEBUG = False

from random import random
from time import time, asctime
from base64 import urlsafe_b64encode, urlsafe_b64decode
from bl.dict import Dict

# ---------------------------------------------------------------------------

class Session(dict):
    """session is a dict, session.id is the id used in session storage
        Session(storage, **args) : returns a new session that will use the storage instance
        session[key]             : return the value of key in session
        session.id               : the unique id of the session
        session.save()           : save the session in storage
        Session.load(storage, id) : load the indicated session from storage.
                                    if it doesn't exist in storage, returns a new session
    Example:
    >>> storage = MemoryStorage()              # new container for sessions
    >>> s = Session.load(storage)               # new session
    >>> s['name'] = 'amp'                       # set a value
    >>> s.save()                                # save the session in storage
    >>> s1 = Session.load(storage, s.id)        # lookup the session by its id; use this with cookies.
    >>> s1.id == s.id and s1['name'] == 'amp'
    True
    >>> storage.delete(s.id)                    # delete an existing session from storage
    >>> s2 = Session.load(storage, s.id)        # now s doesn't exist in storage, so s2 is a new session.
    >>> s2.id != s.id and s2.id != None and s2 == {}
    True
    """

    def __init__(self, storage, **args):
        self.id = self.new_key()
        self.storage = storage
        self.update(**args)

    def new_key(self):
        """create a new session key"""
        # keep it simple but still pretty secure and guaranteed unique
        key = bytes("%s%.17f%.17f" % (time(), random(), random()), encoding='ascii')
        return urlsafe_b64encode(key).decode().strip('=')[12:]

    @classmethod
    def init_storage(cls, storage, **params):
        "load and return the storage object that is indicated by the name and params"
        if storage == 'MemoryStorage':              # no params needed
            session_storage = MemoryStorage()
        elif storage == 'DatabaseStorage':          # params init the database
            from .database_storage import DatabaseStorage
            session_storage = DatabaseStorage(**params)
        elif storage == 'MemcacheStorage':
            from .memcache_storage import MemcacheStorage
            session_storage = MemcacheStorage(**params)
        elif storage == 'CookieStorage':
            from .cookie_storage import CookieStorage
            session_storage = CookieStorage(**params)
        elif storage == 'FileStorage':
            from .file_storage import FileStorage
            session_storage = FileStorage(**params)
        return session_storage

    @classmethod
    def load(cls, storage, id=None, **args):
        """load the session from storage by id. If a wrong id or None is given, return a new session."""
        if id:
            try:
                return storage.load(id)
            except KeyError:
                return Session(storage)
        else:
            return Session(storage)

    def save(self, **args):
        self.storage.save(self, **args)
        self.saved_at = asctime()
        if DEBUG==True: print("session saved:", self.id, self)
        
    def delete(self):
        self.storage.delete(self.id)

    def decode_bytes(self, encoding='UTF-8'):
        return Dict(**self).decode_bytes(encoding=encoding)

# ---------------------------------------------------------------------------

class MemoryStorage(dict):
    """A storage container for sessions. This base class implements memory storage.
    Example:
    >>> st = MemoryStorage()
    >>> s = Session(st, name='sah')
    >>> s.get('name')
    'sah'
    >>> s.save()
    >>> s1 = Session.load(st, s.id)
    >>> s1
    {'name': 'sah'}
    >>> s2 = Session.load(st, 'nonexistentid')
    >>> s2
    {}
    >>> s2.id == 'nonexistentid'
    False
    >>> st.delete(s.id)
    >>> s3 = Session.load(st, s.id)
    >>> s3 == {} and s3.id != s.id and s3.id != None
    True
    """

    def init_session(self, session_id=None, session_class=Session, **args):
        """returns a Session object initialized with self as MemoryStorage and **args as keys.
        If session_id is given and exists in storage, that session is returned.
        """
        s = Session.load(self, session_id)
        s.storage = self
        s.update(**args)
        return s

    # derived storage classes can override load() and save()
    def load(self, sessionid):
        """load the session associated with the given id from storage"""
        return self[sessionid]

    def save(self, session):
        """save the given session in storage"""
        self[session.id] = session

    def delete(self, sessionid):
        """delete the session associated with the given id from storage"""
        self.pop(sessionid, None)

# ---------------------------------------------------------------------------

def doctests():
    """ -- Additional doctests --
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()

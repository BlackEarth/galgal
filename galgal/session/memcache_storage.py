
DEBUG = False

import json
import memcache         # pip install python-memcached

from bl.session import Session, SessionStorage

class MemcacheStorage(SessionStorage):
    """Memcache storage of sessions.
        init with memcache server location (default 127.0.0.1:11211)

    Example Session
    >>> st = MemcacheStorage('127.0.0.1:11211')
    >>> s = Session(st, name='sah')
    >>> s
    {'name': 'sah'}
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

    def __init__(self, memcache_server='127.0.0.1:11211'):
        self.client = memcache.Client([memcache_server])

    def load(self, sessionid=None):
        session = Session(self)
        if sessionid:
            sdata = self.client.get(sessionid)
            if sdata:
                session.update(**json.loads(sdata))
                session.id = sessionid
        else:
            self.save(session)
        return session

    def save(self, session):
        self.client.set(session.id, json.dumps(session))
        self[session.id] = {'saved': session.saved_at}

    def delete(self, sessionid):
        self.client.delete(sessionid)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

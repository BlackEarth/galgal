
DEBUG = False

import os, json
from bl.dict import Dict

from bl.session import Session, SessionStorage
SESSIONS_PATH = os.path.join(os.path.dirname(__file__), 'cache', 'sessions')

class FileStorage(SessionStorage):
    """File-based storage for sessions.
        init with name of directory (which must exist) where sessions will be stored.
    Example: (pretty much the same as the example for SessionStorage)
    >>> st = FileStorage(SESSIONS_PATH)      # local path to sessions folder
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
    def __init__(self, directory=''):
        self.directory = os.path.abspath(directory)
        if not os.path.exists(self.directory): os.makedirs(self.directory)
        if not os.path.isdir(self.directory): raise ValueError("File '%s' exists but is not a directory" % directory)

    def load(self, sessionid=None):
        if os.path.exists(self.session_file(sessionid)):
            f = open(self.session_file(sessionid))
            try:
                sdata = Dict(**json.loads(f.read()))
            except:
                sdata = {}
            f.close
            s = Session(self)
            s.update(**sdata)
            s.id = sessionid
            return s
        else:
            return Session(self)

    def save(self, session):
        # make sure the directory for this session exists.
        if not os.path.exists(self.session_dir(session.id)):
            os.makedirs(self.session_dir(session.id))
        # write the file, overwriting what is there.
        f = open(self.session_file(session.id), 'w')
        f.write(json.dumps(session.decode_bytes()))
        f.close

    def delete(self, sessionid):
        if os.path.exists(self.session_file(sessionid)) \
        and not os.path.isdir(self.session_file(sessionid)):
            os.remove(self.session_file(sessionid))

    def session_dir(self, sessionid):
        """returns an absolute path to the session file."""
        # go 2 levels deep into self.directory, with 1000 x 1000 session folders,
        # making 1,000,000 session folders max.
        if type(sessionid)==bytes: sessionid=sessionid.decode('utf-8')
        return os.path.join(self.directory, sessionid[0:3], sessionid[3:6])

    def session_file(self, sessionid):
        if type(sessionid)==bytes: sessionid=sessionid.decode('utf-8')
        return os.path.join(self.session_dir(sessionid), sessionid)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

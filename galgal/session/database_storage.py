
import json
from bl.session import Session, MemoryStorage
from bl.database import Database
from bl.model import Model

class SessionModel(Model):
    relation = 'sessions'
    pk = ['id']

class DatabaseStorage(MemoryStorage):
    """Database storage of sessions.
        init with a DB-API 2.0 db connection.

    Example Session (uses an in-memory sqlite database for storage)
    >>> from bl.database import Database
    >>> db = Database()                             
    >>> db.execute('''create table sessions (id varchar primary key, data text)''')
    >>> st = DatabaseStorage(db)
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
    >>> db.execute("drop table sessions")
    """

    def __init__(self, db=None, session_model=SessionModel):
        if db is None:
            db = Database()
            db.execute("""create table sessions (id varchar primary key, data text)""")
        self.db = db
        self.SessionModel = session_model

    def load(self, session_id=None):
        record = self.SessionModel(self.db).select_one(id=session_id)
        if record is not None:
            sdata = json.loads(record.data)
            s = Session(self, **sdata)
            s.id = session_id
            return s
        else:
            return Session(self)

    def save(self, session):
        r = self.SessionModel(self.db).select_one(id=session.id) 
        if r is not None:
            r.data = json.dumps(session)
            r.commit()
        else:
            r = self.SessionModel(self.db, id=session.id, data=json.dumps(session))
            r.insert()

    def delete(self, session_id):
        r = self.SessionModel(self.db).select_one(id=session_id)
        if r is not None:
            r.delete()


if __name__ == "__main__":
    import doctest
    doctest.testmod()

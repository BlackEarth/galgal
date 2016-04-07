
DEBUG = False

import json
from random import random
from base64 import urlsafe_b64encode, urlsafe_b64decode
from Crypto.Cipher import AES       # pip install pycrypto

from bl.session import Session, SessionStorage

class CookieStorage(SessionStorage):
    """Cookie storage of sessions.
        init with an encryption key, and request and response objects.

    Example Session (simulating Request and Response objects)
    >>> st = CookieStorage('thiskeyisverybad,bettergetrandom')
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
    >>> st.delete(s.id)             # <-- This has no effect, there is no concept of deleting a cookie session.
    >>> s3 = Session.load(st, s.id)  # <-- The session data is actually in s.id, so the following tests are all false.
    >>> s3 == {} and s3.id != s.id and s3.id != None
    False
    """

    def __init__(self, key):
        self.key = key
        self.cipher = AES.new(self.key, keySize=len(key))

    def load(self, session_id=None):
        # with a cookie session, the session_id is actually the encrypted data for the session
        session = Session(self)
        if session_id:
            try:
                sdata = self.__decrypt(session_id)
            except:
                sdata = {}
            session.update(**sdata)
        session.id = self.__encrypt(session)
        return session

    def save(self, session):
        session.id = self.__encrypt(session)

    def delete(self, session_id, **args):
        pass

    def __encrypt(self, session):
        return urlsafe_b64encode(self.cipher.encrypt(json.dumps(session)))

    def __decrypt(self, session_id):
        return json.loads(self.cipher.decrypt(urlsafe_b64decode(session_id)))

    @classmethod
    def make_key(cls, keySize=32):
        base92 = " 0 1 2 3 4 5 6 7 8 9 a b c d e f g h i j k l m n o p q r s t u v w x y z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z ` ~ ! @ # $ % ^ & * ( ) _ + - = [ { ] } \ | ; : , < . > / ? ".split()
        t = []
        for i in range(keySize):
            t.append(base92[int(random()*92)])
        return "".join(t)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

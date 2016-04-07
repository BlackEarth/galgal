# routes.py -- request routing. 
# by Sean A. Harrison <sah@blackearth.us>
# ---------------------------------------------------------------------------

import re   # regular expressions
import sys  # for sys.version
from bl.dict import Dict

# patterns used in routing requests
Patterns = Dict(**{
    'int': r'[0-9]+',                           # int: integer
    'dec': r'[0-9\.,]+',                        # dec: decimal
    'slug': r'[\w\$\-\_\.\+\!\*\(\)\, %%@]+',   # slug: a part of a url between /
    'path': r'[\w\$\-\_\.\+\!\*\(\)\, %%@/]+',  # path: anything legal in a path
    'word': r'[\w\-]+',                         # word: starts with letter or _ or -, + word chars
    'name': r'[a-zA-Z_][a-zA-Z0-9_]+',          # name: starts with letter or _, then letter, number, or _
    'hex': r'[0-9a-f]+',                        # hex: hexidecimal number
    })

class RouteMap(list):
    """Provides a mapping structure for matching URLs to handling facilities.
    Designed for speed, simplicity, and low memory usage. And no side-effects.
    Memory comparison (using Python 2.7 on Windows):
        ----------------------------------------------------------------------
        Action:                                         Memory:     Footprint:
        -------------------------------------------------------------------  ---
        > python                                        1936 K
        then one of the following:
          from amp.wsgi.routes import *                 2020 K        84 K
          from routes import *                          2800 K       864 K
          from werkzeug.routing import *                4576 K      2640 K
          from django.conf.urls.defaults import *       4920 K      2984 K
        ----------------------------------------------------------------------
    Memory is too important to waste.

    A RouteMap is a list of dicts. If m is a RouteMap, m.match(url) will return
    a dict with key:value pairs indicating what routing keys to use for that url.
    For each route, the pattern is a regular expression, with additional routing
    key:value pairs to specify defaults. See example below. You can use whatever
    routing keys you want in your routes.

    That's it. No URL reversal is provided. What am I, your mother?
    Design your URLs carefully, and then don't change them once published.*
    If you do change them, you can edit your app -- grep is your friend.

    (* To mount your application at a different base url, put the server & path 
        in your site config. Then use this at the beginning of every url 
        in the application. The amp.wsgi.Application object will automatically 
        construct this as c.app.uri available to your application.)

    Here's an example session (using comparison for doctest happiness):
        >>> m = RouteMap([{'pattern': r"^/$", 'controller': 'webpages', 'action': 'view', 'name': 'home'}, \
                     {'pattern': r"^/(?P<controller>\w+)(\.(?P<fmt>\w+))?/?$", 'action': 'index'},    \
                     {'pattern': r"^/(?P<controller>\w+)/(?P<name>\w+)(\.(?P<fmt>\w+))?/?$", 'action': 'view'}, \
                     {'pattern': r"^/(?P<controller>\w+)/(?P<name>\w+)/(?P<action>\w+)/?$"},          \
                     {'pattern': r"^/.*$", 'script': 'errors/notfound.py'}])
        >>> m.match('') == None
        True
        >>> route = m.match('/')
        >>> route == {'controller': 'webpages', 'action': 'view', 'name': 'home'}
        True
        >>> route = m.match('/articles/')
        >>> route == {'controller': 'articles', 'action': 'index'}
        True
        >>> route = m.match('/articles.xml')
        >>> route == {'controller': 'articles', 'action': 'index', 'fmt': 'xml'}
        True
        >>> route = m.match('/articles/how_to_win')
        >>> route == {'controller': 'articles', 'action': 'view', 'name': 'how_to_win'}
        True
        >>> route = m.match('/articles/how_to_win.xml')
        >>> route == {'controller': 'articles', 'action': 'view', 'name': 'how_to_win', 'fmt': 'xml'}
        True
        >>> route = m.match('/articles/how_to_lose/del')
        >>> route == {'controller': 'articles', 'action': 'del', 'name': 'how_to_lose'}
        True
        >>> route = m.match('/someplace/else/that/I/dont/know/about')
        >>> route == {'script': 'errors/notfound.py'}
        True
    """

    def __init__(self, routes):
        """You can define a routemap (a list of dicts) on initialization."""
        for r in routes:
            self.append(Route(**r))

    def match(self, url):
        """Given a url, returns a dict indicating how to handle the request."""
        for rt in self:                # for each route,
            matchdata = rt.regexp.match(url) # see if it matches the url -- CASE-INSENSITIVE
            if matchdata:                       # if so, put routing info in a dict and return it
                d = Dict()                      # don't operate directly on the route! Bad side-effects would ensue (because Python uses call-by-reference).
                d.update(**rt)                  # include everything that is in the route
                d.pop('regexp')               # but don't include the compiled regexp
                d.pop('pattern')              # or the pattern, for that matter
                mdd = matchdata.groupdict()
                for k in mdd:                 # include named groups from match data
                    if mdd[k] is not None:    # except for None values
                        d[k] = mdd[k]
                return d

class Route(Dict):
    def __init__(self, pattern, patterns=None, **args):
        """Take a given pattern and return a Route object, which is used by RouteMap to create a route map.
        pattern: a url pattern, with named args in brackets: {var}
                name can take pattern indicator: {var:int}
                defaults to {var:slug}
        args: give default values for other variables
            controller: the name of the controller
            action: the name of the controller method to use
        Example:
        >>> m = RouteMap([Route("/{controller:slug}/"),
        ...             Route("/users/{username:slug}/", controller='users')])
        >>> m.match("/users/sean")
        {'controller': 'users', 'username': 'sean'}
        """
        if patterns is None: patterns = Patterns
        
        # put args into self
        for k in args.keys(): self[k] = args[k]
        
        # convert the pattern into a regexp.
        self.pattern = pattern
        self.pattern = re.sub(r"\{(%(name)s)\}" % patterns, r"{\1:slug}", self.pattern, flags=re.U + re.I)                  # default name:slug
        self.pattern = re.sub(r"\{(%(name)s):(%(name)s)\}" % patterns, r"(?P<\1>%(\2)s)", self.pattern, flags=re.U + re.I)  # convert
            
        if self.pattern[-1] == '/': self.pattern += "?"     # make trailing slash optional
        self.pattern = "^" + self.pattern + "$"             # the pattern is the whole URL
        self.pattern = self.pattern % patterns
        self.compile()

    def compile(self):
        self.regexp = re.compile(self.pattern, re.U)


# ---------------------------------------------------------------------------
# -- TESTS --
def test_Map():
    """ Build a map, then try matches.
    >>> m = RouteMap([{'pattern': '^/$'}])
    >>> m.match('') == None
    True
    >>> m.match('/') == {}
    True
    """

# To test this module, do "python routes.py" from the command line and see what you get. No output => success.
if __name__ == "__main__":
    import doctest
    doctest.testmod()

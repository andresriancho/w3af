# http://www.logilab.org/blogentry/78354

"""    
Fixes:
    E: 61,12: Module 'httpretty' has no 'enable' member (no-member)
    E: 63,12: Module 'httpretty' has no 'register_uri' member (no-member)
    E: 63,35: Module 'httpretty' has no 'GET' member (no-member)
    E: 72,12: Module 'httpretty' has no 'disable' member (no-member)
"""

from logilab.astng import MANAGER
from logilab.astng.builder import ASTNGBuilder

CODE_FIX = """
def enable(*args, **kwds): pass
def disable(*args, **kwds): pass
def register_uri(*args, **kwds): pass
def GET(*args, **kwds): pass
def POST(*args, **kwds): pass
"""

def httpretty_transform(module):
    if module.name == 'httpretty':
        fake = ASTNGBuilder(MANAGER).string_build(CODE_FIX)
        
        for hashfunc in ('enable', 'disable', 'register_uri', 'GET', 'POST'):
            module.locals[hashfunc] = fake.locals[hashfunc]

def register(linter):
    """called when loaded by pylint --load-plugins, register our tranformation
    function here
    """
    MANAGER.register_transformer(httpretty_transform)


# http://www.logilab.org/blogentry/78354

from logilab.astng import MANAGER
from logilab.astng.builder import ASTNGBuilder

CODE_FIX = """
class md5(object):
    def __init__(self, value): pass
    def hexdigest(self):
        return u''
    def update(self, x):
        return u''
    def digest(self):
        return u''

class sha1(object):
    def __init__(self, value): pass
    def hexdigest(self):
        return u''
    def update(self, x):
        return u''
    def digest(self):
        return u''

class sha512(object):
    def __init__(self, value): pass
    def hexdigest(self):
        return u''
    def update(self, x):
        return u''
    def digest(self):
        return u''
"""

def hashlib_transform(module):
    if module.name == 'hashlib':
        fake = ASTNGBuilder(MANAGER).string_build(CODE_FIX)
        
        for hashfunc in ('sha1', 'md5', 'sha512'):
            module.locals[hashfunc] = fake.locals[hashfunc]

def register(linter):
    """called when loaded by pylint --load-plugins, register our tranformation
    function here
    """
    MANAGER.register_transformer(hashlib_transform)
    
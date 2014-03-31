# http://www.logilab.org/blogentry/78354

from logilab.astng import MANAGER
from logilab.astng.builder import ASTNGBuilder

CODE_FIX = """
class Notify(object):
    def Notification(*args, **kwds): pass
    def init(*args, **kwds): pass
"""

def gi_repository_transform(module):
    if module.name == 'gi.repository':
        fake = ASTNGBuilder(MANAGER).string_build(CODE_FIX)
        
        for func in ('Notify',):
            module.locals[func] = fake.locals[func]

def register(linter):
    """called when loaded by pylint --load-plugins, register our tranformation
    function here
    """
    MANAGER.register_transformer(gi_repository_transform)
    
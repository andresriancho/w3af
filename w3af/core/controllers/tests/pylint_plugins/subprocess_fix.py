# http://www.logilab.org/blogentry/78354

from logilab.astng import MANAGER
from logilab.astng.builder import ASTNGBuilder

CODE_FIX = """
class Popen(object):
    stdout = StringIO.StringIO()
    stderr = StringIO.StringIO()
    returncode = 0
    def communicate(*args, **kwds): pass
    def pid(*args, **kwds): pass
    def poll(*args, **kwds): pass
    def kill(*args, **kwds): pass
    def wait(*args, **kwds): pass
    def send_signal(*args, **kwds): pass
    def terminate(*args, **kwds): pass
"""

def subprocess_transform(module):
    if module.name == 'subprocess':
        fake = ASTNGBuilder(MANAGER).string_build(CODE_FIX)
        
        for func in ('Popen',):
            module.locals[func] = fake.locals[func]

def register(linter):
    """called when loaded by pylint --load-plugins, register our tranformation
    function here
    """
    MANAGER.register_transformer(subprocess_transform)
    
# http://www.logilab.org/blogentry/78354

from logilab.astng import MANAGER
from logilab.astng.builder import ASTNGBuilder

CODE_FIX = '''
class Popen(object):
    stdout = StringIO.StringIO()
    def communicate(*args, **kwds): pass
'''

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
    
# http://www.logilab.org/blogentry/78354

from logilab.astng import MANAGER
from logilab.astng.builder import ASTNGBuilder

CODE_FIX = '''
class ClientError(object):
    args = ()
    
class wc_notify_action(object):
    update_add = u''
    update_delete = u''
    update_update = u''
    
class wc_status_kind(object):
    conflicted = u''
    normal = u''
    unversioned = u''
    modified = u''
    
class opt_revision_kind(object):
    head = u'head'
    number = 1

class Revision(object):
    number = 1

class depth(object):
    infinity = -1
'''

def pysvn_transform(module):
    if module.name == 'pysvn':
        fake = ASTNGBuilder(MANAGER).string_build(CODE_FIX)
        
        for func in ('ClientError', 'wc_notify_action', 'wc_status_kind',
                     'opt_revision_kind', 'Revision', 'depth'):
            module.locals[func] = fake.locals[func]

def register(linter):
    """called when loaded by pylint --load-plugins, register our tranformation
    function here
    """
    MANAGER.register_transformer(pysvn_transform)
    
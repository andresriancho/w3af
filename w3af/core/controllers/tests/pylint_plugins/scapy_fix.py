# http://www.logilab.org/blogentry/78354

from logilab.astng import MANAGER
from logilab.astng.builder import ASTNGBuilder

CODE_FIX = """
class IP(object): pass
class TCP(object): pass
class UDP(object): pass
class traceroute(object):
    def __init__(domain, dport=80):
        pass
"""

def scapy_transform(module):
    if module.name == 'scapy.all':
        fake = ASTNGBuilder(MANAGER).string_build(CODE_FIX)
        
        for func in ('IP', 'TCP', 'UDP', 'traceroute'):
            module.locals[func] = fake.locals[func]

def register(linter):
    """called when loaded by pylint --load-plugins, register our tranformation
    function here
    """
    MANAGER.register_transformer(scapy_transform)
    
from astroid import MANAGER, register_module_extender
from astroid.builder import AstroidBuilder

"""    
Fixes:
    E: 61,12: Module 'httpretty' has no 'enable' member (no-member)
    E: 63,12: Module 'httpretty' has no 'register_uri' member (no-member)
    E: 63,35: Module 'httpretty' has no 'GET' member (no-member)
    E: 72,12: Module 'httpretty' has no 'disable' member (no-member)
"""

CODE_FIX = """
def enable(*args, **kwds): pass
def disable(*args, **kwds): pass
def register_uri(*args, **kwds): pass
def GET(*args, **kwds): pass
def POST(*args, **kwds): pass
"""


def httpretty_transform():
    return AstroidBuilder(MANAGER).string_build(CODE_FIX)


def register(linter):
    register_module_extender(MANAGER, 'httpretty', httpretty_transform)
from astroid import MANAGER, register_module_extender
from astroid.builder import AstroidBuilder

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


def subprocess_transform():
    return AstroidBuilder(MANAGER).string_build(CODE_FIX)


def register(linter):
    register_module_extender(MANAGER, 'subprocess', subprocess_transform)
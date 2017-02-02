from astroid import MANAGER, register_module_extender
from astroid.builder import AstroidBuilder


CODE_FIX = """
class Notify(object):
    def Notification(*args, **kwds): pass
    def init(*args, **kwds): pass
    def new(*args, **kwds): pass
"""


def gi_repository_transform():
    return AstroidBuilder(MANAGER).string_build(CODE_FIX)


def register(linter):
    register_module_extender(MANAGER, 'gi.repository', gi_repository_transform)
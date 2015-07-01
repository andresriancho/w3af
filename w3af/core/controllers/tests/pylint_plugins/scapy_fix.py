from astroid import MANAGER, register_module_extender
from astroid.builder import AstroidBuilder


CODE_FIX = """
class IP(object): pass
class TCP(object): pass
class UDP(object): pass
class traceroute(object):
    def __init__(domain, dport=80, maxttl=1):
        pass
"""


def scapy_transform():
    return AstroidBuilder(MANAGER).string_build(CODE_FIX)


def register(linter):
    register_module_extender(MANAGER, 'scapy.all', scapy_transform)

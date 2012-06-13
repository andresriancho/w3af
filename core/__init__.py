# Before doing anything, check if I have all needed dependencies
from core.controllers.dependency_check.dependency_check import dependency_check
dependency_check()

# Some magic for nosetests to support i18n
def setUpPackage():
    import __builtin__
    __builtin__.__dict__['_'] = lambda x: x



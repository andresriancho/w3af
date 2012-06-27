# Some magic for nosetests to support i18n
def setUpPackage():
    import __builtin__
    __builtin__.__dict__['_'] = lambda x: x



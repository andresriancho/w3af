try:
    _('blah')
except BaseException:
    import __builtin__
    __builtin__.__dict__['_'] = lambda x: x


def setUpPackage():
    import __builtin__
    __builtin__.__dict__['_'] = lambda x: x

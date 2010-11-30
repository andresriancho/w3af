# Intended to be called by nose.
def setUpPackage():
    # Hack to init i18n function
    import __builtins__
    __builtins__.__dict__['_'] = lambda x: x
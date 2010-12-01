# Translation hack. Needed for tests completion.
try:
    _('blah')
except:
    import __builtin__
    __builtin__.__dict__['_'] = lambda x: x

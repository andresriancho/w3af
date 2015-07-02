from astroid import MANAGER
from astroid import scoped_nodes

NEED_FIX = ('Headers', 'NonRepeatKeyValueContainer', 'KeyValueContainer',
            'FormParameters')
FIX_MEMBERS = ('update', 'items', 'iteritems', 'keys', '__setitem__',
               'setdefault', 'get')


def register(linter):
    pass


def transform(cls):
    """
    pylint fails to "inherit" the attributes from the OrderedDict class when
    using multiple inheritance. So we need this fix for some special cases

    :param cls: The class, with name, etc.
    :return: None
    """
    if cls.name in NEED_FIX:
        for f in FIX_MEMBERS:
            cls.locals[f] = [scoped_nodes.Class(f, None)]


MANAGER.register_transform(scoped_nodes.Class, transform)
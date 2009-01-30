# -*- coding: iso-8859-1 -*-
'''Main module of the TkTreectrl package.
Once the TkTreectrl package is installed, it is safe to do :

    from TkTreectrl import *

This will add a number of constants and the following widget classes to the current
namespace:

Treectrl, MultiListbox, ScrolledTreectrl, ScrolledMultiListbox, ScrolledWidget

Constant names defined here include:

ABOVE = 'above'
ACTIVE = 'active'
ALL = 'all'
ASCII = 'ascii'
BELOW = 'below'
BITMAP  = 'bitmap'
BORDER = 'border'
DECREASING = 'decreasing'
DICTIONARY = 'dictionary'
DOUBLE = 'double'
DOT = 'dot'
DYNAMIC = 'dynamic'
ENABLED = 'enabled'
FIRST = 'first'
FIRSTCHILD = 'firstchild'
FOCUS = 'focus'
IMAGE = 'image'
INCREASING = 'increasing'
INTEGER = 'integer'
ITEM = 'item'
LAST = 'last'
LASTCHILD = 'lastchild'
LERFTMOST = 'leftmost'
LONG = 'long'
NEXT = 'next'
NEXTSIBLING = 'nextsibling'
OPEN = 'open'
PARENT = 'parent'
PREV = 'prev'
PREVSIBLING = 'prevsibling'
REAL = 'real'
RECT = 'rect'
RIGHTMOST = 'rightmost'
ROOT = 'root'
SELECT = 'select'
SELECTED = 'selected'
STATIC = 'static'
STRING = 'string'
TAIL = 'tail'
TEXT = 'text'
TIME = 'time'
TREE = 'tree'
WINDOW = 'window'
'''

ABOVE = 'above'
ACTIVE = 'active'
ALL = 'all'
ASCII = 'ascii'
BELOW = 'below'
BITMAP  = 'bitmap'
BORDER = 'border'
DECREASING = 'decreasing'
DICTIONARY = 'dictionary'
DOUBLE = 'double'
DOT = 'dot'
DYNAMIC = 'dynamic'
ENABLED = 'enabled'
FIRST = 'first'
FIRSTCHILD = 'firstchild'
FOCUS = 'focus'
IMAGE = 'image'
INCREASING = 'increasing'
INTEGER = 'integer'
ITEM = 'item'
LAST = 'last'
LASTCHILD = 'lastchild'
LERFTMOST = 'leftmost'
LONG = 'long'
NEXT = 'next'
NEXTSIBLING = 'nextsibling'
OPEN = 'open'
PARENT = 'parent'
PREV = 'prev'
PREVSIBLING = 'prevsibling'
REAL = 'real'
RECT = 'rect'
RIGHTMOST = 'rightmost'
ROOT = 'root'
SELECT = 'select'
SELECTED = 'selected'
STATIC = 'static'
STRING = 'string'
TAIL = 'tail'
TEXT = 'text'
TIME = 'time'
TREE = 'tree'
WINDOW = 'window'

from Treectrl import Treectrl
from MultiListbox import MultiListbox
from ScrolledTreectrl import ScrolledTreectrl
from ScrolledTreectrl import ScrolledMultiListbox
# put the ScrolledWidget class in the global namespace so people can easily
# create custom subclasses
from ScrolledTreectrl import ScrolledWidget

'''
Created on Dec 30, 2010

@author: jandalia
'''
from collections import deque
import sys

# TODO: Remove this code when w3af is supported by python >=2.6
if sys.version_info < (2, 6):
    import collections
    # Adding maxlen behaviour so it can be used as the 'tail filter' in Linux
    # We'll only be interested in the statuses for the last N responses
    class _deque(collections.deque):
        def __init__(self, iterable=(), maxlen=None):
            collections.deque.__init__(self, iterable)
            self._maxlen = maxlen
        def append(self, ele):
            collections.deque.append(self, ele)
            if len(self) > self._maxlen:
                self.popleft()
    deque = _deque

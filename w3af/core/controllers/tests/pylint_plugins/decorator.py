"""
decorator.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
from functools import wraps


def only_if_subclass(meth):
    """
    Function to decorate tests that should NOT be called unless they are
    a subclass of  
    """
    @wraps(meth)
    def test_only_subclass(self, *args, **kwds):
        """Note that this method needs to start with test_ in order for nose
        to run it!"""
        for base_klass in self.__class__.__bases__:
            if meth.__name__ in dir(base_klass) and \
            base_klass.__name__ != self.__class__.__name__:
                # The method that we're calling was defined in a base class
                # of the current caller, so we want to call it!
                return meth(self, *args, **kwds)
            
        return
        
    return test_only_subclass

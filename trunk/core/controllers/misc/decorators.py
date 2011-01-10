'''
decorators.py

Copyright 2011 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
'''

def runonce(exc_class=Exception):
    '''
    Function to decorate methods that should be called only once.
    
    @param exc_class: The Exception class to be raised when the method has
        already been called.
    '''
    def runonce_meth(meth):
        def inner_runonce_meth(self, *args):
            if not getattr(self, '_already_executed', False):
                self._already_executed = True
                return meth(self, *args)
            raise exc_class()
        return inner_runonce_meth
    return runonce_meth

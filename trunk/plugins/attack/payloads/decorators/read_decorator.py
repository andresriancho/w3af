'''
read_decorator.py

Copyright 2009 Andres Riancho

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
import core.controllers.outputManager as om

def read_debug(fn):
    def new( self, filename ):
        #   Run the original function
        result = fn( self, filename )
        no_newline_result = result.replace('\n','')
        no_newline_result = no_newline_result.replace('\r','')
        
        #   Format the message
        if len(no_newline_result) > 25:
            file_content = '"' + no_newline_result[:25] + '...' + '"'
        else:
            file_content = '"' + no_newline_result[:25] + '"'
            
        msg = 'read( "' + filename + '" , ' + file_content +') == ' + str(len(file_content)) + ' bytes.'
        
        #   Print the message to the debug output
        om.out.debug( msg )
        
        #   Return the result
        return result
        
    return new


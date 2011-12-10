'''
string_representation.py

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


class string_representation(object):
    '''
    Generates an image representation of any string. Very useful for comparing
    two or more strings in a split second. This representation can be used to
    generate an image, show in a GTK DrawingArea, etc.
    '''

    def __init__(self, instr, width=60, height=40):
        '''
        @param instr: The input string to represent.
        '''
        self.parsed_instr = {}
        self.gen_representation(instr, width, height)
        
    def gen_representation(self, instr, width, height):
        '''
        @param width: The width of the string to generate
        @param height: The width of the string to generate
        
        >>> instr = 'A\\n' * 40
        >>> si = string_representation( instr, 40, 40 )
        >>> si.get_representation()[1] == 25
        True
        >>> si.get_representation()[0] == 25
        True


        >>> instr = 'AA\\n' * 40
        >>> si = string_representation( instr, 40, 40 )
        >>> si.get_representation()[1] == 10
        True
        >>> si.get_representation()[0] == 10
        True

        >>> instr = 'AA\\n' * 80
        >>> si = string_representation( instr, 40, 40 )
        >>> si.get_representation()[1] == 20
        True
        >>> si.get_representation()[0] == 20
        True
        '''
        #
        #    Initial parsing
        #
        splitted = instr.split('\n')
        group_size = len(splitted) / width
        current_group_index = 0
        count = 0
        index = 0 
        
        for line in splitted:
            if current_group_index == 0:
                count = 0
            current_group_index += 1
            
            for char in line:
                count += ord(char)
            
            if current_group_index == group_size:
                self.parsed_instr[index] = count
                index += 1
                current_group_index = 0
            
        #
        #    Now I have a dict with the correct width, but I'll
        #    need to adjust the height also. The min value I can
        #    put in the image is 0 and the highest is $height so
        #    I have to translate all my values to that range. 
        # 
        for key, value in self.parsed_instr.iteritems():
            self.parsed_instr[key] = value % height 
            
    def get_representation(self):
        return self.parsed_instr

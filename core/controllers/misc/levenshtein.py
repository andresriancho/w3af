'''
levenshtein.py

Copyright 2008 Andres Riancho

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


def relative_distance(a_str, b_str):
    '''
    Computes the relative levenshtein distance between two strings. Its in the range
    (0-1] where 1 means total equality.
    
    @param a_str: A string object
    @param b_str: A string object
    @return: A float with the distance
    '''        
    m, n = (len(a_str),a_str), (len(b_str),b_str)
    
    #ensure that the 'm' tuple holds the longest string
    if(m[0] < n[0]):                
        m, n = n, m
    
    #assume distance = length of longest string (worst case)
    dist = m[0]
    
    # reduce the distance for each char match in shorter string   
    for i in range(0, n[0]):
        if m[1][i] == n[1][i]:
            dist = dist - 1
    
    # make it relative
    longer = float(max((len(a_str), len(b_str))))
    shorter = float(min((len(a_str), len(b_str))))    
    r = ((longer - dist) / longer) * (shorter / longer)
    r = 100 - r * 100
    
    r = r / 100
    r = 1 - r
    
    return r

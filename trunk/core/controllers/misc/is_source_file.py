'''
is_source_file.py

Copyright 2010 Andres Riancho

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
import re

# This regex means: "find all tags that are of the form <? something ?> 
# but if that something is "xml .*" ignore it completely. This is to 
# remove the false positive in the detection of code disclosure
# that is added when the web application uses something like
# <?xml version="1.0" encoding="UTF-8"?>
# This was added to fix bug #1989056
php = re.compile( '<\?(?! *xml).*\?>', re.IGNORECASE | re.DOTALL)

# The rest of the regex are ok, because this patterns aren't used in html / xhtml
asp = re.compile( '<%.*?%>', re.IGNORECASE | re.DOTALL)
# Commented this one because it's the same regular expression that ASP
#jsp = re.compile( '<%.*?%>', re.IGNORECASE | re.DOTALL)
jsp2 = re.compile( '<jsp:.*?>', re.IGNORECASE | re.DOTALL)

# I've also seen some devs think like this:
#
# 1- I have my code that says <? print 'something' ?>
# 2- I want to comment that code
# 3- I comment it like this!  <!--? print 'something' ?-->
# or like this:  <!--? print 'something' ?>
#
# Not a bad idea, huh?
commented_asp = re.compile( '<!--\s*%.*?%(--)?>', re.IGNORECASE | re.DOTALL)
commented_php = re.compile( '<!--\s*\?.*?\?(--)?>', re.IGNORECASE | re.DOTALL)
# Commented this one because it's the same regular expression that ASP
#commented_jsp = re.compile( '<!--\s*%.*?%(--)?>', re.IGNORECASE | re.DOTALL)
commented_jsp2 = re.compile( '<!--\s*jsp:.*?(--)?>', re.IGNORECASE | re.DOTALL)

REGEX_LIST = []
REGEX_LIST.append( (php, 'PHP') )
REGEX_LIST.append( (asp, 'ASP or JSP') )
#REGEX_LIST.append( (jsp, 'JSP') )
REGEX_LIST.append( (jsp2, 'JSP') )
REGEX_LIST.append( (commented_php, 'PHP') )
REGEX_LIST.append( (commented_asp, 'ASP or JSP') )
#REGEX_LIST.append( (commented_jsp, 'JSP') )
REGEX_LIST.append( (commented_jsp2, 'JSP') )


def is_source_file( file_content ):
    '''
    @parameter file_content: 
    @return: A tuple with (
                            a re.match object if the file_content matches a source code file,
                            a string with the source code programming language
                          ).
    '''
    for regex, lang in REGEX_LIST:
        
        match = regex.search( file_content )
        if match:
            return (match, lang)
    
    return (None, None)



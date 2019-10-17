"""
constants.py

Copyright 2006 Andres Riancho

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
QUOTE_CHARS = {'"', "'"}

ATTR_DELIMITERS = {'"', '`', "'"}

# These attributes run the value:
#
# <a onclick="ShowOld(2367,146986,2);">
JS_EVENTS = {'onclick', 'ondblclick', 'onmousedown', 'onmousemove',
             'onmouseout', 'onmouseover', 'onmouseup', 'onchange', 'onfocus',
             'onblur', 'onscroll', 'onselect', 'onsubmit', 'onkeydown',
             'onkeypress', 'onkeyup', 'onload', 'onunload'}

# These attributes do execute JavaScript code if they start with javascript:
# or vbscript: , otherwise they are not executable
#
# <a href="javascript:ShowOld(2367,146986,2);">
EXECUTABLE_ATTRS = {'href', 'src', 'background', 'dynsrc', 'lowsrc'}

# Note that the x at the beginning is important since in HTML the tag name needs
# to start with a letter
CONTEXT_DETECTOR = 'x3141592653589793'

"""
ignored_params.py

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

#
# The following is a list of parameter names that will be ignored during
# the fuzzing process
#
IGNORED_PARAMETERS = {'ASP.NET_SESSIONID',
                      'ASPSESSIONID',
                      'CFID',
                      'CFTOKEN',
                      'CSRFMIDDLEWARETOKEN',
                      'JAVAX.FACES.VIEWSTATE',
                      'JSESSIONID',
                      'JSF_SEQUENCE',
                      'JSF_STATE',
                      'JSF_STATE_64',
                      'JSF_TREE',
                      'JSF_TREE_64',
                      'JSF_VIEWID',
                      'PHPSESSID',
                      '__DNNVARIABLE',
                      '__EVENTARGUMENT',
                      '__EVENTTARGET',
                      '__EVENTVALIDATION',
                      '__VIEWSTATE',
                      '__VIEWSTATEENCRYPTED'}


def is_in_ignored_parameters(param):
    return param.upper() in IGNORED_PARAMETERS

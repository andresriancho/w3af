"""
url_list_option.py

Copyright 2008 Andres Riancho

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
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.options.list_option import ListOption 
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.options.option_types import URL_LIST


class URLListOption(ListOption):

    _type = URL_LIST

    def set_value(self, value):
        return super(URLListOption, self).set_value(value)

    def validate(self, value):
        parsed_list = super(URLListOption, self).validate(value)
        res = []
        
        for input_url in parsed_list:
            try:
                res.append(URL(input_url))
            except Exception, e:
                msg = 'Invalid URL configured by user, error: %s.' % e
                raise BaseFrameworkException(msg)
        
        return res

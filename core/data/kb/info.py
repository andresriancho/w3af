'''
info.py

Copyright 2006 Andres Riancho

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
import core.data.constants.severity as severity

from core.data.parsers.url import URL


class info(dict):
    '''
    This class represents an information that is saved to the kb.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self, data_obj=None):

        # Default values
        self._url = None
        self._uri = None
        self._desc = None
        self._method = None
        self._variable = None
        self._id = []
        self._name = None
        self._plugin_name = None
        self._plugin_name = ''
        self._dc = None
        self._string_matches = set()

        # Clone the info object!
        if isinstance(data_obj, info):
            self.set_uri(data_obj.get_uri())
            self.set_desc(data_obj.get_desc())
            self.set_method(data_obj.get_method())
            self.set_var(data_obj.get_var())
            self.set_id(data_obj.get_id())
            self.set_name(data_obj.get_name())
            self.set_dc(data_obj.get_dc())
            for k in data_obj.keys():
                self[k] = data_obj[k]

    def get_severity(self):
        '''
        @return: severity.INFORMATION , all information objects have the same
                 level of severity.
        '''
        return severity.INFORMATION

    def set_name(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def set_url(self, url):
        '''
        >>> i = info()
        >>> i.set_url('http://www.google.com/')
        Traceback (most recent call last):
          ...
        TypeError: The URL in the info object must be of url.URL type.
        >>> url = URL('http://www.google.com/')
        >>> i.set_url(url)
        >>> i.get_url() == url
        True
        '''
        if not isinstance(url, URL):
            raise TypeError(
                'The URL in the info object must be of url.URL type.')

        self._url = url.uri2url()
        self._uri = url

    def get_url(self):
        return self._url

    def set_uri(self, uri):
        '''
        >>> i = info()
        >>> i.set_uri('http://www.google.com/')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        TypeError: The URI in the info object must be of url.URL type.
        >>> uri = URL('http://www.google.com/')
        >>> i = info()
        >>> i.set_uri(uri)
        >>> i.get_uri() == uri
        True
        '''
        if not isinstance(uri, URL):
            raise TypeError(
                'The URI in the info object must be of url.URL type.')

        self._uri = uri
        self._url = uri.uri2url()

    def get_uri(self):
        return self._uri

    def set_method(self, method):
        self._method = method.upper()

    def get_method(self):
        return self._method

    def set_desc(self, desc):
        self._desc = desc

    def get_desc(self, with_id=True):
        #
        #    TODO: Who's creating a info() object and not setting a description?!
        #
        if self._desc is None:
            return 'No description was set for this object.'

        if self._id is not None and self._id != 0 and with_id:
            if not self._desc.strip().endswith('.'):
                self._desc += '.'

            # One request OR more than one request
            desc_to_return = self._desc
            if len(self._id) > 1:
                desc_to_return += ' This information was found in the requests with'
                desc_to_return += ' ids ' + \
                    self._convert_to_range_wrapper(self._id) + '.'
            elif len(self._id) == 1:
                desc_to_return += ' This information was found in the request with'
                desc_to_return += ' id ' + str(self._id[0]) + '.'

            return desc_to_return
        else:
            return self._desc

    def set_plugin_name(self, plugin_name):
        self._plugin_name = plugin_name

    def get_plugin_name(self):
        return self._plugin_name

    def _convert_to_range_wrapper(self, list_of_integers):
        '''
        Just a wrapper for _convert_to_range; please see documentation below!

        @return: The result of self._convert_to_range( list_of_integers ) but
                 without the trailing comma.
        '''
        res = self._convert_to_range(list_of_integers)
        if res.endswith(','):
            res = res[:-1]
        return res

    def _convert_to_range(self, seq):
        '''
        Convert a list of integers to a nicer "range like" string. Assumed
        that `seq` elems are ordered.

        @see test_info.py
        '''
        first = last = seq[0]
        dist = 0
        res = []
        last_in_seq = seq[-1]
        is_last_in_seq = lambda num: num == last_in_seq

        for num in seq[1:]:
            # Is it a new subsequence?
            is_new_seq = (num != last + 1)
            if is_new_seq:  # End of sequence
                if dist:  # multi-elems sequence
                    res.append(_('%s to %s') % (first, last))
                else:  # one-elem sequence
                    res.append(first)
                if is_last_in_seq(num):
                    res.append(_('and') + ' %s' % num)
                    break
                dist = 0
                first = num
            else:
                if is_last_in_seq(num):
                    res.append(_('%s to %s') % (first, num))
                    break
                dist += 1
            last = num

        res_str = ', '.join(str(ele) for ele in res)
        return res_str.replace(', ' + _('and'), ' and')

    def __str__(self):
        return self._desc

    def __repr__(self):
        return '<info object for issue: "' + self._desc + '">'

    def set_id(self, id):
        '''
        The id is a unique number that identifies every request and response
        performed by the framework.

        The id parameter is usually an integer, that points to that request/
        response pair.

        In some cases, one information object is related to more than one
        request/response, in those cases, the id parameter is a list of integers.

        For example, in the cases where the info object is related to one
        request / response, we get this call:
            set_id( 3 )

        And we save this to the attribute:
            [ 3, ]

        When the info object is related to more than one request / response,
        we get this call:
            set_id( [3, 4] )

        And we save this to the attribute:
            [ 3, 4]

        Also, the list is sorted!
            set_id( [4, 3] )

        Will save:
            [3, 4]
        '''
        if isinstance(id, list):
            # A list with more than one ID:
            # Ensuring that all of them are actually integers
            for i in id:
                assert isinstance(
                    i, int), 'All request/response ids have to be integers.'
            id.sort()
            self._id = id
        else:
            self._id = [id, ]

    def get_id(self):
        '''
        @return: The list of ids related to this information object. Please read
                 the documentation of set_id().
        '''
        return self._id

    def set_var(self, variable):
        self._variable = variable

    def get_var(self):
        return self._variable

    def set_dc(self, dc):
        self._dc = dc

    def get_dc(self):
        return self._dc

    def get_to_highlight(self):
        '''
        The string match is the string that was used to identify the vulnerability.
        For example, in a SQL injection the string match would look like:

            - "...supplied argument is not a valid MySQL..."

        This information is used to highlight the string in the GTK user interface,
        when showing the request / response.
        '''
        return self._string_matches

    def add_to_highlight(self, *str_match):
        for s in str_match:
            if s:
                self._string_matches.add(s)

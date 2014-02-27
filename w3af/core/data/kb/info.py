"""
info.py

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
from w3af.core.data.constants.severity import INFORMATION
from w3af.core.data.parsers.url import URL
from w3af.core.data.fuzzer.mutants.mutant import Mutant
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class Info(dict):
    """
    This class represents an information that is saved to the kb.
    
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, name, desc, response_ids, plugin_name):
        """
        :param name: The vulnerability name, will be checked against the values
                     in core.data.constants.vulns.
        
        :param desc: The vulnerability description
        
        :param severity: The severity for this object
        
        :param response_ids: A list of response ids associated with this vuln
        
        :param plugin_name: The name of the plugin which identified the vuln
        """
        # Default values
        self._url = None
        self._uri = None
        self._method = 'GET'
        self._variable = None
        self._dc = None
        self._string_matches = set()
        self._mutant = None
        
        self.set_id(response_ids)
        self.set_name(name)
        self.set_desc(desc)
        self.set_plugin_name(plugin_name)
    
    @classmethod
    def from_mutant(cls, name, desc, response_ids, plugin_name, mutant):
        """
        :return: An info instance with the proper data set based on the values
                 taken from the mutant.
        """
        if not isinstance(mutant, Mutant):
            raise TypeError('Mutant expected in from_mutant.')
        
        inst = cls(name, desc, response_ids, plugin_name)

        inst.set_uri(mutant.get_uri())
        inst.set_method(mutant.get_method())
        inst.set_var(mutant.get_var())
        inst.set_dc(mutant.get_dc())
        inst.set_mutant(mutant)
            
        return inst

    @classmethod
    def from_fr(cls, name, desc, response_ids, plugin_name, freq):
        """
        :return: An info instance with the proper data set based on the values
                 taken from the fuzzable request.
        """
        if not isinstance(freq, FuzzableRequest):
            raise TypeError('FuzzableRequest expected in from_fr.')
        
        inst = cls(name, desc, response_ids, plugin_name)

        inst.set_uri(freq.get_uri())
        inst.set_method(freq.get_method())
        inst.set_dc(freq.get_dc())
            
        return inst
            
    @classmethod
    def from_info(cls, other_info):
        """
        :return: A clone of other_info. 
        """
        if not isinstance(other_info, Info):
            raise TypeError('Info expected in from_info.')
        
        name = other_info.get_name()
        desc = other_info.get_desc()
        response_ids = other_info.get_id()
        plugin_name = other_info.get_plugin_name()
        
        inst = cls(name, desc, response_ids, plugin_name)

        inst._uri = other_info.get_uri()
        inst._url = other_info.get_url()
        inst._method = other_info.get_method()
        inst._variable = other_info.get_var()
        inst._dc = other_info.get_dc()
        inst._string_matches = other_info.get_to_highlight()
        inst._mutant = other_info.get_mutant()

        for k in other_info.keys():
            inst[k] = other_info[k]

        return inst

    def get_severity(self):
        """
        :return: severity.INFORMATION , all information objects have the same
                 level of severity.
        """
        return INFORMATION

    def set_name(self, name):
        """
        if not is_valid_name(name):
            msg = 'Invalid vulnerability name "%s" specified.'
            raise ValueError(msg % name)
        """
        self._name = name

    def get_name(self):
        return self._name

    def set_url(self, url):
        if not isinstance(url, URL):
            error = 'The URL in the info object must be of url.URL type.'
            raise TypeError(error)

        self._url = url.uri2url()
        self._uri = url

    def get_url(self):
        return self._url

    def set_uri(self, uri):
        if not isinstance(uri, URL):
            msg = 'The URI in the info object must be of url.URL type.'
            raise TypeError(msg)

        self._uri = uri
        self._url = uri.uri2url()

    def get_uri(self):
        return self._uri

    def set_method(self, method):
        self._method = method.upper()

    def get_method(self):
        return self._method

    def set_desc(self, desc):
        if not isinstance(desc, basestring):
            raise TypeError('Descriptions need to be strings.')
        
        if len(desc) <= 15:
            raise ValueError('Description too short.')

        if '%s' in desc:
            msg = 'Format string resolution missing is set_desc method for'\
                  ' string "%s".'
            raise ValueError(msg % desc)
        
        self._desc = desc

    def get_desc(self, with_id=True):
        return self._get_desc_impl('information', with_id)
    
    def _get_desc_impl(self, what, with_id=True):
        
        if self._id is not None and self._id != 0 and with_id:
            if not self._desc.strip().endswith('.'):
                self._desc += '.'

            # One request OR more than one request
            desc_to_return = self._desc
            if len(self._id) > 1:
                id_range = self._convert_to_range_wrapper(self._id)
                
                desc_to_return += ' This %s was found in the requests with' % what
                desc_to_return += ' ids %s.' % id_range

            elif len(self._id) == 1:
                desc_to_return += ' This %s was found in the request with' % what
                desc_to_return += ' id %s.' % self._id[0]

            return desc_to_return
        else:
            return self._desc

    def set_plugin_name(self, plugin_name):
        self._plugin_name = plugin_name

    def get_plugin_name(self):
        return self._plugin_name

    def _convert_to_range_wrapper(self, list_of_integers):
        """
        Just a wrapper for _convert_to_range; please see documentation below!

        :return: The result of self._convert_to_range( list_of_integers ) but
                 without the trailing comma.
        """
        res = self._convert_to_range(list_of_integers)
        if res.endswith(','):
            res = res[:-1]
        return res

    def _convert_to_range(self, seq):
        """
        Convert a list of integers to a nicer "range like" string. Assumed
        that `seq` elems are ordered.

        @see test_info.py
        """
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
    
    def get_uniq_id(self):
        """
        :return: A uniq identifier for this info object. Since info objects are
                 persisted to SQLite and then re-generated for showing them to
                 the user, we can't use id() to know if two info objects are
                 the same or not.
                 
                 Also, for some special cases it's not enough to be able to use
                 __eq__ since the code was already designed to use id().
                 
                 This method was added as part of the KB to SQLite migration
                 and might disappear in the future. If possible use __eq__
                 to verify if two instances are the same.
        """
        concat_all = ''
        
        for functor in (self.get_uri, self.get_method, self.get_var,
                        self.get_dc, self.get_id, self.get_name, self.get_desc,
                        self.get_plugin_name):
            data = functor()
            if isinstance(data, unicode):
                data = data.encode('utf-8')
            concat_all += str(data)
            
        return str(hash(concat_all))
    
    def __eq__(self, other):
        return self.get_uri() == other.get_uri() and\
               self.get_method() == other.get_method() and\
               self.get_var() == other.get_var() and\
               self.get_dc() == other.get_dc() and\
               self.get_id() == other.get_id() and\
               self.get_name() == other.get_name() and\
               self.get_desc() == other.get_desc() and\
               self.get_plugin_name() == other.get_plugin_name()

    def set_id(self, _id):
        """
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
        """
        if isinstance(_id, list):
            # A list with more than one ID:
            # Ensuring that all of them are actually integers
            error_msg = 'All request/response ids have to be integers.'
            for i in _id:
                assert isinstance(i, int), error_msg
            _id.sort()
            self._id = _id
        elif isinstance(_id, int):
            self._id = [_id, ]
        else:
            raise TypeError('IDs need to be lists of int or int not %s' % type(_id))

    def get_id(self):
        """
        :return: The list of ids related to this information object. Please read
                 the documentation of set_id().
        """
        return self._id

    def set_var(self, variable):
        self._variable = variable

    def get_var(self):
        return self._variable

    def set_dc(self, dc):
        self._dc = dc

    def get_dc(self):
        return self._dc

    def set_mutant(self, mutant):
        """
        Sets the mutant that created this vuln.
        """
        self._mutant = mutant

    def get_mutant(self):
        return self._mutant

    def get_to_highlight(self):
        """
        The string match is the string that was used to identify the
        vulnerability. For example, in a SQL injection the string match would
        look like:

            - "...supplied argument is not a valid MySQL..."

        This information is used to highlight the string in the GTK user
        interface, when showing the request / response.
        """
        return self._string_matches

    def add_to_highlight(self, *str_match):
        for s in str_match:
            if not isinstance(s, basestring):
                raise TypeError('Only able to highlight strings.')
            
            self._string_matches.add(s)

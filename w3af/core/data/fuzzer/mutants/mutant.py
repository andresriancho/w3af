"""
mutant.py

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
import copy

from w3af.core.data.constants.ignored_params import is_in_ignored_parameters
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.db.disk_item import DiskItem


class Mutant(DiskItem):
    """
    This class is a wrapper for fuzzable requests that has been modified.
    """
    def __init__(self, freq):
        super(Mutant, self).__init__()

        self._freq = freq
        self._original_response_body = None

    def copy(self):
        return copy.deepcopy(self)

    def get_fuzzable_request(self):
        return self._freq

    def set_fuzzable_request(self, freq):
        self._freq = freq

    def set_dc(self, data_container):
        msg = 'Mutant sub-class "%s" needs to implement set_dc'
        raise NotImplementedError(msg % self.__class__.__name__)

    def get_dc(self):
        msg = 'Mutant sub-class "%s" needs to implement get_dc'
        raise NotImplementedError(msg % self.__class__.__name__)

    def get_token(self):
        return self.get_dc().get_token()

    def set_token(self, token_path):
        """
        Shortcut!
        :return: For the current data-container, point the token to a specific
                 location specified by *args.
        """
        return self.get_dc().set_token(token_path)

    def get_token_value(self):
        """
        Shortcut!
        :return: The current token value
        """
        return self.get_token().get_value()

    def get_token_payload(self):
        """
        Shortcut!
        :return: The current token payload
        """
        return self.get_token().get_payload()

    def get_token_original_value(self):
        """
        Shortcut!
        :return: The current token original value
        """
        return self.get_token().get_original_value()

    def set_token_original_value(self, new_value):
        """
        Shortcut!
        :return: The current token original value
        """
        return self.get_token().set_original_value(new_value)

    def get_token_name(self):
        """
        Shortcut!
        :return: The current token value
        """
        return self.get_token().get_name()

    def set_token_value(self, value):
        """
        Shortcut!
        :return: Sets the current token to :value:
        """
        token = self.get_token()

        if token is not None:
            return token.set_value(value)

        dc = self.get_dc()
        msg = 'Token is None at "%s" data container dump: "%s"'
        args = (dc.__class__.__name__, dc)
        raise AttributeError(msg % args)

    def __repr__(self):
        fmt = '<mutant-%s | %s | %s >'
        return fmt % (self.get_mutant_type(), self.get_method(), self.get_uri())

    def get_original_response_body(self):
        """
        The fuzzable request is a representation of a request; the original
        response body is the body of the response that is generated when w3af
        requests the fuzzable request for the first time.
        """
        if self._original_response_body is None:
            raise ValueError('[mutant error] You should set the original '
                             'response body before getting its value!')
        return self._original_response_body

    def set_original_response_body(self, orig_body):
        self._original_response_body = orig_body

    #
    # All the other methods are forwarded to the fuzzable request except for
    # the magic methods.
    #
    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError("%s instance has no attribute '%s'" %
                                 (self.__class__.__name__, name))
        return getattr(self._freq, name)

    def get_eq_attrs(self):
        return ['_freq', '_original_response_body']

    def __eq__(self, other):
        return (self.get_token() == other.get_token() and
                self.get_fuzzable_request() == other.get_fuzzable_request())

    def found_at(self):
        """
        Return a string representing WHAT was fuzzed. This string
        is used like this:
            - v.set_desc('SQL injection was found at: ' + mutant.found_at())
        """
        dc = self.get_dc()
        dc_short = dc.get_short_printable_repr()
        token = dc.get_token()

        msg = '"%s", using HTTP method %s. The sent data was: "%s"'
        msg %= (smart_str_ignore(self.get_url()),
                smart_str_ignore(self.get_method()),
                smart_str_ignore(dc_short))

        if token is not None:
            msg += ' The modified parameter was "%s".' % smart_str_ignore(token.get_name())

        return msg

    @staticmethod
    def get_mutant_type():
        return 'generic'

    @classmethod
    def get_mutant_class(cls):
        return cls.__name__

    @classmethod
    def create_mutants(cls, freq, payload_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        return cls._create_mutants_worker(freq, cls, payload_list,
                                          fuzzable_param_list,
                                          append, fuzzer_config)

    @staticmethod
    def _create_mutants_worker(freq, mutant_cls, payload_list,
                               fuzzable_param_list, append,
                               fuzzer_config):
        """
        An auxiliary function to create_mutants.

        :return: A list of mutants.
        """
        if not issubclass(mutant_cls, Mutant):
            msg = 'mutant_cls parameter needs to be one of the known mutant'\
                  ' classes, not %s.'
            raise ValueError(msg % mutant_cls)

        result = []

        # This line has a lot of magic in it!
        #
        # The basic idea is that we're wrapping the FuzzableRequest instance in
        # a Mutant sub-class, then the sub-class implements a way to get one of
        # the FuzzableRequest attributes and return it as a DataContainer, so we
        # can fuzz it!
        data_container = mutant_cls(freq).get_dc()

        for payload in payload_list:
            for dc_copy, token in data_container.iter_bound_tokens():
                #
                # Ignore the banned parameter names
                #
                if is_in_ignored_parameters(token.get_name()):
                    continue

                # Only fuzz the specified parameters (if any)
                # or fuzz all of them (the fuzzable_param_list == [] case)
                if not fuzzable_param_list == []:
                    if not token.get_name() in fuzzable_param_list:
                        continue

                # Ok, now we have a data container with the mutant string,
                # but it's possible that all the other fields of the data
                # container are empty (think about a form). We need to fill
                # those in, with something *useful* to get around the
                # easiest developer checks like: "parameter A was filled" or
                # "parameter A is a number".

                # But I only perform this task in HTML forms, everything
                # else is left as it is:
                if hasattr(dc_copy, 'smart_fill'):
                    dc_copy.smart_fill()

                if append:
                    if not isinstance(payload, basestring):
                        # This prevents me from flattening the special type to
                        # a string in a couple of lines below where I apply the
                        # string formatting
                        msg = 'Incorrect payload type %s'
                        raise RuntimeError(msg % type(payload))

                    original_value = token.get_original_value()
                    token.set_value('%s%s' % (original_value, payload))
                else:
                    token.set_value(payload)

                # Create the mutant
                freq_copy = copy.deepcopy(freq)
                m = mutant_cls(freq_copy)
                m.set_dc(dc_copy)

                # Done, add it to the result
                result.append(m)

        return result

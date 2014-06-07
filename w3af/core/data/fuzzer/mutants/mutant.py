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

from w3af.core.controllers.misc.io import NamedStringIO

from w3af.core.data.dc.form import Form
from w3af.core.data.dc.token import DataToken
from w3af.core.data.fuzzer.form_filler import smart_fill
from w3af.core.data.constants.ignored_params import IGNORED_PARAMETERS
from w3af.core.data.constants.file_templates.file_templates import get_file_from_template
from w3af.core.data.db.disk_item import DiskItem


class Mutant(DiskItem):
    """
    This class is a wrapper for fuzzable requests that has been modified.
    """
    def __init__(self, freq):
        super(Mutant, self).__init__()
        
        self._freq = freq
        self._original_response_body = None

    def get_eq_attrs(self):
        return ['_freq', '_original_response_body']

    def copy(self):
        return copy.deepcopy(self)

    def get_fuzzable_req(self):
        return self._freq

    def set_fuzzable_req(self, freq):
        self._freq = freq

    def get_token(self):
        return self._freq.get_dc().get_token()

    def get_token_value(self):
        """
        Shortcut!
        :return: The current token value
        """
        return self.get_token().get_value()

    def set_token_value(self, value):
        """
        Shortcut!
        :return: Sets the current token to :value:
        """
        return self.get_token().set_value(value)

    def print_token_value(self):
        fmt = 'The data that was sent is: "%s".'
        return fmt % self.get_data()

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
        msg = msg % (self.get_url(), self.get_method(), dc_short)

        if token is not None:
            msg += ' The modified parameter was "%s".' % token.get_name()

        return msg

    @staticmethod
    def get_mutant_type():
        return 'generic'

    @classmethod
    def get_mutant_class(cls):
        return cls.__name__        

    @staticmethod
    def create_mutants(freq, payload_list, fuzzable_param_list,
                       append, fuzzer_config, data_container=None):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        return Mutant._create_mutants_worker(freq, Mutant, payload_list,
                                             fuzzable_param_list,
                                             append, fuzzer_config,
                                             data_container)

    @staticmethod
    def _create_mutants_worker(freq, mutant_cls, payload_list,
                               fuzzable_param_list, append,
                               fuzzer_config, data_container=None):
        """
        An auxiliary function to create_mutants.

        :return: A list of mutants.
        """
        if not issubclass(mutant_cls, Mutant):
            msg = 'mutant_cls parameter needs to be one of the known mutant'\
                  ' classes, not %s.'
            raise ValueError(msg % mutant_cls)

        result = []

        if data_container is None:
            data_container = freq.get_dc()

        for payload in payload_list:

            for dc_copy, token in data_container.iter_bound_tokens():
                #
                # Ignore the banned parameter names
                #
                if token.get_name() in IGNORED_PARAMETERS:
                    continue

                # Exclude the file parameters, those are fuzzed in
                # FileContentMutant (depending on framework config)
                #
                # But if we have a form with files, then we have a multipart
                # form, and we have to keep it that way. If we don't send
                # the multipart form as multipart, the remote programming
                # language may ignore all the request, and the parameter
                # that we are fuzzing (that's not the file content one)
                # will be ignored too
                #
                # The "keeping the multipart form alive" thing is done some
                # lines below, search for the "__HERE__" string!
                #
                # The exclusion is done here:
                if token.get_name() in freq.get_file_vars() \
                and not isinstance(payload, NamedStringIO) \
                and not isinstance(payload, file):
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
                if isinstance(dc_copy, Form):
                    dc_copy = mutant_smart_fill(freq, dc_copy, fuzzer_config)

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
                freq_copy = freq.copy()
                m = mutant_cls(freq_copy)
                m.set_dc(dc_copy)

                # Done, add it to the result
                result.append(m)

        return result

AVOID_FILLING_FORM_TYPES = {'checkbox', 'radio', 'select'}


def mutant_smart_fill(freq, dc_copy, fuzzer_config):
    """
    :param freq: The fuzzable request (original request instance) we're fuzzing

    :return: A data container that has been filled using smart_fill, not filling
             the data container location which contains the DataToken instance
    """
    for var_name, value, setter in dc_copy.iter_setters():
        if dc_copy.get_type(var_name) in AVOID_FILLING_FORM_TYPES:
            continue

        if isinstance(value, DataToken):
            # This is the value which is being fuzzed (the payload)
            continue

        # Please see the comment above (search for __HERE__) for an explanation
        # of what we are doing here:
        if var_name in freq.get_file_vars():
            # Try to upload a valid file
            extension = fuzzer_config.get('fuzz_form_files') or 'gif'
            success, file_content, file_name = get_file_from_template(extension)

            # I have to create the NamedStringIO with a "name",
            # required for MultipartPostHandler
            str_file = NamedStringIO(file_content, name=file_name)

            setter(str_file)

        #   Fill only if the parameter does NOT have a value set.
        #
        #   The reason of having this already set would be that the form
        #   has something like this:
        #
        #   <input type="text" name="p" value="foobar">
        #
        elif value == '':
            #
            #   Fill it smartly
            #
            setter(smart_fill(var_name))

    return dc_copy

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

from w3af.core.data.dc.data_container import DataContainer
from w3af.core.data.dc.form import Form
from w3af.core.data.fuzzer.form_filler import smart_fill
from w3af.core.data.constants.ignored_params import IGNORED_PARAMETERS
from w3af.core.data.constants.file_templates.file_templates import get_file_from_template
from w3af.core.data.db.disk_item import DiskItem


class Mutant(DiskItem):
    """
    This class is a wrapper for fuzzable requests that have been modified.
    """
    def __init__(self, freq, israw=False):
        super(Mutant, self).__init__()
        
        self._freq = freq
        self._var = ''
        self._index = 0
        self._original_value = ''
        self._original_response_body = None
        self._mutant_dc = DataContainer()
    
    def get_eq_attrs(self):
        return ['_freq', '_var', '_index', '_original_value',
                '_original_response_body', '_mutant_dc']
    
    def get_mutant_dc(self):
        return self._mutant_dc

    def set_mutant_dc(self, dc):
        if not isinstance(dc, DataContainer):
            raise TypeError('Argument must be a DataContainer instance.')
        self._mutant_dc = dc

    #
    # These methods are from the mutant
    #
    def get_fuzzable_req(self):
        return self._freq

    def set_fuzzable_req(self, freq):
        self._freq = freq

    def set_var(self, var, index=0):
        """
        Set the name of the variable that this mutant modifies.

        :param var: The variable name that's being modified.
        :param index: The index. This was added to support repeated parameter names.
                      For example, if the data container holds a=123&a=456, and I
                      want to overwrite 456, index has to be 1.
        """
        self._var = var
        self._index = index

    def get_var(self):
        return self._var

    def get_var_index(self):
        return self._index

    def set_original_value(self, v):
        self._original_value = v

    def get_original_value(self):
        return self._original_value

    def set_mod_value(self, val):
        """
        Set the value of the variable that this mutant modifies.
        """
        try:
            self._freq._dc[self.get_var()][self._index] = val
        except Exception, e:
            msg = 'The mutant object wasn\'t correctly initialized. Either' \
                  ' the variable to be modified, or the index of that variable'\
                  ' are incorrect. This error was found in set_mod_value() the'\
                  ' data original exception was: "%s".'
            raise ValueError(msg % e)

    def get_mod_value(self):
        """
        :return: The value that was sent to the remote server and triggered the
                 vulnerability.
        """
        try:
            return self._freq._dc[self.get_var()][self._index]
        except:
            msg = 'The mutant object wasn\'t correctly initialized. Either' \
                  ' the variable to be modified, or the index of that variable' \
                  ' are incorrect. This error was found in mutant.set_mod_value()'
            raise ValueError(msg)

    def print_mod_value(self):
        fmt = 'The data that was sent is: "%s".'
        return fmt % self.get_data()

    def __repr__(self):
        fmt = '<mutant-%s | %s | %s >'
        return fmt % (self.get_mutant_type(), self.get_method(), self.get_uri())

    def copy(self):
        return copy.deepcopy(self)

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
            - v.set_desc('SQL injection in a '+ v['db'] +
                        ' was found at: ' + mutant.found_at())
        """
        res = ['"%s", using HTTP method %s. The sent data was: "'
               % (self.get_url(), self.get_method())]

        # Depending on the data container, print different things:
        dc = self.get_dc()
        dc_length = sum(
            map(lambda item: len(item[0]) + len(item[1]), dc.items())
        )
        if dc_length > 65:
            res.append('...%s=%s..."' % (self.get_var(), self.get_mod_value()))
        else:
            res.append('%s".' % (dc,))
            if len(dc) > 1:
                res.append(
                    ' The modified parameter was "%s".' % self.get_var())

        return ''.join(res)

    @staticmethod
    def get_mutant_type():
        return 'generic'

    @classmethod
    def get_mutant_class(cls):
        return cls.__name__        

    @staticmethod
    def create_mutants(freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config, data_container=None):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        return Mutant._create_mutants_worker(freq, Mutant, mutant_str_list,
                                             fuzzable_param_list,
                                             append, fuzzer_config,
                                             data_container)

    @staticmethod
    def _create_mutants_worker(freq, mutant_cls, mutant_str_list,
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

        for pname in data_container:

            #
            # Ignore the banned parameter names
            #
            if pname in IGNORED_PARAMETERS:
                continue

            # This for is to support repeated parameter names
            for element_index, element_value in enumerate(data_container[pname]):

                for mutant_str in mutant_str_list:

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
                    if pname in freq.get_file_vars() \
                    and not isinstance(mutant_str, NamedStringIO) \
                    and not isinstance(mutant_str, file):
                        continue

                    # Only fuzz the specified parameters (if any)
                    # or fuzz all of them (the fuzzable_param_list == [] case)
                    if not fuzzable_param_list == []:
                        if not pname in fuzzable_param_list:
                            continue

                    dc_copy = data_container.copy()
                    original_value = element_value

                    # Ok, now we have a data container with the mutant string,
                    # but it's possible that all the other fields of the data
                    # container are empty (think about a form). We need to fill
                    # those in, with something *useful* to get around the
                    # easiest developer checks like: "parameter A was filled" or
                    # "parameter A is a number".

                    # But I only perform this task in HTML forms, everything
                    # else is left as it is:
                    if isinstance(dc_copy, Form):
                        dc_copy = mutant_smart_fill(freq, dc_copy, pname,
                                                    element_index,
                                                    fuzzer_config)

                    if append:
                        mutant_str = original_value + mutant_str
                    dc_copy[pname][element_index] = mutant_str

                    # Create the mutant
                    freq_copy = freq.copy()
                    m = mutant_cls(freq_copy)
                    m.set_var(pname, index=element_index)
                    m.set_dc(dc_copy)
                    m.set_original_value(original_value)
                    m.set_mod_value(mutant_str)

                    # Done, add it to the result
                    result.append(m)

        return result

AVOID_FILLING_FORM_TYPES = {'checkbox', 'radio', 'select', 'file'}


def mutant_smart_fill(freq, dc_copy, ignore_pname, ignore_index, fuzzer_config):
    """
    :param freq: The fuzzable request (original request instance) we're fuzzing
    :param ignore_pname: A parameter name to ignore
    :param ignore_index: The index we want to ignore

    :return: A data container that has been filled using smart_fill, ignoring
             the parameters that I'm fuzzing and filling the file inputs with
             valid image file.
    """
    for var_name_dc in dc_copy:
        for element_index_dc, element_value_dc in enumerate(dc_copy[var_name_dc]):

            if (var_name_dc, element_index_dc) == (ignore_pname, ignore_index):
                continue

            if dc_copy.get_type(var_name_dc) in AVOID_FILLING_FORM_TYPES:
                continue

            #   Fill only if the parameter does NOT have a value set.
            #
            #   The reason of having this already set would be that the form
            #   has something like this:
            #
            #   <input type="text" name="p" value="foobar">
            #
            if dc_copy[var_name_dc][element_index_dc] == '':
                #
                #   Fill it smartly
                #
                dc_copy[var_name_dc][element_index_dc] = smart_fill(var_name_dc)

    # Please see the comment above (search for __HERE__) for an explanation
    # of what we are doing here:
    for var_name in freq.get_file_vars():

        # Try to upload a valid file
        extension = fuzzer_config.get('fuzz_form_files') or 'gif'
        success, file_content, file_name = get_file_from_template(extension)

        # I have to create the NamedStringIO with a "name",
        # required for MultipartPostHandler
        str_file = NamedStringIO(file_content, name=file_name)

        # TODO: Is this hard-coded [0] enough?
        dc_copy[var_name][0] = str_file

    return dc_copy

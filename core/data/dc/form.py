# -*- coding: utf8 -*-
'''
form.py

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

import operator
import random

from core.data.constants.encodings import DEFAULT_ENCODING
from core.data.dc.dataContainer import DataContainer
from core.data.parsers.encode_decode import urlencode
from core.data.parsers.urlParser import url_object
import core.controllers.outputManager as om


class Form(DataContainer):
    '''
    This class represents a HTML form.
    
    @author: Andres Riancho ( andres.riancho@gmail.com ) |
        Javier Andalia (jandalia =at= gmail.com)
    '''
    # Max
    TOP_VARIANTS = 15
    MAX_VARIANTS_TOTAL = 10**9
    SEED = 1
    
    def __init__(self, init_val=(), encoding=DEFAULT_ENCODING):
        super(Form, self).__init__(init_val, encoding)
        
        # Internal variables
        self._method = None
        self._action = None
        self._types = {}
        self._files = []
        self._selects = {}
        self._submitMap = {}
        
        # This is used for processing checkboxes
        self._secret_value = "3_!21#47w@"
        
    def getAction(self):
        '''
        @return: The Form action.
        '''
        return self._action
        
    def setAction(self, action):
        '''
        >>> f = Form()
        >>> f.setAction('http://www.google.com/')
        Traceback (most recent call last):
          ...
        TypeError: The action of a Form must be of urlParser.url_object type.
        >>> f = Form()
        >>> action = url_object('http://www.google.com/')
        >>> f.setAction(action)
        >>> f.getAction() == action
        True
        '''
        if not isinstance(action, url_object):
            raise TypeError('The action of a Form must be of '
                             'urlParser.url_object type.')
        self._action = action
        
    def getMethod(self):
        '''
        @return: The Form method.
        '''
        return self._method
    
    def setMethod(self, method):
        self._method = method.upper()
    
    def getFileVariables( self ):
        return self._files

    def _setVar(self, name, value):
        '''
        Auxiliary setter for name=value
        '''
        # added to support repeated parameter names
        vals = self.setdefault(name, [])
        vals.append(value)

    def addFileInput( self, attrs ):
        '''
        Adds a file input to the Form
        @parameter attrs: attrs=[("class", "screen")]
        '''
        name = ''

        for attr in attrs:
            if attr[0] == 'name':
                name = attr[1]
                break

        if not name:
            for attr in attrs:
                if attr[0] == 'id':
                    name = attr[1]
                    break

        if name:
            self._files.append( name )
            self._setVar(name, '')
            # TODO: This does not work if there are different parameters in a form
            # with the same name, and different types
            self._types[name] = 'file'
    
    def __str__(self):
        '''
        This method returns a string representation of the Form object.
        
        >>> f = Form()
        >>> _ = f.addInput([("type", "text"), ("name", "abc"), ("value", "123")])
        >>> str(f)
        'abc=123'

        >>> f = Form()
        >>> _ = f.addInput([("type", "text"), ("name", "abc"), ("value", "123")])
        >>> _ = f.addInput([("type", "text"), ("name", "def"), ("value", "000")])        
        >>> str(f)
        'abc=123&def=000'
        
        >>> import urllib
        >>> f = Form() # Default encoding UTF-8
        >>> _ = f.addInput([("type", "text"), ("name", u"v"),("value", u"áéíóú")])
        >>> _ = f.addInput([("type", "text"), ("name", u"c"), ("value", u"ñçÑÇ")])
        >>> f.addSubmit('address', 'bsas')
        >>> urllib.unquote(str(f)).decode('utf-8') == u'c=ñçÑÇ&address=bsas&v=áéíóú'
        True

        @return: string representation of the Form object.
        '''
        #
        # FIXME: hmmm I think that we are missing something here... what about
        # self._select values. See FIXME below.
        #
        d = dict(self)
        d.update(self._submitMap)
        return urlencode(d, encoding=self.encoding)
        
    def addSubmit( self, name, value ):
        '''
        This is something I hadn't thought about !
        <input type="submit" name="b0f" value="Submit Request">
        '''
        self._submitMap[name] = value
        
    def addInput(self, attrs):
        '''
        Adds a input to the Form
        
        @parameter attrs: attrs=[("class", "screen")]
        '''

        '''
        <INPUT type="text" name="email"><BR>
        <INPUT type="radio" name="sex" value="Male"> Male<BR>
        '''
        # Set the default input type to text.
        attr_type = 'text'
        name = value = ''
        
        # Try to get the name:
        for attr in attrs:
            if attr[0] == 'name':
                name = attr[1]
        if not name:
            for attr in attrs:
                if attr[0] == 'id':
                    name = attr[1]

        if not name:
            return (name, value)

        # Find the attr_type
        for attr in attrs:
            if attr[0] == 'type':
                attr_type = attr[1].lower()

        # Find the default value
        for attr in attrs:
            if attr[0] == 'value':
                value = attr[1]

        if attr_type == 'submit':
            self.addSubmit( name, value )
        else:
            self._setVar(name, value)
        
        # Save the attr_type
        self._types[name] = attr_type
        
        #
        # TODO May be create special internal method instead of using
        # addInput()?
        #
        return (name, value)

    def getType( self, name ):
        return self._types[name]

    def addCheckBox(self, attrs):
        """
        Adds checkbox field
        """
        name, value = self.addInput(attrs)

        if not name:
            return

        if name not in self._selects:
            self._selects[name] = []

        if value not in self._selects[name]:
            self._selects[name].append(value)
            self._selects[name].append(self._secret_value)
            
        self._types[name] = 'checkbox'

    def addRadio(self, attrs):
        """
        Adds radio field
        """
        name, value = self.addInput(attrs)

        if not name:
            return
        
        self._types[name] = 'radio'
        
        if name not in self._selects:
            self._selects[name] = []

        #
        # FIXME: how do you maintain the same value in self._selects[name]
        # and in self[name] ?
        #
        if value not in self._selects[name]:
            self._selects[name].append(value)

    def addSelect(self, name, options):
        """
        Adds one more select field with options
        Options is list of options attrs (tuples)
        """
        if not name:
            return
        
        self._selects.setdefault(name, [])
        self._types[name] = 'select'
        
        value = ""
        for option in options:
            for attr in option:
                if attr[0].lower() == "value":
                    value = attr[1]
                    self._selects[name].append(value)

        self._setVar(name, value)

    def getVariants(self, mode="tmb"):
        """
        Generate all Form's variants by mode:
          "all" - all values
          "tb" - only top and bottom values
          "tmb" - top, middle and bottom values
          "t" - top values
          "b" - bottom values
        """
        
        if mode not in ("all", "tb", "tmb", "t", "b"):
            raise ValueError, "mode must be in ('all', 'tb', 'tmb', 't', 'b')"
        
        yield self

        # Nothing to do
        if not self._selects:
            return
        
        secret_value = self._secret_value
        sel_names = self._selects.keys()
        matrix = self._selects.values()

        # Build self variant based on `sample_path`
        for sample_path in self._getSamplePaths(mode, matrix):
            # Clone self
            self_variant = self.copy()
            
            for row_index, col_index in enumerate(sample_path):
                sel_name = sel_names[row_index]
                try:
                    value = matrix[row_index][col_index]
                except IndexError:
                    '''
                    This handles "select" tags that have no options inside.

                    The getVariants method should return a variant with the select tag name
                    that is always an empty string.

                    This case reported by Taras at https://sourceforge.net/apps/trac/w3af/ticket/171015
                    '''
                    value = ''
                
                if value != secret_value:
                    # FIXME: Needs to support repeated parameter names
                    self_variant[sel_name] = [value]
                else:
                    # FIXME: Is it good solution to simply delete unwant to
                    # send checkboxes?
                    if self_variant.get(sel_name): # We might had removed it b4
                        del self_variant[sel_name]
            
            yield self_variant

    def _getSamplePaths(self, mode, matrix):
        if mode in ["t", "tb"]:
            yield [0] * len(matrix)

        if mode in ["b", "tb"]:
            yield [-1] * len(matrix)
        # mode in ["tmb", "all"]
        elif mode in ["tmb", "all"]:
            variants_total = self._getVariantsCount(matrix, mode)
            
            # Combinatoric explosion. We only want TOP_VARIANTS paths top.
            # Create random sample. We ensure that random sample is unique
            # matrix by using `SEED` in the random generation
            if variants_total > self.TOP_VARIANTS:
                
                # Inform user
                om.out.information("w3af found an HTML form that has several"
                   " checkbox, radio and select input tags inside. Testing "
                   "all combinations of those values would take too much "
                   "time, the framework will only test %s randomly "
                   "distributed variants." % self.TOP_VARIANTS)

                # Init random object. Set our seed.
                rand = random.Random()
                rand.seed(self.SEED)

                # xrange in python2 has the following issue:
                # >>> xrange(10**10)
                # Traceback (most recent call last):
                # File "<stdin>", line 1, in <module>
                # OverflowError: long int too large to convert to int
                #
                # Which was amazingly reported by one of our users
                # http://sourceforge.net/apps/trac/w3af/ticket/161481
                #
                # Given that we want to test SOME of the combinations we're 
                # going to settle with a rand.sample from the first 
                # MAX_VARIANTS_TOTAL (=10**9) items (that works in python2)
                #
                # >>> xrange(10**9)
                # xrange(1000000000)
                # >>>

                variants_total = min(variants_total, self.MAX_VARIANTS_TOTAL)

                for path in rand.sample(xrange(variants_total),
                                            self.TOP_VARIANTS):
                    yield self._decodePath(path, matrix)

            # Less than TOP_VARIANTS elems in matrix
            else:
                # Compress matrix dimensions to (N x Mc) where 1 <= Mc <=3
                if mode == "tmb":
                    for row, vector in enumerate(matrix):
                        # Create new 3-length vector
                        if len(vector) > 3:
                            new_vector = [vector[0]]
                            new_vector.append(vector[len(vector)/2])
                            new_vector.append(vector[-1])
                            matrix[row] = new_vector

                    # New variants total
                    variants_total = self._getVariantsCount(matrix, mode)

                # Now get all paths!
                for path in xrange(variants_total):
                    decoded_path = self._decodePath(path, matrix)
                    yield decoded_path

    def _decodePath(self, path, matrix):
        '''
        Decode the integer `path` into a tuple of ints where the ith-elem 
        is the index to select from vector given by matrix[i].

        Diego Buthay (dbuthay@gmail.com) made a significant contribution to
        the used algorithm.
        
        @param path: integer
        @param matrix: list of lists
        @return: Tuple of integers
        '''        
        # Hack to make the algorithm work.
        matrix.append([1])
        get_count = lambda i: reduce(operator.mul, map(len, matrix[i+1:]))
        remainder = path
        decoded_path = []

        for i in xrange(len(matrix)-1):
            base = get_count(i)
            decoded_path.append(remainder / base)
            remainder = remainder % base

        # Restore state, pop out [1]
        matrix.pop()

        return decoded_path
    
    def _getVariantsCount(self, matrix, mode):
        '''
        
        @param matrix: 
        @param tmb: 
        '''
        if mode in ["t", "b"]:
            return 1
        elif mode == "tb":
            return 2
        else:
            len_fun = (lambda x: min(len(x), 3)) if mode == "tmb" else len
            return reduce(operator.mul, map(len_fun, matrix))

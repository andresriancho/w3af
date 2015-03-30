"""
fuzzygen.py

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
import re

try:
    from w3af.core.controllers.exceptions import BaseFrameworkException
except ImportError:
    # this is to easy the test when executing this file directly
    BaseFrameworkException = Exception

REPP = re.compile("\$.*?\$")


class FuzzyError(BaseFrameworkException):
    pass


class FuzzyGenerator(object):
    """Handles two texts with the fuzzy syntax.

    Syntax rules:
        - the "$" is the delimiter
        - to actually include a "$", use "\$"
        - if you write "$something$", the "something" will be evaluated with
          eval, having the "string" module already imported
          (eg: "$range(1,5,2)$", "$string.lowercase$").

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, txt1, txt2):
        # separate the sane and replaceable info
        self.torp1, self.sane1 = self._dissect(txt1)
        self.torp2, self.sane2 = self._dissect(txt2)

        # check validity
        self._genGenerators()

    def calculate_quantity(self):
        combin = 1
        genr1, genr2 = self._genGenerators()
        for elem in genr1 + genr2:
            if elem:
                combin *= len(elem)
        return combin

    def _genGenerators(self):
        # generate the generators, :)
        genr1 = [self._genIterator(x) for x in self.torp1]
        genr2 = [self._genIterator(x) for x in self.torp2]

        # if one of them is empty, put a dummy
        if not genr1:
            genr1 = [[]]
        if not genr2:
            genr2 = [[]]
        return genr1, genr2

    def _genIterator(self, text):
        """Generates the iterator from the text."""
        namespace = {"string": __import__("string")}
        try:
            it = eval(text, namespace)
        except Exception, e:
            msg = _("%s: %s (generated from %r)") % (e.__class__.__name__, e,
                                                     text)
            raise FuzzyError(msg)

        try:
            iter(it)
        except TypeError:
            msg = _("%r is not iterable! (generated from %r)") % (it, text)
            raise FuzzyError(msg)
        return it

    def _dissect(self, txt):
        """Separates the fixed and dynamic part from the text.

        :param txt: the string of the HTTP request to process.
        """
        #
        #    fix for bug #164086
        #
        try:
            header = txt.split('\n')[0]
            url_string = header.split(' ')[1]
            replaced_url_string = url_string.replace('%24', '$')
            txt = txt.replace(url_string, replaced_url_string)
        except:
            pass
        #
        #    /fix for bug #164086
        #

        # remove the \$
        txt = txt.replace("\$", "\x00")

        # separate sane texts from what is to be replaced
        toreplace = REPP.findall(txt)
        saneparts = REPP.split(txt)

        # transform \$ for $
        for i, part in enumerate(toreplace):
            if "\x00" in part:
                toreplace[i] = part.replace("\x00", "$")
        for i, part in enumerate(saneparts):
            if "\x00" in part:
                saneparts[i] = part.replace("\x00", "$")

        # extract border $
        toreplace = [x[1:-1] for x in toreplace]

        return toreplace, saneparts

    def generate(self):
        """Generates the different possibilities."""
        genr1, genr2 = self._genGenerators()
        for x in self._possib(genr1):
            full1 = self._build(self.sane1, x)
            for y in self._possib(genr2):
                full2 = self._build(self.sane2, y)
                yield (full1, full2)

    def _build(self, sane, vals):
        """Constructs the whole text again."""
        if vals is None:
            return sane[0]
        full = []
        for x, y in zip(sane, vals):
            full.append(str(x))
            full.append(str(y))
        full.append(str(sane[-1]))
        return "".join(full)

    def _possib(self, generat, constr=None):
        """Builds the different possibilities."""
        if constr is None:
            constr = []
        pos = len(constr)
        if not generat[pos]:
            yield None
        for elem in generat[pos]:
            if pos + 1 == len(generat):
                yield constr + [elem]
            else:
                for val in self._possib(generat, constr + [elem]):
                    yield val

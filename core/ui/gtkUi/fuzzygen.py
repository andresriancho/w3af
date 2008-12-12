'''
fuzzygen.py

Copyright 2008 Andres Riancho

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
import re
try:
    from core.controllers.w3afException import w3afException
except ImportError:
    # this is to easy the test when executing this file directly
    w3afException = Exception

REPP = re.compile("\$.*?\$")

class FuzzyError(w3afException): pass

# Syntax rules:
#
# - the "$" is the delimiter
#
# - to actually include a "$", use "\$"
#
# - if you write "$something$", the "something" will be evaluated with
#   eval, having the "string" module already imported (eg:
#   "$range(1,5,2)$", "$string.lowercase$").

class FuzzyGenerator(object):
    '''Handles two texts with the fuzzy syntax.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, txt1, txt2):
        # separate the sane and replaceable info
        self.torp1, self.sane1 = self._dissect(txt1)
        self.torp2, self.sane2 = self._dissect(txt2)

        # check validity
        self._genGenerators()

    def calculateQuantity(self):
        combin = 1
        genr1, genr2 = self._genGenerators()
        for elem in genr1+genr2:
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
        '''Generates the iterator from the text.'''
        namespace = {"string":__import__("string")}
        try:
            it = eval(text, namespace)
        except Exception, e:
            msg = _("%s: %s (generated from %r)") % (e.__class__.__name__, e,
                                                                        text)
            raise FuzzyError(msg)

        try:
            iter(it)
        except TypeError:
            msg = _("%r is not iterable! (generated from %r)") % (it,text)
            raise FuzzyError(msg)
        return it

    def _dissect(self, txt):
        '''Separates the fixed and dynamic part from the text.

        @param txt: the text to process.
        '''
        # remove the \$
        txt = txt.replace("\$", "\x00")

        # separate sane texts from what is to be replaced
        toreplace = REPP.findall(txt)
        saneparts = REPP.split(txt)

        # transform \$ for $
        for i,part in enumerate(toreplace):
            if "\x00" in part:
                toreplace[i] = part.replace("\x00", "$")
        for i,part in enumerate(saneparts):
            if "\x00" in part:
                saneparts[i] = part.replace("\x00", "$")

        # extract border $
        toreplace = [x[1:-1] for x in toreplace]

        return toreplace, saneparts

    def generate(self):
        '''Generates the different possibilities.'''
        genr1, genr2 = self._genGenerators()
        for x in self._possib(genr1):
            full1 = self._build(self.sane1, x)
            for y in self._possib(genr2):
                full2 = self._build(self.sane2, y)
                yield (full1, full2)

    def _build(self, sane, vals):
        '''Constructs the whole text again.'''
        if vals is None:
            return sane[0]
        full = []
        for x,y in zip(sane, vals):
            full.append(str(x))
            full.append(str(y))
        full.append(str(sane[-1]))
        return "".join(full)

    def _possib(self, generat, constr=None):
        '''Builds the different possibilities.'''
        if constr is None:
            constr = []
        pos = len(constr)
        if not generat[pos]:
            yield None
        for elem in generat[pos]:
            if pos+1 == len(generat):
                yield constr+[elem]
            else:
                for val in self._possib(generat, constr+[elem]):
                    yield val


if __name__ == "__main__":
    import unittest
    globals()["_"] = lambda x: x

    class TestAll(unittest.TestCase):
        def test_simple_doubledollar(self):
            fg = FuzzyGenerator("Hola \$mundo\ncruel", "")
            self.assertEqual(fg.sane1, ["Hola $mundo\ncruel"])

            fg = FuzzyGenerator("Hola \$mundo\ncruel\$", "")
            self.assertEqual(fg.sane1, ["Hola $mundo\ncruel$"])

            fg = FuzzyGenerator("Hola \$mundo\ncruel\$asdfg\$\$gh", "")
            self.assertEqual(fg.sane1, ["Hola $mundo\ncruel$asdfg$$gh"])

        def test_quantities(self):
            fg = FuzzyGenerator("$range(2)$ dnd$'as'$", "pp")
            self.assertEqual(fg.calculateQuantity(), 4)

            fg = FuzzyGenerator("$range(2)$ n$'as'$", "p$string.lowercase[:2]$")
            self.assertEqual(fg.calculateQuantity(), 8)

        def test_generations(self):
            fg = FuzzyGenerator("$range(2)$ dnd$'as'$", "pp")
            self.assertEqual(list(fg.generate()), [
                ('0 dnda', 'pp'), ('0 dnds', 'pp'),
                ('1 dnda', 'pp'), ('1 dnds', 'pp')])

            fg = FuzzyGenerator("$range(2)$ d$'as'$", "p$string.lowercase[:2]$")
            self.assertEqual(list(fg.generate()), [
                ('0 da', 'pa'), ('0 da', 'pb'), ('0 ds', 'pa'), ('0 ds', 'pb'),
                ('1 da', 'pa'), ('1 da', 'pb'), ('1 ds', 'pa'), ('1 ds', 'pb'),
            ])

        def test_quant_gen_gen(self):
            fg = FuzzyGenerator("$range(2)$ dnd$'as'$", "pp")
            self.assertEqual(fg.calculateQuantity(), 4)

            self.assertEqual(list(fg.generate()), [
                ('0 dnda', 'pp'), ('0 dnds', 'pp'),
                ('1 dnda', 'pp'), ('1 dnds', 'pp')])

        def test_noniterable(self):
            self.assertRaises(FuzzyError, FuzzyGenerator, "", "aa $3$ bb")
            self.assertRaises(FuzzyError, FuzzyGenerator, "",
                                                "aa $[].extend([1,2])$ bb")

        def test_inside_doubledollar(self):
            fg = FuzzyGenerator(
                    "GET http://localhost/$['aaa\$b', 'b\$ccc']$ HTTP/1.0", "")
            self.assertEqual(list(fg.generate()), [
                ("GET http://localhost/aaa$b HTTP/1.0", ""),
                ("GET http://localhost/b$ccc HTTP/1.0", ""),
                                ])

        def test_double_token_together(self):
            # from bug 2393362, the idea is to generate 00 to 99
            # using to generators (I'm doing less iterations here)
            fg = FuzzyGenerator("-$xrange(2)$$xrange(2)$-", "")
            self.assertEqual(list(fg.generate()), [
                ("-00-", ""), ("-01-", ""), ("-10-", ""), ("-11-", "") ])

    unittest.main()

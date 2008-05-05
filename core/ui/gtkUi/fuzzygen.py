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

REPP = re.compile("\$.*?\$")

class FuzzyError(Exception): pass

# Syntax rules:
# 
# - the "$" is the delimiter
# 
# - to actually include a "$", use "$$"
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
        torp1, self.sane1 = self._dissect(txt1)
        torp2, self.sane2 = self._dissect(txt2)

        # generate the generators, :)
        namespace = {"string":__import__("string")}
        try:
            self.genr1 = [eval(x, namespace) for x in torp1]
            self.genr2 = [eval(x, namespace) for x in torp2]
        except Exception, e:
            raise FuzzyError("%s: %s" % (e.__class__.__name__, e))

        # if one of them is empty, put a dummy
        if not self.genr1:
            self.genr1 = [[]]
        if not self.genr2:
            self.genr2 = [[]]

    def _dissect(self, txt):
        # separate sane texts from what is to be replaced 
        toreplace = REPP.findall(txt)
        saneparts = REPP.split(txt)
        
        # transform $$ for $
        self._doubleMark(toreplace, saneparts)

        # extract border $
        toreplace = [x[1:-1] for x in toreplace]
    
        return toreplace, saneparts

    def _doubleMark(self, torp, sane):
        '''Replaces $$ for $, modifying the lists in place.'''
        # check if anything to do
        if "$$" not in torp:
            return

        # get the position, and delete the mark
        pos = torp.index("$$")
        del torp[pos]

        # join the two sane elements
        sane[pos:pos+2] = [sane[pos] + "$" + sane[pos+1]]

        # check again, recursively
        self._doubleMark(torp, sane)

    def generate(self):
        for x in self._possib(self.genr1):
            full1 = self._build(self.sane1, x)
            for y in self._possib(self.genr2):
                full2 = self._build(self.sane2, y)
                yield (full1, full2)

    def _build(self, sane, vals):
        if vals is None:
            return sane[0]
        full = []
        for x,y in zip(sane, vals):
            full.append(str(x))
            full.append(str(y))
        full.append(str(sane[-1]))
        return "".join(full)

    def _possib(self, generat, constr=[]):
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
    # simple $$ to $ checks
    fg = FuzzyGenerator("Hola $$mundo\ncruel", "")
    assert fg.sane1 == ["Hola $mundo\ncruel"]
    
    fg = FuzzyGenerator("Hola $$mundo\ncruel$$", "")
    assert fg.sane1 == ["Hola $mundo\ncruel$"]
    
    fg = FuzzyGenerator("Hola $$mundo\ncruel$$asdfg$$$$gh", "")
    assert fg.sane1 == ["Hola $mundo\ncruel$asdfg$$gh"]

    # generations
    fg = FuzzyGenerator("$range(2)$ dnd$'as'$", "pp")
    assert list(fg.generate()) == [
        ('0 dnda', 'pp'), ('0 dnds', 'pp'), ('1 dnda', 'pp'), ('1 dnds', 'pp')]

    fg = FuzzyGenerator("$range(2)$ dnd$'as'$", "pp$string.lowercase[:2]$")
    assert list(fg.generate()) == [
        ('0 dnda', 'ppa'), ('0 dnda', 'ppb'), ('0 dnds', 'ppa'), ('0 dnds', 'ppb'),
        ('1 dnda', 'ppa'), ('1 dnda', 'ppb'), ('1 dnds', 'ppa'), ('1 dnds', 'ppb'),
    ]

'''
history.py

Copyright 2007 Andres Riancho

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

import cPickle, operator, os

class HistorySuggestion(object):
    '''Handles the history of any text, providing suggestions.

    @param filename: Name of the file where the info is stored

    It's also responsible of loading and saving the info in a file.
    '''
    def __init__(self, filename):
        self.filename = filename
        self.history = {}

        if os.access(filename, os.R_OK):
            # dict: {text:points}
            fileh = open(filename)
            self.history = cPickle.load(fileh)
            fileh.close()

    def getTexts(self):
        '''Provides the texts, ordered by relevance.

        @return: a generator with the texts
        '''
        info = sorted(self.history.items(), key=operator.itemgetter(1), reverse=True)
        return [k for k,v in info]

    def insert(self, newtext):
        self.history[newtext] = self.history.get(newtext, 0) + 1

    def save(self):
        fileh = open(self.filename, "w")
        cPickle.dump(self.history, fileh)
        fileh.close()

if __name__ == "__main__":
    import random, string, time

    QUANT = 5000
    LENGTH = 50
    print "Testing History with %d elements" % QUANT

    arch = "test_history.pickle"
    if os.access(arch, os.F_OK):
        os.remove(arch)
    his = HistorySuggestion(arch)

    texts = ["".join(random.choice(string.letters) for x in xrange(LENGTH)) for y in xrange(QUANT)]

    print "Storing the elements:",
    tini = time.time()
    for txt in texts:
        his.insert(txt)
    print "%.1f mseg/element" % ((time.time() - tini) * 1000 / QUANT)

    print "Saving to disk:",
    tini = time.time()
    his.save()
    print "%.1f mseg" % ((time.time() - tini) * 1000)

    print "Loading from disk:",
    tini = time.time()
    HistorySuggestion(arch)
    print "%.1f mseg" % ((time.time() - tini) * 1000)

    os.remove(arch)

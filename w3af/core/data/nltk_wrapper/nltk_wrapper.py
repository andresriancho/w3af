"""
nltk_wrapper.py

Copyright 2011 Andres Riancho

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
import os

from w3af import ROOT_PATH

# pylint: disable=E0611
# E0611: 24,0: No name 'util' in module 'LazyModule'
# E0611: 26,0: No name 'reader' in module 'LazyModule'
# E0611: 27,0: No name 'reader' in module 'LazyModule'
from nltk.corpus.util import LazyCorpusLoader
from nltk.data import ZipFilePathPointer
from nltk.corpus.reader.wordnet import WordNetCorpusReader
from nltk.corpus.reader.api import CorpusReader


class wordnet_loader(LazyCorpusLoader):
    def __init__(self, name, reader_cls, *args, **kwargs):
        super(wordnet_loader, self).__init__(name, reader_cls, *args, **kwargs)
        assert issubclass(reader_cls, CorpusReader)
        self.__name = self.__name__ = name
        self.__reader_cls = reader_cls
        self.__args = args
        self.__kwargs = kwargs

    def __load(self):
        # Find the corpus root directory.
        zip_location = os.path.join(
            ROOT_PATH, 'plugins', 'crawl', 'wordnet', 'wordnet.zip')
        root = ZipFilePathPointer(zip_location, 'wordnet/')

        # Load the corpus.
        corpus = self.__reader_cls(root, None, *self.__args, **self.__kwargs)

        # This is where the magic happens!  Transform ourselves into
        # the corpus by modifying our own __dict__ and __class__ to
        # match that of the corpus.
        self.__dict__ = corpus.__dict__
        self.__class__ = corpus.__class__

    def __getattr__(self, attr):
        self.__load()
        # This looks circular, but its not, since __load() changes our
        # __class__ to something new:
        return getattr(self, attr)

wn = wordnet_loader('wordnet', WordNetCorpusReader)

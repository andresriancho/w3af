# -*- coding: iso-8859-1 -*-

"""Utilities for clue storage.

Provides functionality needed to store clues on disk.
"""

# Copyright (C) 2004, 2005, 2006 Juan M. Bello Rivas <jmbr@superadditive.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import os
import csv
import types
import shutil

import Halberd.util
from Halberd.clues.Clue import Clue


class InvalidFile(Exception):
    """The loaded file is not a valid clue file.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


def save(filename, clues):
    """Save a clues to a file.

    @param filename: Name of the file where the clues will be written to.
    @type filename: C{str}

    @param clues: Sequence of clues to write.
    @type clues: C{list}
    """
    # Create or truncate the destination file.
    cluefp = open(filename, 'w+')
    writer = csv.writer(cluefp)

    for clue in clues:
        # Store the most relevant clue information.
        writer.writerow((clue.getCount(), clue._local, clue.headers))

    cluefp.close()


def load(filename):
    """Load clues from file.

    @param filename: Name of the files where the clues are stored.
    @type filename: C{str}

    @return: Clues extracted from the file.
    @rtype: C{list}

    @raise InvalidFile: In case there's a problem while reinterpreting the
    clues.
    """
    cluefp = open(filename, 'r')
    reader = csv.reader(cluefp)

    clues = []
    for tup in reader:
        try:
            count, localtime, headers = tup
        except ValueError:
            raise InvalidFile, 'Cannot unpack fields'

        # Recreate the current clue.
        clue = Clue()
        try:
            clue._count = int(count)
            clue._local = float(localtime)
        except ValueError:
            raise InvalidFile, 'Could not convert fields'

        # This may be risky from a security standpoint.
        clue.headers = eval(headers, {}, {})
        if not (isinstance(clue.headers, types.ListType) or
                isinstance(clue.headers, types.TupleType)):
            raise InvalidFile, 'Wrong clue header field'
        clue.parse(clue.headers)

        clues.append(clue)

    cluefp.close()
    return clues


class ClueDir:
    """Stores clues hierarchically using the underlying filesystem.

    ClueDir tries to be as portable as possible but requires the host operating
    system to be able to create long filenames (and directories, of course).

    This is an example layout::

        http___www_microsoft_com/
        http___www_microsoft_com/207_46_134_221.clu
        http___www_microsoft_com/207_46_156_220.clu
        http___www_microsoft_com/207_46_156_252.clu
                .
                .
                .
    """
    def __init__(self, root=None):
        """Initializes ClueDir object.

        @param root: Root folder where to start creating sub-folders.
        @type root: C{str}
        """
        self.ext = 'clu'
        if not root:
            self.root = os.getcwd()
        else:
            self.root = root
            self._mkdir(self.root)

    def _sanitize(self, url):
        """Filter out potentially dangerous chars.
        """
        return url.translate(Halberd.util.table)

    def _mkdir(self, dest):
        """Creates a directory to store clues.

        If the directory already exists it won't complain about that.
        """
        try:
            st = os.stat(dest)
        except OSError:
            os.mkdir(dest)
        else:
            if not shutil.stat.S_ISDIR(st.st_mode):
                raise InvalidFile, \
                      '%s already exist and is not a directory' % dest

        return dest

    def save(self, url, addr, clues):
        """Hierarchically write clues.

        @param url: URL scanned (will be used as a directory name).
        @type url: C{url}

        @param addr: Address of the target.
        @type addr: C{str}

        @param clues: Clues to be stored.
        @type clues: C{list}

        @raise OSError: If the directories can't be created.
        @raise IOError: If the file can't be stored successfully.
        """
        assert url and addr
        
        urldir = self._mkdir(os.path.join(self.root, self._sanitize(url)))
        filename = self._sanitize(addr) + os.extsep + self.ext
        cluefile = os.path.join(urldir, filename)

        Halberd.clues.file.save(cluefile, clues)


# vim: ts=4 sw=4 et

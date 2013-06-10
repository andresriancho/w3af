#!/usr/bin/env python

"""
Copyright (c) 2006-2013 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

from lib.core.enums import DBMS
from lib.core.settings import MAXDB_SYSTEM_DBS
from lib.core.unescaper import unescaper
from w3af.plugins.dbms.maxdb.enumeration import Enumeration
from w3af.plugins.dbms.maxdb.filesystem import Filesystem
from w3af.plugins.dbms.maxdb.fingerprint import Fingerprint
from w3af.plugins.dbms.maxdb.syntax import Syntax
from w3af.plugins.dbms.maxdb.takeover import Takeover
from w3af.plugins.generic.misc import Miscellaneous

class MaxDBMap(Syntax, Fingerprint, Enumeration, Filesystem, Miscellaneous, Takeover):
    """
    This class defines SAP MaxDB methods
    """

    def __init__(self):
        self.excludeDbsList = MAXDB_SYSTEM_DBS

        Syntax.__init__(self)
        Fingerprint.__init__(self)
        Enumeration.__init__(self)
        Filesystem.__init__(self)
        Miscellaneous.__init__(self)
        Takeover.__init__(self)

    unescaper[DBMS.MAXDB] = Syntax.escape

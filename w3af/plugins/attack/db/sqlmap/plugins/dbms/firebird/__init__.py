#!/usr/bin/env python

"""
Copyright (c) 2006-2013 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

from lib.core.enums import DBMS
from lib.core.settings import FIREBIRD_SYSTEM_DBS
from lib.core.unescaper import unescaper
from w3af.plugins.dbms.firebird.enumeration import Enumeration
from w3af.plugins.dbms.firebird.filesystem import Filesystem
from w3af.plugins.dbms.firebird.fingerprint import Fingerprint
from w3af.plugins.dbms.firebird.syntax import Syntax
from w3af.plugins.dbms.firebird.takeover import Takeover
from w3af.plugins.generic.misc import Miscellaneous

class FirebirdMap(Syntax, Fingerprint, Enumeration, Filesystem, Miscellaneous, Takeover):
    """
    This class defines Firebird methods
    """

    def __init__(self):
        self.excludeDbsList = FIREBIRD_SYSTEM_DBS

        Syntax.__init__(self)
        Fingerprint.__init__(self)
        Enumeration.__init__(self)
        Filesystem.__init__(self)
        Miscellaneous.__init__(self)
        Takeover.__init__(self)

    unescaper[DBMS.FIREBIRD] = Syntax.escape

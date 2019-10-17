#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import locale
import os
import re
import subprocess
import time

from lib.core.common import dataToStdout
from lib.core.common import getSafeExString
from lib.core.common import pollProcess
from lib.core.data import conf
from lib.core.data import logger
from lib.core.data import paths
from lib.core.revision import getRevisionNumber
from lib.core.settings import GIT_REPOSITORY
from lib.core.settings import IS_WIN


def update():
    if not conf.updateAll:
        return

    success = False

    if not os.path.exists(os.path.join(paths.SQLMAP_ROOT_PATH, ".git")):
        errMsg = "not a git repository. Please checkout the 'sqlmapproject/sqlmap' repository "
        errMsg += "from GitHub (e.g. 'git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap')"
        logger.error(errMsg)
    else:
        infoMsg = "updating sqlmap to the latest development version from the "
        infoMsg += "GitHub repository"
        logger.info(infoMsg)

        debugMsg = "sqlmap will try to update itself using 'git' command"
        logger.debug(debugMsg)

        dataToStdout("\r[%s] [INFO] update in progress " % time.strftime("%X"))

        try:
            process = subprocess.Popen(
                "git checkout . && git pull %s HEAD" %
                GIT_REPOSITORY,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=paths.SQLMAP_ROOT_PATH.encode(
                    locale.getpreferredencoding()))  # Reference: http://blog.stastnarodina.com/honza-en/spot/python-unicodeencodeerror/
            pollProcess(process, True)
            stdout, stderr = process.communicate()
            success = not process.returncode
        except (IOError, OSError) as ex:
            success = False
            stderr = getSafeExString(ex)

        if success:
            logger.info(
                "%s the latest revision '%s'" %
                ("already at" if "Already" in stdout else "updated to",
                 getRevisionNumber()))
        else:
            if "Not a git repository" in stderr:
                errMsg = "not a valid git repository. Please checkout the 'sqlmapproject/sqlmap' repository "
                errMsg += "from GitHub (e.g. 'git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap')"
                logger.error(errMsg)
            else:
                logger.error(
                    "update could not be completed ('%s')" %
                    re.sub(
                        r"\W+", " ", stderr).strip())

    if not success:
        if IS_WIN:
            infoMsg = "for Windows platform it's recommended "
            infoMsg += "to use a GitHub for Windows client for updating "
            infoMsg += "purposes (http://windows.github.com/) or just "
            infoMsg += "download the latest snapshot from "
            infoMsg += "https://github.com/sqlmapproject/sqlmap/downloads"
        else:
            infoMsg = "for Linux platform it's required "
            infoMsg += "to install a standard 'git' package (e.g.: 'sudo apt-get install git')"

        logger.info(infoMsg)

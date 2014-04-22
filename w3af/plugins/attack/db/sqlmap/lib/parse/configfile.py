#!/usr/bin/env python

"""
Copyright (c) 2006-2014 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

import codecs

from ConfigParser import MissingSectionHeaderError

from lib.core.common import checkFile
from lib.core.common import unArrayizeValue
from lib.core.common import UnicodeRawConfigParser
from lib.core.data import conf
from lib.core.data import logger
from lib.core.exception import SqlmapMissingMandatoryOptionException
from lib.core.exception import SqlmapSyntaxException
from lib.core.optiondict import optDict
from lib.core.settings import UNICODE_ENCODING

config = None

def configFileProxy(section, option, boolean=False, integer=False):
    """
    Parse configuration file and save settings into the configuration
    advanced dictionary.
    """

    global config

    if config.has_option(section, option):
        if boolean:
            value = config.getboolean(section, option) if config.get(section, option) else False
        elif integer:
            value = config.getint(section, option) if config.get(section, option) else 0
        else:
            value = config.get(section, option)

        if value:
            conf[option] = value
        else:
            conf[option] = None
    else:
        debugMsg = "missing requested option '%s' (section " % option
        debugMsg += "'%s') into the configuration file, " % section
        debugMsg += "ignoring. Skipping to next."
        logger.debug(debugMsg)

def configFileParser(configFile):
    """
    Parse configuration file and save settings into the configuration
    advanced dictionary.
    """

    global config

    debugMsg = "parsing configuration file"
    logger.debug(debugMsg)

    checkFile(configFile)
    configFP = codecs.open(configFile, "rb", UNICODE_ENCODING)

    try:
        config = UnicodeRawConfigParser()
        config.readfp(configFP)
    except MissingSectionHeaderError:
        errMsg = "you have provided an invalid configuration file"
        raise SqlmapSyntaxException(errMsg)

    if not config.has_section("Target"):
        errMsg = "missing a mandatory section 'Target' in the configuration file"
        raise SqlmapMissingMandatoryOptionException(errMsg)

    condition = not config.has_option("Target", "url")
    condition &= not config.has_option("Target", "logFile")
    condition &= not config.has_option("Target", "bulkFile")
    condition &= not config.has_option("Target", "googleDork")
    condition &= not config.has_option("Target", "requestFile")
    condition &= not config.has_option("Target", "wizard")

    if condition:
        errMsg = "missing a mandatory option in the configuration file "
        errMsg += "(url, logFile, bulkFile, googleDork, requestFile or wizard)"
        raise SqlmapMissingMandatoryOptionException(errMsg)

    for family, optionData in optDict.items():
        for option, datatype in optionData.items():
            datatype = unArrayizeValue(datatype)

            boolean = datatype == "boolean"
            integer = datatype == "integer"

            configFileProxy(family, option, boolean, integer)

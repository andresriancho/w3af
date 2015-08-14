#!/usr/bin/env python

"""
Copyright (c) 2006-2015 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

import os

from xml.etree import ElementTree as et

from lib.core.data import conf
from lib.core.data import paths
from lib.core.datatype import AttribDict
from lib.core.exception import SqlmapInstallationException

def cleanupVals(text, tag):
    if tag in ("clause", "where"):
        text = text.split(',')

    if isinstance(text, basestring):
        text = int(text) if text.isdigit() else str(text)

    elif isinstance(text, list):
        count = 0

        for _ in text:
            text[count] = int(_) if _.isdigit() else str(_)
            count += 1

        if len(text) == 1 and tag not in ("clause", "where"):
            text = text[0]

    return text

def parseXmlNode(node):
    for element in node.getiterator('boundary'):
        boundary = AttribDict()

        for child in element.getchildren():
            if child.text:
                values = cleanupVals(child.text, child.tag)
                boundary[child.tag] = values
            else:
                boundary[child.tag] = None

        conf.boundaries.append(boundary)

    for element in node.getiterator('test'):
        test = AttribDict()

        for child in element.getchildren():
            if child.text and child.text.strip():
                values = cleanupVals(child.text, child.tag)
                test[child.tag] = values
            else:
                if len(child.getchildren()) == 0:
                    test[child.tag] = None
                    continue
                else:
                    test[child.tag] = AttribDict()

                for gchild in child.getchildren():
                    if gchild.tag in test[child.tag]:
                        prevtext = test[child.tag][gchild.tag]
                        test[child.tag][gchild.tag] = [prevtext, gchild.text]
                    else:
                        test[child.tag][gchild.tag] = gchild.text

        conf.tests.append(test)

def loadBoundaries():
    try:
        doc = et.parse(paths.BOUNDARIES_XML)
    except Exception, ex:
        errMsg = "something seems to be wrong with "
        errMsg += "the file '%s' ('%s'). Please make " % (paths.BOUNDARIES_XML, ex)
        errMsg += "sure that you haven't made any changes to it"
        raise SqlmapInstallationException, errMsg

    root = doc.getroot()
    parseXmlNode(root)

def loadPayloads():
    payloadFiles = os.listdir(paths.SQLMAP_XML_PAYLOADS_PATH)
    payloadFiles.sort()

    for payloadFile in payloadFiles:
        payloadFilePath = os.path.join(paths.SQLMAP_XML_PAYLOADS_PATH, payloadFile)

        try:
            doc = et.parse(payloadFilePath)
        except Exception, ex:
            errMsg = "something seems to be wrong with "
            errMsg += "the file '%s' ('%s'). Please make " % (payloadFilePath, ex)
            errMsg += "sure that you haven't made any changes to it"
            raise SqlmapInstallationException, errMsg

        root = doc.getroot()
        parseXmlNode(root)

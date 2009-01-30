#!/usr/bin/env python
# -*- Mode: Python; py-indent-offset: 4 -*-

import optparse

import defsparser

parser = optparse.OptionParser(
    usage="usage: %prog [options] generated-defs old-defs")
parser.add_option("-p", "--merge-parameters",
                  help="Merge changes in function/methods parameter lists",
                  action="store_true", dest="parmerge", default=False)
(options, args) = parser.parse_args()

if len(args) != 2:
    parser.error("wrong number of arguments")

newp = defsparser.DefsParser(args[0])
oldp = defsparser.DefsParser(args[1])

newp.startParsing()
oldp.startParsing()

newp.merge(oldp, options.parmerge)

newp.write_defs()

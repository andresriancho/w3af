#!/usr/bin/env python
import sys

def main(args):
    output = args[1]
    input = args[2:]
    outfd = open(output, 'w')
    outfd.write(';; -*- scheme -*-\n')
    outfd.write(';; THIS FILE IS GENERATED - DO NOT EDIT\n')
    for filename in input:
        outfd.write('(include "%s")\n' % filename)
    outfd.close()

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

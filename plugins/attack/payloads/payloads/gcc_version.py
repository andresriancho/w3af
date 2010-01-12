import re

result = []

def parse_gcc_version( proc_version ):
    gcc_version = re.search('(?<=gcc version ).*?\)', proc_version)
    return gcc_version.group(0)

result.append(parse_gcc_version( read( '/proc/version')))

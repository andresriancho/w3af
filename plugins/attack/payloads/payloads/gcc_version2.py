import re

result = []

def parse_gcc_version( proc_version ):
    gcc_version = re.search('(?<=gcc version ).*?\)', proc_version)
    if gcc_version:
        return gcc_version.group(0)
    else:
        return ''

result.append(parse_gcc_version( execute( '/proc/version')))
result = [p for p in result if p != '']

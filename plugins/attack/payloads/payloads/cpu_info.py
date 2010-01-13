#REQUIRE_LINUX
import re

result = []

def parse_cpu_info( cpu_info ):
    processor = re.search('(?<=model name\t: )(.*)', cpu_info)
    if processor:
        return processor.group(1)
    else:
        return ''

def parse_cpu_cores( cpu_info ):
    cores = re.search('(?<=cpu cores\t: )(.*)', cpu_info)
    if cores:
        return cores.group(1)
    else:
        return ''

result.append(parse_cpu_info( read( '/proc/cpuinfo') ) \
                                   +' ['+parse_cpu_cores( read( '/proc/cpuinfo'))+' Cores]' )
result = [p for p in result if p != '']

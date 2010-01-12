#REQUIRE_LINUX
import re

result = []

def parse_cpu_info( cpu_info ):
    processor = re.search('(?<=model name\t: )(.*)', cpu_info)
    return processor.group(1)

result.append(parse_cpu_info( read( '/proc/cpuinfo') ) )
result = [p for p in result if p != '']

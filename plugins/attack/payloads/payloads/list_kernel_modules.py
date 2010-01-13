#REQUIRE_LINUX
import re

result = []

def parse_module_name ( modules_file ):
    name = re.findall('(.*?)\s(\d{0,6}) (\d.*?),? -?\s?Live', modules_file)
    return name

result.append('Module'.ljust(28)+'Size'.ljust(7)+'Used by'.ljust(20))
for module in parse_module_name(open( '/proc/modules').read()):
    result.append(module[0].ljust(28)+module[1].ljust(7)+module[2].ljust(20))

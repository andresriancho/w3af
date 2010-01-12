#REQUIRE_LINUX
import re

result = []

def parse_module_name ( modules_file ):
    name = re.findall('(.*?)\s(\d{0,6}) (\d.*?),? -?\s?Live', modules_file)
    return name

result.append('Module   Size    Used by')
for module in parse_module_name(open( '/proc/modules').read()):
    result.append(module[0]+'   '+module[1]+'   '+module[2])

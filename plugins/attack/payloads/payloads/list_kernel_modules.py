import re
from plugins.attack.payloads.base_payload import base_payload

class list_kernel_modules(base_payload):
    '''
    This payload displays a list of all modules loaded into the kernel
    '''
    def api_read(self):
        result = {}


        def parse_module_name ( modules_file ):
            name = re.findall('(.*?)\s(\d{0,6}) (\d.*?),? -?\s?Live', modules_file)
            if name:
                return name
            else:
                return ''

        for module in parse_module_name(self.shell.read( '/proc/modules')):
            result[module] = {}
            result[module] = {'size':module[1], 'used':module[2]}
        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('Module'.ljust(28)+'Size'.ljust(7)+'Used by'.ljust(20))
            for module, info in hashmap.iteritems():
                result.append(module[0].ljust(28)+hashmap[module]['size'].ljust(7)+hashmap[module]['used'].ljust(20))
        if result == [ ]:
            result.append('Kernel modules information not found.')
        return result

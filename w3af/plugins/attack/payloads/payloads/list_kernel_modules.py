import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class list_kernel_modules(Payload):
    """
    This payload displays a list of all modules loaded into the kernel
    """
    def api_read(self):
        result = {}

        def parse_module_info(modules_file):
            info = re.findall(
                '(.*?)\s(\d{0,6}) \d\d? (.*?),? -?\s?Live', modules_file)
            return info

        for info in parse_module_info(self.shell.read('/proc/modules')):
            name = info[0]
            used = info[2]

            if used == '-':
                used = ''

            result[name] = {}
            result[name] = {'used': used}

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'Failed to identify kernel modules.'
        else:
            rows = []
            rows.append(['Module', 'Used by'])
            rows.append([])

            modules = api_result.keys()
            modules.sort()

            for module in modules:
                used = api_result[module]['used']
                rows.append([module, used])

            result_table = table(rows)
            result_table.draw(80)
            return rows

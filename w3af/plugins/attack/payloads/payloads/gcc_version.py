import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class gcc_version(Payload):
    """
    This payload shows the current GCC Version
    """
    def api_read(self):
        result = {}

        def parse_gcc_version(proc_version):
            gcc_version = re.search('(?<=gcc version ).*?\)', proc_version)
            if gcc_version:
                return gcc_version.group(0)
            else:
                return ''

        version = parse_gcc_version(self.shell.read('/proc/version'))
        if version:
            result['gcc_version'] = version

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['gcc_version']:
            return 'GCC version could not be identified.'
        else:
            rows = []
            rows.append(['GCC Version', api_result['gcc_version']])
            result_table = table(rows)
            result_table.draw(80)
            return rows

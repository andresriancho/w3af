from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class route(Payload):
    """
    This payload shows the IP Routing Table.
    """
    def api_read(self):

        def parse_route(net_route):
            data = net_route.split(' ')
            if len(data) < 2:
                return []

            parsed_data = []
            data[0] = data[0] + data[1]
            data.remove(data[1])
            data = [i for i in data if i != '']

            for line in data:
                tmp = line.split('\t')
                tmp = [i for i in tmp if i != '']
                parsed_data.append(tmp)

            return parsed_data

        def dec_to_dotted_quad(n):
            d = 256 * 256 * 256
            q = []
            while d > 0:
                m, n = divmod(n, d)
                q.append(str(m))
                d /= 256
            q.reverse()
            return '.'.join(q)

        data = parse_route(self.shell.read('/proc/net/route'))
        result = {'route': []}

        for line in data:
            if len(line) > 7 and 'Iface' not in line:
                result['route'].append({'Iface': line[0][1:],
                                        'Destination': str(dec_to_dotted_quad(int(line[1], 16))),
                                        'Gateway': str(dec_to_dotted_quad(int(line[2], 16))),
                                        'Mask': str(dec_to_dotted_quad(int(line[7], 16)))})

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['route']:
            return 'Remote host routes could not be retrieved.'
        else:
            rows = []
            rows.append(['Interface', 'Destination', 'Gateway', 'Mask'])
            rows.append([])
            for a_route in api_result['route']:
                rows.append([a_route['Iface'], a_route['Destination'],
                            a_route['Gateway'], a_route['Mask']])

            result_table = table(rows)
            result_table.draw(80)

            return rows

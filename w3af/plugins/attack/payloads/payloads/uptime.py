from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class uptime(Payload):
    """
    This payload shows server Uptime.
    """
    def api_read(self):
        result = {}

        uptime = self.shell.read('/proc/uptime')
        uptime = uptime.split(' ')

        uptime[0] = int(float(uptime[0]))
        mins, secs = divmod(int(uptime[0]), 60)
        hours, mins = divmod(mins, 60)
        result['uptime'] = {'hours': str(hours), 'minutes': str(
            mins), 'seconds': str(secs)}

        uptime[1] = int(float(uptime[1]))
        mins, secs = divmod(int(uptime[1]), 60)
        hours, mins = divmod(mins, 60)
        result['idletime'] = {'hours': str(hours), 'minutes': str(
            mins), 'seconds': str(secs)}

        return result

    def run_read(self):
        api_result = self.api_read()

        rows = []
        rows.append(['Description', 'Hours', 'Minutes', 'Seconds'])
        rows.append([])
        for key in api_result:
            hours = api_result[key]['hours']
            minutes = api_result[key]['minutes']
            seconds = api_result[key]['seconds']
            rows.append([key, hours, minutes, seconds])

        result_table = table(rows)
        result_table.draw(80)
        return rows

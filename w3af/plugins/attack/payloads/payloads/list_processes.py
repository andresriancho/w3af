import re

import w3af.core.controllers.output_manager as om

from w3af.core.ui.console.tables import table
from w3af.plugins.attack.payloads.base_payload import Payload


class list_processes(Payload):
    """
    This payload shows current proccesses on the system.

    Usage: list_processes <max_pid>
    """
    def parse_proc_name(self, status_file):
        name = re.search('(?<=Name:\t)(.*)', status_file)
        if name:
            return name.group(1)
        else:
            return ''

    def parse_proc_state(self, status_file):
        state = re.search('(?<=State:\t)(.*)', status_file)
        if state:
            return state.group(1)
        else:
            return ''

    def api_read(self, max_pid_user):
        try:
            max_pid_user = int(max_pid_user)
        except:
            raise ValueError('Invalid max_pid, expected an integer.')

        result = {}
        stat_count = 400

        max_pid_proc = self.shell.read('/proc/sys/kernel/pid_max')[:-1]
        max_pid = min(max_pid_proc, max_pid_user)
        pid_iter = xrange(1, int(max_pid))
        
        def fname_iter(pid_iter):
            for pid in pid_iter:
                yield '/proc/%s/status' % pid
        
        
        for file_name, status_file in self.read_multi(fname_iter(pid_iter)):
            #   "progress bar"
            stat_count -= 1
            if stat_count == 0:
                om.out.console('.', new_line=False)
                stat_count = 400
            #   end "progress bar"
    
            cmd = ''
            if status_file:
                name = self.parse_proc_name(status_file)
                state = self.parse_proc_state(status_file)
                
                pid = file_name.split('/')[2]
                
                cmd = self.shell.read('/proc/%s/cmdline' % pid)
                cmd = cmd.replace('\x00', ' ')
                cmd = cmd.strip()
                if not cmd:
                    cmd = '[kernel process]'
                    
                result[pid] = {'name': name, 'state': state, 'cmd': cmd}
                om.out.console('+', new_line=False)

        return result

    def api_win_read(self):
        result = {}

        def parse_iis6_log(iis6_log):
            process_list = re.findall(
                '(?<=OC_ABOUT_TO_COMMIT_QUEUE:[)(.*)', iis6_log, re.MULTILINE)
            for process in process_list:
                pid, name = process.split('] ')
                result[pid] = {'name': name, 'state':
                                    'unknown', 'cmd': 'unknown'}

        parse_iis6_log(self.shell.read('/windows/iis6.log'))
        return result

    def run_read(self, max_pid):
        api_result = self.api_read(max_pid)

        if not api_result:
            return 'Failed to list proccesses.'
        else:
            rows = []
            rows.append(['PID', 'Name', 'Status', 'Cmd'])
            rows.append([])

            pids = api_result.keys()
            pids.sort()

            for pid in pids:
                name = api_result[pid]['name']
                state = api_result[pid]['state']
                cmd = api_result[pid]['cmd']

                rows.append([pid, name, state, cmd])

            result_table = table(rows)
            result_table.draw(80)
            return rows

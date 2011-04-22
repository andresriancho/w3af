from plugins.attack.payloads.base_payload import base_payload


class is_root(base_payload):
    '''
    Return True if the remote user has root privileges. 
    '''
    def api_read(self, parameters):
        
        shadow = self.shell.read('/etc/shadow')
        return 'root' in shadow
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
                
        if api_result:
            return 'The remote syscalls are run as root.'
        else:
            return 'The remote syscalls are NOT run as root.'        
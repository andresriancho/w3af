from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class hosts(base_payload):
    '''
    This payload shows the hosts allow and deny files.
    '''
    def api_read(self, parameters):
        result = {}
        hosts = []

        hosts.append('/etc/hosts')
        hosts.append('/etc/hosts.allow')
        hosts.append('/etc/hosts.deny')

        for file in hosts:
            content = self.shell.read(file)
            if content:
                result[file] = content
        return result
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'Hosts files not found.'
        else:
            rows = []
            rows.append( ['Host file', 'Content'] )
            rows.append( [] )
            for file in api_result:
                rows.append( [file, api_result[file]] )
                rows.append( [] )
                    
            result_table = table( rows[:-1] )
            result_table.draw( 160 )
            return
        
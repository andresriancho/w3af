import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload
import re
#TODO: Test it, doesnt work yet.

class spider(base_payload):
    '''
    This payload spiders through known readdable files to find more of them.
    '''
    def api_read(self, parameters):
        files = []
        self.result = []
        
        def check_files( self, files ):
            checked = []
            for file in files:
                file_content = self.shell.read(file)
                if file_content != '':
                    checked.append({file:file_content})
            return checked

        def get_files(self,  file_content ):
            files = re.findall('/([a-zA-Z0-9_\-.]+/)+[a-zA-Z0-9_.]+(?!/)', file_content, re.MULTILINE)
            files = re.match('(/([a-zA-Z0-9_\-.]+/)+[a-zA-Z0-9_.]+)(?!/)(.*?) ', '/var/www.com')
            if files:
                checked = check_files(self, files)
                for checked_file, checked_file_content in checked.iteritems():
                    get_files(self, checked_file_content)
                    self.result.update({checked_file:checked_file_content})

        payload =  self.exec_payload('payload_name')
        for file, file_content in payload.iteritems():
            if type(file_content).__name__ == 'dict':
                for k, v in file_content:
                    get_files(v)
            else:
                get_files(self, file_content)
        
        return self.result

    def run_read(self, parameters):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('payload_name - <Spider>')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        
        if result == [ ]:
            result.append('Payload retrived no results.')
        return result


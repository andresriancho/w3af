#REQUIRE_LINUX
import re

result = []
files = []


def parse_config (apache_config):
    config = re.findall('^(?!.?#)(.*?)$', apache_config, re.MULTILINE)
    if config:
        return config
    else:
        return ''

apache_config_files = run_payload('apache_config_files')
if apache_config_files:
    for file in apache_config_files:
        result.append('------------------------- ')
        result.append('FILE => '+file)
        for line in parse_config(read(file)):
            result.append(line)

result = [p for p in result if p != '']

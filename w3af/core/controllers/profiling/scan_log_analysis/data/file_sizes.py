import re
import os

from utils.output import KeyValueOutput

XML_OUTPUT_SIZE = re.compile('The XML output file size is (.*?) bytes.')


def get_file_sizes(scan_log_filename, scan):
    stat_info = os.stat(scan_log_filename)

    latest_xml_size = None

    for line in scan:
        match = XML_OUTPUT_SIZE.search(line)
        if match:
            latest_xml_size = match.group(1)

    data = {'debug_log': stat_info.st_size,
            'xml_output': latest_xml_size}

    return KeyValueOutput('file_sizes', 'output file sizes (bytes)', data)

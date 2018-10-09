import re
import os

XML_OUTPUT_SIZE = re.compile('The XML output file size is (.*?) bytes.')


def show_file_sizes(scan_log_filename, scan):
    print('')

    stat_info = os.stat(scan_log_filename)

    print('The debug log file size is %s bytes' % stat_info.st_size)

    latest_xml_size_line = None

    for line in scan:
        match = XML_OUTPUT_SIZE.search(line)
        if match:
            latest_xml_size_line = line

    if latest_xml_size_line is None:
        return

    print(latest_xml_size_line)

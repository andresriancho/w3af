#!/usr/bin/env python

"""
update.py

Copyright 2015 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import os
import csv
import sys

import subprocess32 as subprocess
import lxml.etree as etree


URL = 'https://data.phishtank.com/data/online-valid/'
XML_DB_FILE = 'w3af/plugins/crawl/phishtank/index.xml'
CSV_DB_FILE = 'w3af/plugins/crawl/phishtank/index.csv'
DOWNLOAD_CMD = 'wget -q %s -O %s'


class PhishTankHandler(object):
    """
    <entry>
        <url><![CDATA[http://cbisis...paypal.support/]]></url>
        <phish_id>118884</phish_id>
        <phish_detail_url>
            <![CDATA[http://www.phishtank.com/phish_detail.php?phish_id=118884]]>
        </phish_detail_url>
        <submission>
            <submission_time>2007-03-03T21:01:19+00:00</submission_time>
        </submission>
        <verification>
            <verified>yes</verified>
            <verification_time>2007-03-04T01:58:05+00:00</verification_time>
        </verification>
        <status>
            <online>yes</online>
        </status>
    </entry>
    """
    def __init__(self, output_csv_file):
        self.output_csv_file = output_csv_file
        self.entry_writer = csv.writer(output_csv_file, delimiter=' ',
                                       quotechar='|', quoting=csv.QUOTE_MINIMAL)

        self.url = u''
        self.phish_detail_url = u''

        self.inside_entry = False
        self.inside_URL = False
        self.url_count = 0
        self.inside_detail = False

    def start(self, name, attrs):
        # name parameters are strings (as sent by lxml) so we use strings here
        # to avoid the conversion
        if name == 'entry':
            self.inside_entry = True

        elif name == 'url':
            self.inside_URL = True
            # But when it sends the information in data(), it uses unicode
            self.url = u''

        elif name == 'phish_detail_url':
            self.inside_detail = True
            # But when it sends the information in data(), it uses unicode
            self.phish_detail_url = u''

        return

    def data(self, ch):
        if self.inside_URL:
            self.url += ch

        if self.inside_detail:
            self.phish_detail_url += ch

    def end(self, name):
        # name parameters are strings (as sent by lxml) so we use strings here
        # to avoid the conversion
        if name == 'phish_detail_url':
            self.inside_detail = False

        if name == 'url':
            self.inside_URL = False
            self.url_count += 1

        if name == 'entry':
            self.inside_entry = False
            #
            #    Now I dump the data to the CSV file
            #
            self.entry_writer.writerow([self.url, self.phish_detail_url])

    def close(self):
        self.output_csv_file.close()
        return self.url_count


def download():
    print('Downloading XML file...')
    subprocess.check_call(DOWNLOAD_CMD % (URL, XML_DB_FILE), shell=True)


def convert_xml_to_csv():
    """
    Had to do this because XML parsing with lxml is slow and memory intensive,
    see test_phishtank_xml_parsing.py for more information on this.

    :return: None, we store in CSV_DB_FILE
    """
    try:
        # According to different sources, xml.sax knows how to handle
        # encoding, so it will simply decode using the header:
        #
        # <?xml version="1.0" encoding="utf-8"?>
        phishtank_db_fd = file(XML_DB_FILE, 'r')
    except Exception, e:
        msg = 'Failed to open XML phishtank database: "%s", exception: "%s".'
        sys.exit(msg % (XML_DB_FILE, e))

    try:
        output_csv_file = file(CSV_DB_FILE, 'w')
    except Exception, e:
        msg = 'Failed to open CSV phishtank database: "%s", exception: "%s".'
        sys.exit(msg % (CSV_DB_FILE, e))

    pt_handler = PhishTankHandler(output_csv_file)
    parser = etree.HTMLParser(recover=True, target=pt_handler)

    print('Starting the phishtank XML conversion.')

    try:
        etree.parse(phishtank_db_fd, parser)
    except Exception, e:
        msg = 'XML parsing error in phishtank DB, exception: "%s".'
        sys.exit(msg % e)

    print('Finished XML conversion.')


if __name__ == '__main__':
    download()
    convert_xml_to_csv()
    os.unlink(XML_DB_FILE)

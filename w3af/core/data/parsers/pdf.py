"""
PDFParser.py

Copyright 2006 Andres Riancho

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
import StringIO
import re

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, process_pdf
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFSyntaxError

from w3af.core.data.parsers.baseparser import BaseParser
from w3af.core.data.parsers.url import URL


class PDFParser(BaseParser):
    """
    This class parses pdf documents to find emails and URLs. It's based on the
    pdfminer library.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, HTTPResponse):
        super(PDFParser, self).__init__(HTTPResponse)
        # Work !
        self._pre_parse(HTTPResponse.body)

    def _pre_parse(self, document):
        content_text = pdf_to_text(document)
        self._parse(content_text)

    def _parse(self, content_text):

        # Get the URLs using a regex
        for x in re.findall(BaseParser.URL_RE, content_text):
            try:
                self._re_urls.add(URL(x[0]))
            except ValueError:
                pass

        # Get the mail addys
        self._extract_emails(content_text)

    def get_references(self):
        """
        Searches for references on a page. w3af searches references in every html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.

        :return: Two lists, one with the parsed URLs, and one with the URLs that came out of a
        regular expression. The second list if less trustworthy.
        """
        return ([], list(self._re_urls))

    get_references_of_tag = get_forms = get_comments = \
        get_meta_redir = get_meta_tags = lambda *args, **kwds: []


def pdf_to_text(pdf_string):
    """
    :param pdf_string: The PDF file contents.
    :return: A string with the content of the PDF file.
    """
    rsrcmgr = PDFResourceManager(caching=True)
    laparams = LAParams()
    
    output = StringIO.StringIO()
    device = TextConverter(rsrcmgr, output, codec='utf-8', laparams=laparams)
    
    document_io = StringIO.StringIO(pdf_string)
    pagenos = set()
    try:
        process_pdf(rsrcmgr, device, document_io, pagenos, check_extractable=False)
    except PDFSyntaxError:
        return u''
    
    device.close()
    output.seek(0)
    return output.read().decode('utf-8')

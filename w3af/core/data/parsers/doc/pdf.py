"""
pdf.py

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

from pdfminer.converter import HTMLConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError

from w3af.core.data.parsers.doc.baseparser import BaseParser
from w3af.core.data.parsers.doc.sgml import SGMLParser
from w3af.core.data.parsers.utils.re_extract import ReExtract


class PDFParser(BaseParser):
    """
    This class parses pdf documents to find emails and URLs. It's based on the
    pdfminer library.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, http_response):
        super(PDFParser, self).__init__(http_response)

        self._re_urls = set()

    @staticmethod
    def can_parse(http_resp):
        """
        :param http_resp: A http response object that contains a document of
                          type HTML / PDF / WML / etc.

        :return: True if the document parameter is a string that contains a PDF
                 document.
        """
        if http_resp.content_type not in ('application/x-pdf', 'application/pdf'):
            return False

        document = http_resp.body

        # Safety check:
        if not document:
            return False

        # Some PDF files don't end with %%EOF, they end with
        # things like %%EOF\n , or %%EOF\r, or %%EOF\r\n.
        #
        # So... just to be sure I search in the last 12 characters.
        if document.startswith('%PDF-') and '%%EOF' in document[-12:]:
            return True

        return False

    def parse(self):
        """
        Get the URLs using a regex
        """
        doc_string = pdf_to_text(self.get_http_response().get_body())
        re_extract = ReExtract(doc_string, self._base_url, self._encoding)
        re_extract.parse()
        self._re_urls = re_extract.get_references()

    def get_clear_text_body(self):
        return pdf_to_text(self.get_http_response().get_body())

    def get_references(self):
        """
        Searches for references on a page. w3af searches references in every
        html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.

        :return: Two lists, one with the parsed URLs, and one with the URLs
                 that came out of a regular expression. The second list if less
                 trustworthy.
        """
        return [], list(self._re_urls)

    get_references_of_tag = get_forms = BaseParser._return_empty_list
    get_comments = BaseParser._return_empty_list
    get_meta_redir = get_meta_tags = get_emails = BaseParser._return_empty_list


def pdf_to_text(pdf_string):
    """
    :param pdf_string: The PDF file contents.
    :return: A string with the content of the PDF file.
    """
    rsrcmgr = PDFResourceManager(caching=True)
    output = StringIO.StringIO()

    # According to https://github.com/euske/pdfminer/issues/61 it is a good idea
    # to set laparams to None, which will speed-up parsing
    device = NoPageHTMLConverter(rsrcmgr, output, codec='utf-8',
                                 layoutmode='normal',
                                 laparams=None, imagewriter=None,
                                 showpageno=False)

    document_io = StringIO.StringIO(pdf_string)
    pagenos = set()
    try:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(document_io, pagenos, maxpages=0,
                                      caching=True, check_extractable=True):
            page.rotate = (page.rotate + 0) % 360
            interpreter.process_page(page)
    except PDFSyntaxError:
        return u''
    
    device.close()
    output.seek(0)
    output_str = output.read().decode('utf-8')
    return SGMLParser.ANY_TAG_MATCH.sub('', output_str)


class NoPageHTMLConverter(HTMLConverter):
    def write_footer(self):
        self.write('</body></html>\n')
        return

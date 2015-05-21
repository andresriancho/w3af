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
from w3af.core.data.parsers.doc.pdf import pdf_to_text
from w3af.plugins.grep.password_profiling_plugins.base_plugin import BasePwdProfilingPlugin


class pdf(BasePwdProfilingPlugin):
    """
    This plugin creates a map of possible passwords by reading pdf documents.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        BasePwdProfilingPlugin.__init__(self)

    def _get_pdf_content(self, document_str):
        """
        Iterate through all PDF pages and extract text
        
        :return: A list containing the words in the PDF
        """
        pdf_text = pdf_to_text(document_str)
        return pdf_text.split()

    def get_words(self, response):
        """
        Get words from the pdf document.

        :param response: In most common cases, an html. Could be almost
                         anything, if we are lucky, it's a PDF file.
        :return: A map of strings:repetitions.
        """
        res = None

        if response.content_type in ('application/x-pdf', 'application/pdf'):
            try:
                words = self._get_pdf_content(response.get_body())
            except:
                return None
            else:
                res = {}
                for w in words:
                    if w in res:
                        res[w] += 1
                    else:
                        res[w] = 1

        return res

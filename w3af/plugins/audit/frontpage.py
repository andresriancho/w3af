"""
frontpage.py

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
import w3af.core.controllers.output_manager as om

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.kb.vuln import Vuln

POST_BODY = ('method=put document:%s&service_name=&document=[document_name=%s'
             ';meta_info=[]]&put_option=overwrite&comment=&'
             'keep_checked_out=false\n')


class frontpage(AuditPlugin):
    """
    Tries to upload a file using frontpage extensions (author.dll).

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._already_tested = ScalableBloomFilter()
        self._author_url = None

    def _get_author_url(self):
        if self._author_url is not None:
            return self._author_url

        for info in kb.kb.get('frontpage_version', 'frontpage_version'):
            author_url = info.get('FPAuthorScriptUrl', None)
            if author_url is not None:
                self._author_url = author_url
                return self._author_url

        return None

    def audit(self, freq, orig_response, debugging_id):
        """
        Searches for file upload vulns using a POST to author.dll.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        # Only run if we have the author URL for this frontpage instance
        if self._get_author_url() is None:
            return

        # Only identify one vulnerability of this type
        if kb.kb.get(self, 'frontpage'):
            return

        domain_path = freq.get_url().get_domain_path()

        # Upload only once to each directory
        if domain_path in self._already_tested:
            return

        self._already_tested.add(domain_path)

        rand_file = rand_alpha(6) + '.html'
        upload_id = self._upload_file(domain_path, rand_file, debugging_id)
        self._verify_upload(domain_path, rand_file, upload_id, debugging_id)

    def _upload_file(self, domain_path, rand_file, debugging_id):
        """
        Upload the file using author.dll

        :param domain_path: http://localhost/f00/
        :param rand_file: <random>.html
        """
        # TODO: The frontpage version should be obtained from the information
        # saved in the kb by the infrastructure.frontpage_version plugin!
        #
        # The 4.0.2.4715 version should be dynamic!
        version = '4.0.2.4715'

        file_path = domain_path.get_path() + rand_file

        data = POST_BODY % (version, file_path)
        data += rand_file[::-1]
        data = smart_str_ignore(data)

        target_url = self._get_author_url()

        try:
            res = self._uri_opener.POST(target_url,
                                        data=data,
                                        debugging_id=debugging_id)
        except BaseFrameworkException, e:
            om.out.debug('Exception while uploading file using author.dll: %s' % e)
            return None
        else:
            if res.get_code() in [200]:
                om.out.debug('frontpage plugin seems to have successfully uploaded'
                             ' a file to the remote server.')
            return res.id

    def _verify_upload(self, domain_path, rand_file, upload_id, debugging_id):
        """
        Verify if the file was uploaded.

        :param domain_path: http://localhost/f00/
        :param rand_file: The filename that was (potentially) uploaded
        :param upload_id: The id of the POST request to author.dll
        """
        target_url = domain_path.url_join(rand_file)

        try:
            res = self._uri_opener.GET(target_url,
                                       cache=False,
                                       grep=False,
                                       debugging_id=debugging_id)
        except BaseFrameworkException, e:
            om.out.debug('Exception while verifying if the file that was uploaded'
                         'using author.dll was there: %s' % e)
        else:
            # The file we uploaded has the reversed filename as body
            if rand_file[::-1] not in res.get_body():
                return

            desc = ('An insecure configuration in the frontpage extensions'
                    ' allows unauthenticated users to upload files to the'
                    ' remote web server.')

            response_ids = [upload_id, res.id] if upload_id is not None else [res.id]

            v = Vuln('Insecure Frontpage extensions configuration', desc,
                     severity.HIGH, response_ids, self.get_name())

            v.set_url(target_url)
            v.set_method('POST')

            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
            self.kb_append(self, 'frontpage', v)

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['infrastructure.frontpage_version']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin audits the frontpage extension configuration by trying to
        upload a file to the remote server using the author.dll script provided
        by FrontPage.
        """

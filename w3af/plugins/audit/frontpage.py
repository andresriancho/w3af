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
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.kb.vuln import Vuln


class frontpage(AuditPlugin):
    """
    Tries to upload a file using frontpage extensions (author.dll).

    :author: Andres Riancho ((andres.riancho@gmail.com))
    """

    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._already_tested = ScalableBloomFilter()

    def audit(self, freq, orig_response):
        """
        Searches for file upload vulns using a POST to author.dll.

        :param freq: A FuzzableRequest
        """
        domain_path = freq.get_url().get_domain_path()

        if kb.kb.get(self, 'frontpage'):
            # Nothing to do, I have found vuln(s) and I should stop on first
            msg = 'Not verifying if I can upload files to: "%s" using'\
                  ' author.dll. Because I already found a vulnerability.'
            om.out.debug(msg)
            return

        # I haven't found any vulns yet, OR i'm trying to find every
        # directory where I can write a file.
        if domain_path not in self._already_tested:
            self._already_tested.add(domain_path)

            # Find a file that doesn't exist and then try to upload it
            for _ in xrange(3):
                rand_file = rand_alpha(5) + '.html'
                rand_path_file = domain_path.url_join(rand_file)
                res = self._uri_opener.GET(rand_path_file)
                if is_404(res):
                    upload_id = self._upload_file(domain_path, rand_file)
                    self._verify_upload(domain_path, rand_file, upload_id)
                    break
            else:
                msg = 'frontpage plugin failed to find a 404 page. This is'\
                      ' mostly because of an error in 404 page detection.'
                om.out.error(msg)

    def _upload_file(self, domain_path, rand_file):
        """
        Upload the file using author.dll

        :param domain_path: http://localhost/f00/
        :param rand_file: <random>.html
        """
        file_path = domain_path.get_path() + rand_file

        # TODO: The frontpage version should be obtained from the information saved in the kb
        # by the infrastructure.frontpage_version plugin!
        # The 4.0.2.4715 version should be dynamic!
        # The information is already saved in the crawl plugin in the line:
        # i['version'] = version_match.group(1)
        content = "method=put document:4.0.2.4715&service_name=&document=[document_name="
        content += file_path
        content += ";meta_info=[]]&put_option=overwrite&comment=&keep_checked_out=false"
        content += '\n'
        # The content of the file I'm uploading is the file name reversed
        content += rand_file[::-1]

        # TODO: The _vti_bin and _vti_aut directories should be PARSED from the _vti_inf file
        # inside the infrastructure.frontpage_version plugin, and then used here
        target_url = domain_path.url_join('_vti_bin/_vti_aut/author.dll')

        try:
            res = self._uri_opener.POST(target_url, data=content)
        except BaseFrameworkException, e:
            om.out.debug(
                'Exception while uploading file using author.dll: ' + str(e))
        else:
            if res.get_code() in [200]:
                msg = 'frontpage plugin seems to have successfully uploaded'\
                      ' a file to the remote server.'
                om.out.debug(msg)
            return res.id

        return 200

    def _verify_upload(self, domain_path, rand_file, upload_id):
        """
        Verify if the file was uploaded.

        :param domain_path: http://localhost/f00/
        :param rand_file: The filename that was supposingly uploaded
        :param upload_id: The id of the POST request to author.dll
        """
        target_url = domain_path.url_join(rand_file)

        try:
            res = self._uri_opener.GET(target_url)
        except BaseFrameworkException, e:
            msg = 'Exception while verifying if the file that was uploaded'\
                  'using author.dll was there: %s' % e
            om.out.debug(msg)
        else:
            # The file we uploaded has the reversed filename as body
            if res.get_body() == rand_file[::-1] and not is_404(res):
                desc = 'An insecure configuration in the frontpage extensions'\
                       ' allows unauthenticated users to upload files to the'\
                       ' remote web server.'
                
                v = Vuln('Insecure Frontpage extensions configuration', desc,
                         severity.HIGH, [upload_id, res.id], self.get_name())

                v.set_url(target_url)
                v.set_method('POST')
                
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
                self.kb_append(self, 'frontpage', v)
            else:
                msg = 'The file that was uploaded using the POST method is'\
                      ' not present on the remote web server at "%s".'
                om.out.debug(msg % target_url)

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before the
        current one.
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

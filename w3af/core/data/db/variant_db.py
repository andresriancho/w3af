"""
variant_db.py

Copyright 2012 Andres Riancho

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
import threading
import copy

from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.db.disk_dict import DiskDict

PARAMS_MAX_VARIANTS = 10
PATH_MAX_VARIANTS = 50


class VariantDB(object):

    def __init__(self, params_max_variants=PARAMS_MAX_VARIANTS,
                 path_max_variants=PATH_MAX_VARIANTS):
        self._disk_dict = DiskDict(table_prefix='variant_db')
        self._db_lock = threading.RLock()
        self.params_max_variants = params_max_variants
        self.path_max_variants = path_max_variants

    def append(self, reference):
        """
        Called when a new reference is found and we proved that new
        variants are still needed.

        :param reference: The reference (as a URL object) to add. This method
                          will "normalize" it before adding it to the internal
                          shelve.
        """
        clean_reference = self._clean_reference(reference)

        with self._db_lock:
            count = self._disk_dict.get(clean_reference, None)

            if count is not None:
                self._disk_dict[clean_reference] = count + 1
            else:
                self._disk_dict[clean_reference] = 1

    def append_fr(self, fuzzable_request):
        """
        See append()'s documentation
        """
        clean_fuzzable_request = self._clean_fuzzable_request(fuzzable_request)

        with self._db_lock:
            count = self._disk_dict.get(clean_fuzzable_request, None)

            if count is not None:
                self._disk_dict[clean_fuzzable_request] = count + 1
            else:
                self._disk_dict[clean_fuzzable_request] = 1

    def need_more_variants(self, reference):
        """
        :return: True if there are not enough variants associated with
        this reference in the DB.
        """
        dict_key = self._clean_reference(reference)
        return self._internal_need_more_check(dict_key, reference)

    def need_more_variants_for_fr(self, fuzzable_request):
        """
        :return: True if there are not enough variants associated with
        this reference in the DB.
        """
        dict_key = self._clean_fuzzable_request(fuzzable_request)
        url = fuzzable_request.get_uri()

        return self._internal_need_more_check(dict_key, url)

    def _internal_need_more_check(self, dict_key, url):
        # I believe this is atomic enough...
        count = self._disk_dict.get(dict_key, 0)
        has_qs = url.has_query_string()

        # When we're analyzing a path (without QS), we just need 1
        max_variants = self.params_max_variants if has_qs else 1

        if count >= max_variants:
            return False
        else:
            return True

    def _clean_reference(self, reference):
        """
        This method is VERY dependent on the are_variants method from
        core.data.request.variant_identification , make sure to remember that
        when changing stuff here or there.

        What this method does is to "normalize" any input reference string so
        that they can be compared very simply using string match.

        Since this is a reference (link) we'll prepend '(GET)-' to the result,
        which will help us add support for forms/fuzzable requests with
        '(POST)-' in the future.
        """
        res = '(GET)-'
        res += reference.get_domain_path().url_string.encode(DEFAULT_ENCODING)
        res += reference.get_file_name()

        if reference.has_query_string():
            res += '?' + self._clean_data_container(reference.querystring)

        return res

    def _clean_data_container(self, data_container):
        """
        A simplified/serialized version of the data container. Every data
        container is serialized to query string format, but we don't lose info
        since we just want to keep the keys and value types.

        This simplification allows us to store and compare complex data
        containers which might have unique ids (such as multipart).
        """
        result = []
        dc = copy.deepcopy(data_container)

        for key, value, path, setter in dc.iter_setters():

            if value.isdigit():
                _type = 'number'
            else:
                _type = 'string'

            result.append('%s=%s' % (key, _type))

        return '&'.join(result)

    def _clean_fuzzable_request(self, fuzzable_request):
        """
        Very similar to _clean_reference but we receive a fuzzable request
        instead. The output includes the HTTP method and any parameters which
        might be sent over HTTP post-data in the request are appended to the
        result as query string params.

        :param fuzzable_request: The fuzzable request instance to clean
        :return: See _clean_reference
        """
        res = '(%s)-' % fuzzable_request.get_method().upper()

        uri = fuzzable_request.get_uri()
        res += uri.get_domain_path() + uri.get_file_name()

        if uri.has_query_string():
            res += '?' + self._clean_data_container(uri.querystring)

        if fuzzable_request.get_raw_data():
            res += '!' + self._clean_data_container(fuzzable_request.get_raw_data())

        return res
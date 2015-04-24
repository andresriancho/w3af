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

#
# Limits the max number of variants we'll allow for URLs with the same path
# and parameter names. For example, these are two variants:
#
#       http://foo.com/abc/def?id=3&abc=bar
#       http://foo.com/abc/def?id=3&abc=spam
#
# For URLs which have the same path (/abc/def) and parameters
# (id=number&abc=string) we'll collect at most PARAMS_MAX_VARIANTS of those
#
PARAMS_MAX_VARIANTS = 10

#
# Limits the max number of variants we'll allow for URLs with the same path.
# For example, these are two "path variants":
#
#       http://foo.com/abc/def.htm
#       http://foo.com/abc/def.htm
#
# In this case we'll collect at most PATH_TOKEN URLs with the same htm extension
# inside the "abc" path.
#
# These two are also path variants, but in this case without a filename:
#
#       http://foo.com/abc/spam/
#       http://foo.com/abc/eggs/
#
# In this case we'll collect at most PATH_TOKEN URLs with different paths inside
# the "abc" path.
#
PATH_MAX_VARIANTS = 50

FILENAME_TOKEN = 'file-5692fef3f5dcd97'
PATH_TOKEN = 'path-0fb923a04c358a37c'


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
        dict_key = self._clean_reference(reference)
        self._internal_append(dict_key)

    def append_fr(self, fuzzable_request):
        """
        See append()'s documentation
        """
        dict_key = self._clean_fuzzable_request(fuzzable_request)
        self._internal_append(dict_key)

    def _internal_append(self, dict_key):
        with self._db_lock:
            count = self._disk_dict.get(dict_key, None)

            if count is not None:
                self._disk_dict[dict_key] = count + 1
            else:
                self._disk_dict[dict_key] = 1

    def need_more_variants(self, reference):
        """
        :return: True if there are not enough variants associated with
        this reference in the DB.
        """
        dict_key = self._clean_reference(reference)
        has_params = reference.has_query_string()
        return self._internal_need_more_check(dict_key, has_params)

    def need_more_variants_for_fr(self, fuzzable_request):
        """
        :return: True if there are not enough variants associated with
        this reference in the DB.
        """
        dict_key = self._clean_fuzzable_request(fuzzable_request)
        url = fuzzable_request.get_uri()
        has_params = url.has_query_string() or fuzzable_request.get_raw_data()

        return self._internal_need_more_check(dict_key, has_params)

    def _internal_need_more_check(self, dict_key, has_params):
        # I believe this is atomic enough...
        count = self._disk_dict.get(dict_key, 0)

        # Choose which max_variants to use
        if has_params:
            max_variants = self.params_max_variants
        else:
            max_variants = self.path_max_variants

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
        res += self._clean_url(reference)
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
        res += self._clean_url(fuzzable_request.get_uri())

        raw_data = fuzzable_request.get_raw_data()

        if raw_data:
            res += '!' + self._clean_data_container(raw_data)

        return res

    def _clean_url(self, url):
        """
        Clean a URL instance to string following these rules:
            * If there is a query string, leave the path+filename untouched and
              clean the query string only

            * Otherwise clean the path+filename

        :param url: URL instance
        :return: A "clean" representation of the URL
        """
        res = url.base_url().url_string.encode(DEFAULT_ENCODING)

        if url.has_query_string():
            res += url.get_path().encode(DEFAULT_ENCODING)[1:]
            res += '?' + self._clean_data_container(url.querystring)
        else:
            res += self._clean_path_filename(url)

        return res

    def _clean_path_filename(self, url):
        """
        Clean the path+filename following these rules:
            * If the URL has a filename, we'll keep the path untouched
            * If the filename has an extension, we keep it untouched
            * When cleaning the path we only touch the last child path

        :param url: The URL instance
        :return: A clean URL string
        """
        filename = url.get_file_name()
        path = url.get_path_without_file().encode(DEFAULT_ENCODING)

        if filename:
            res = path[1:]
            res += self._clean_filename(filename)
        else:
            res = self._clean_path(url.get_path().encode(DEFAULT_ENCODING))[1:]

        return res

    def _clean_filename(self, filename):
        """
        Clean the URL filename (if any)
        :param filename: The URL filename
        :return: A "clean" representation of the filename we can use to compare
        """
        # Clean the filename
        split_fname = filename.rsplit('.', 1)
        split_fname[0] = FILENAME_TOKEN

        # Create the filename again
        return '.'.join(split_fname)

    def _clean_path(self, path):
        """
        Clean the URL path (if any)
        :param path: The URL path
        :return: A "clean" representation of the path we can use to compare
        """
        split_path = path.rsplit('/', 2)[:-1]

        if len(split_path) == 2:
            # We have a path, clean the last part of it
            split_path[1] = PATH_TOKEN

        return '/'.join(split_path) + '/'

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
#       http://foo.com/abc/spam.htm
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


def clean_data_container(data_container):
    """
    A simplified/serialized version of the data container. Every data
    container is serialized to query string format, but we don't lose info
    since we just want to keep the keys and value types.

    This simplification allows us to store and compare complex data
    containers which might have unique ids (such as multipart).

    We replace the value by a number/string depending on the content, this
    allows us to quickly search and match two URLs which are similar
    """
    result = []

    for key, value, path, setter in data_container.iter_setters():

        if value.isdigit():
            _type = 'number'
        else:
            _type = 'string'

        result.append('%s=%s' % (key, _type))

    return '&'.join(result)


class VariantDB(object):
    """
    See the notes on PARAMS_MAX_VARIANTS and PATH_MAX_VARIANTS above. Also
    understand that we'll keep "dirty" versions of the references/fuzzable
    requests in order to be able to answer "False" to a call for
    need_more_variants in a situation like this:

        need_more_variants('http://foo.com/abc?id=32')      --> True
        append('http://foo.com/abc?id=32')
        need_more_variants('http://foo.com/abc?id=32')      --> False

    """
    def __init__(self, params_max_variants=PARAMS_MAX_VARIANTS,
                 path_max_variants=PATH_MAX_VARIANTS):
        self._disk_dict = DiskDict(table_prefix='variant_db')
        self._db_lock = threading.RLock()
        self.params_max_variants = params_max_variants
        self.path_max_variants = path_max_variants

    def append(self, fuzzable_request):
        """
        :return: True if we added a new fuzzable request variant to the DB,
                 False if no more variants are required for this fuzzable
                 request.
        """
        #
        # Is the fuzzable request already known to us? (exactly the same)
        #
        request_hash = fuzzable_request.get_request_hash()
        already_seen = self._disk_dict.get(request_hash, False)
        if already_seen:
            return False

        # Store it to avoid duplicated fuzzable requests in our framework
        self._disk_dict[request_hash] = True

        #
        # Do we need more variants of the fuzzable request? (similar match)
        #
        clean_dict_key = self._clean_fuzzable_request(fuzzable_request)

        with self._db_lock:

            count = self._disk_dict.get(clean_dict_key, None)

            if count is None:
                self._disk_dict[clean_dict_key] = 1
                return True

            # We've seen at least one fuzzable request with this pattern...
            url = fuzzable_request.get_uri()
            has_params = url.has_query_string() or fuzzable_request.get_raw_data()

            # Choose which max_variants to use
            if has_params:
                max_variants = self.params_max_variants
            else:
                max_variants = self.path_max_variants

            if count >= max_variants:
                return False

            else:
                self._disk_dict[clean_dict_key] = count + 1
                return True

    def _clean_fuzzable_request(self, fuzzable_request,
                                dc_handler=clean_data_container):
        """
        We receive a fuzzable request and output includes the HTTP method and
        any parameters which might be sent over HTTP post-data in the request
        are appended to the result as query string params.

        :param fuzzable_request: The fuzzable request instance to clean
        """
        res = '(%s)-' % fuzzable_request.get_method().upper()
        res += self._clean_url(fuzzable_request.get_uri(),
                               dc_handler=dc_handler)

        raw_data = fuzzable_request.get_raw_data()

        if raw_data:
            res += '!' + dc_handler(raw_data)

        return res

    def _clean_url(self, url, dc_handler=clean_data_container):
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
            res += '?' + dc_handler(url.querystring)
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

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

from w3af.core.data.db.disk_dict import DiskDict
from w3af.core.data.db.clean_dc import clean_fuzzable_request


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
        clean_dict_key = clean_fuzzable_request(fuzzable_request)

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



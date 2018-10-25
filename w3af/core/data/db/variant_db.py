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

import w3af.core.data.kb.config as cf
import w3af.core.controllers.output_manager as om

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.db.cached_disk_dict import CachedDiskDict
from w3af.core.data.db.clean_dc import (clean_fuzzable_request,
                                        clean_fuzzable_request_form)

#
# Limits the max number of variants we'll allow for URLs with the same path.
# For example, these are two "path variants":
#
#       http://foo.com/abc/def.htm
#       http://foo.com/abc/spam.htm
#
# In this case we'll collect at most PATH_MAX_VARIANTS URLs with the same htm
# extension inside the "abc" path.
#
# These two are also path variants, but in this case without a filename:
#
#       http://foo.com/abc/spam/
#       http://foo.com/abc/eggs/
#
# In this case we'll collect at most PATH_MAX_VARIANTS URLs with different
# paths inside the "abc" path.
#
PATH_MAX_VARIANTS = 50

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
PARAMS_MAX_VARIANTS = 15

#
# Limits the number variants for "the same form". A good example to understand this
# is a site which has many products, one for each URL using mod_rewrite:
#
#  * /product/description-for-prod-2/123/5
#  * /product/another-text-which-is-desc-for-prod-2/54/1
#
# And in each of those URLs there is a contact form which is submitted to the
# product URL.
#
# PATH_MAX_VARIANTS won't prevent these URLs from being crawled since it will
# only match the last URL part (5 and 1 in the examples above).
#
# PARAMS_MAX_VARIANTS won't match either since the path is not the same.
#
# For MAX_EQUAL_FORM_VARIANTS, forms are equal if:
#   * They have the same HTTP method
#   * They have the same HTTP encoding (json, url-encoded, etc.)
#   * They have the same parameter names and types
#   * They have at least two parameters
#
# https://github.com/andresriancho/w3af/issues/15970
#
MAX_EQUAL_FORM_VARIANTS = 5


class VariantDB(object):
    """
    See the notes on PARAMS_MAX_VARIANTS and PATH_MAX_VARIANTS above. Also
    understand that we'll keep "dirty" versions of the references/fuzzable
    requests in order to be able to answer "False" to a call for
    need_more_variants in a situation like this:

        >> need_more_variants('http://foo.com/abc?id=32')
        True

        >> append('http://foo.com/abc?id=32')
        True

        >> need_more_variants('http://foo.com/abc?id=32')
        False

    """
    HASH_IGNORE_HEADERS = ('referer',)
    TAG = '[variant_db]'

    MAX_IN_MEMORY = 50

    def __init__(self):
        self._variants = CachedDiskDict(max_in_memory=self.MAX_IN_MEMORY,
                                        table_prefix='variant_db')
        self._variants_eq = ScalableBloomFilter()
        self._variants_form = CachedDiskDict(max_in_memory=self.MAX_IN_MEMORY,
                                             table_prefix='variant_db_form')

        self.params_max_variants = cf.cf.get('params_max_variants')
        self.path_max_variants = cf.cf.get('path_max_variants')
        self.max_equal_form_variants = cf.cf.get('max_equal_form_variants')

        self._db_lock = threading.RLock()

    def cleanup(self):
        self._variants.cleanup()
        self._variants_form.cleanup()

    def append(self, fuzzable_request):
        """
        :return: True if we added a new fuzzable request variant to the DB,
                 False if NO more variants are required for this fuzzable
                 request.
        """
        with self._db_lock:
            if self._seen_exactly_the_same(fuzzable_request):
                return False

            if self._has_form(fuzzable_request):
                if not self._need_more_variants_for_form(fuzzable_request):
                    return False

            if not self._need_more_variants_for_uri(fuzzable_request):
                return False

            # Yes, please give me more variants of fuzzable_request
            return True

    def _log_return_false(self, fuzzable_request, reason):
        args = (reason, fuzzable_request)
        msg = 'VariantDB is returning False because of "%s" for "%s"'
        om.out.debug(msg % args)

    def _need_more_variants_for_uri(self, fuzzable_request):
        #
        # Do we need more variants for the fuzzable request? (similar match)
        # PARAMS_MAX_VARIANTS and PATH_MAX_VARIANTS
        #
        clean_dict_key = clean_fuzzable_request(fuzzable_request)
        count = self._variants.get(clean_dict_key, None)

        if count is None:
            self._variants[clean_dict_key] = 1
            return True

        # We've seen at least one fuzzable request with this pattern...
        url = fuzzable_request.get_uri()
        has_params = url.has_query_string() or fuzzable_request.get_raw_data()

        # Choose which max_variants to use
        if has_params:
            max_variants = self.params_max_variants
            max_variants_type = 'params'
        else:
            max_variants = self.path_max_variants
            max_variants_type = 'path'

        if count >= max_variants:
            _type = 'need_more_variants_for_uri(%s)' % max_variants_type
            self._log_return_false(fuzzable_request, _type)
            return False

        self._variants[clean_dict_key] = count + 1
        return True

    def _seen_exactly_the_same(self, fuzzable_request):
        #
        # Is the fuzzable request already known to us? (exactly the same)
        #
        request_hash = fuzzable_request.get_request_hash(self.HASH_IGNORE_HEADERS)
        if request_hash in self._variants_eq:
            return True

        # Store it to avoid duplicated fuzzable requests in our framework
        self._variants_eq.add(request_hash)

        self._log_return_false(fuzzable_request, 'seen_exactly_the_same')
        return False

    def _has_form(self, fuzzable_request):
        raw_data = fuzzable_request.get_raw_data()
        if raw_data and len(raw_data.get_param_names()) >= 2:
            return True

        return False

    def _need_more_variants_for_form(self, fuzzable_request):
        #
        # Do we need more variants for this form? (similar match)
        # MAX_EQUAL_FORM_VARIANTS
        #
        clean_dict_key_form = clean_fuzzable_request_form(fuzzable_request)
        count = self._variants_form.get(clean_dict_key_form, None)

        if count is None:
            self._variants_form[clean_dict_key_form] = 1
            return True

        if count >= self.max_equal_form_variants:
            self._log_return_false(fuzzable_request, 'need_more_variants_for_form')
            return False

        self._variants_form[clean_dict_key_form] = count + 1
        return True


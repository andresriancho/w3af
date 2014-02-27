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


class VariantDB(object):

    def __init__(self, max_variants=5):
        self._disk_dict = DiskDict()
        self._db_lock = threading.RLock()
        self.max_variants = max_variants

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

    def _clean_reference(self, reference):
        """
        This method is VERY dependent on the are_variants method from
        core.data.request.variant_identification , make sure to remember that
        when changing stuff here or there.

        What this method does is to "normalize" any input reference string so
        that they can be compared very simply using string match.

        """
        res = reference.get_domain_path() + reference.get_file_name()

        if reference.has_query_string():

            res += '?'
            qs = reference.querystring.copy()

            for key in qs:
                value_list = qs[key]
                for i, value in enumerate(value_list):
                    if value.isdigit():
                        qs[key][i] = 'number'
                    else:
                        qs[key][i] = 'string'

            res += str(qs)

        return res

    def need_more_variants(self, reference):
        """
        :return: True if there are not enough variants associated with
        this reference in the DB.
        """
        clean_reference = self._clean_reference(reference)
        # I believe this is atomic enough...
        count = self._disk_dict.get(clean_reference, 0)
        if count >= self.max_variants:
            return False
        else:
            return True

"""
info_set.py

Copyright 2015 Andres Riancho

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


class InfoSet(object):
    """
    This class represents a set of Info instances which are grouped together
    by the plugin developer.

    The inspiration for this class comes from vulnerabilities like cross-domain
    javascript where Info instances can be grouped by a common attribute such
    as the remote domain.

    This class allows us to represent this sentence:
        "The target application includes javascript source from the insecure
         domain foo.com, the URLs where this was found are <long list here>"

    Representing the same without this class would look like:
        "The target application includes javascript source from the insecure
         domain foo.com, the vulnerable URL is X"
        ...
        "The target application includes javascript source from the insecure
         domain foo.com, the vulnerable URL is N"

    First I thought about adding these features directly to the Info class, but
    it would have been harder to refactor the whole code and the end result
    would have been difficult to read.

    :see: https://github.com/andresriancho/w3af/issues/3955
    """
    def __init__(self, info_instances):
        if not len(info_instances):
            raise ValueError('Empty InfoSets are not allowed')

        if not isinstance(info_instances, list):
            raise TypeError('info_instances must be a list')

        self.infos = info_instances

    def add(self, info):
        self.infos.append(info)

    @property
    def first_info(self):
        return self.infos[0]

    def get_name(self):
        return self.first_info.get_name()

    def get_desc(self):
        return self.first_info.get_desc(with_id=False)

    def get_ids(self):
        all_ids = []
        for info in self.infos:
            all_ids.extend(info.get_id())
        return list(set(all_ids))

    def get_urls(self):
        all_urls = []
        for info in self.infos:
            all_urls.append(info.get_url())
        return list(set(all_urls))

    def get_uris(self):
        all_urls = []
        for info in self.infos:
            all_urls.append(info.get_uri())
        return list(set(all_urls))

    def get_plugin_name(self):
        return self.first_info.get_plugin_name()

    def get_uniq_id(self):
        """
        :return: A uniq identifier for this InfoSet instance. Since InfoSets are
                 persisted to SQLite and then re-generated for showing them to
                 the user, we can't use id() to know if two info objects are
                 the same or not.
        """
        concat_all = ''

        for info in self.infos:
            concat_all += info.get_uniq_id()

        return str(hash(concat_all))

    def get_attribute(self, attr_name):
        return self.first_info[attr_name]

    def __eq__(self, other):
        return self.get_uniq_id() == other.get_uniq_id()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<info_set instance for: "%s" - len: %s>' % (self.get_name(),
                                                            len(self.infos))

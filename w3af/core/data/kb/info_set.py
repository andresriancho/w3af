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

        self.infos = info_instances

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

    def get_plugin_name(self):
        return self.first_info.get_plugin_name()
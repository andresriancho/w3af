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
import uuid
import textwrap
import pprint

from jinja2 import StrictUndefined, Environment

import w3af.core.controllers.output_manager as om

from w3af.core.data.misc.encoding import smart_str, smart_unicode
from w3af.core.data.fuzzer.mutants.empty_mutant import EmptyMutant
from w3af.core.data.kb.info import Info
from w3af.core.controllers.misc.human_number import human_number


def sample_count(value):
    """
    Filter function used to render some InfoSets
    """
    len_uris = len(value)
    if len_uris == 1:
        return 'ten'
    if len_uris > 10:
        return 'ten'
    else:
        return human_number(len_uris)


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

    Note that:
        * It can hold both Info and Vuln instances.

        * It's going to use the first Info instance to retrieve important things
          such as severity, name, description, etc. Those should all be common
          to the set being hold here.

    :see: https://github.com/andresriancho/w3af/issues/3955
    """
    TEMPLATE = None
    ITAG = None

    MAX_INFO_INSTANCES = 30

    JINJA2_ENV = Environment(undefined=StrictUndefined,
                             trim_blocks=True,
                             lstrip_blocks=True)
    JINJA2_ENV.filters['human_number'] = human_number
    JINJA2_ENV.filters['sample_count'] = sample_count

    def __init__(self, info_instances):
        if not len(info_instances):
            raise ValueError('Empty InfoSets are not allowed')

        if not isinstance(info_instances, list):
            raise TypeError('info_instances must be a list')

        for info in info_instances:
            if not isinstance(info, Info):
                raise TypeError('info_instances list items must be Info sub'
                                '-classes, found "%r" instead' % info)

        self.infos = info_instances
        self._mutant = EmptyMutant()
        self._uniq_id = str(uuid.uuid4())

    def add(self, info):
        if len(self.infos) == self.MAX_INFO_INSTANCES:
            return False

        self.infos.append(info)
        return True

    def extend(self, infos):
        for i in infos:
            added = self.add(i)
            if not added:
                return False

        return True

    @property
    def first_info(self):
        return self.infos[0]

    def get_name(self):
        return self.first_info.get_name()

    def get_desc(self, with_id=False):
        if self.TEMPLATE is None:
            return self.first_info.get_desc(with_id=with_id)

        # We render the template using the information set data
        context = {'urls': [smart_unicode(u) for u in self.get_urls()],
                   'uris': [smart_unicode(u) for u in self.get_uris()],
                   'severity': self.get_severity(),
                   'name': self.get_name(),
                   'id': self.get_id(),
                   'method': smart_unicode(self.get_method()),
                   'plugin': self.get_plugin_name()}
        context.update(self.first_info.items())

        template_str = textwrap.dedent(self.TEMPLATE)
        template = self.JINJA2_ENV.from_string(template_str)

        try:
            rendered_desc = template.render(context)
        except UnicodeDecodeError:
            context_pp = pprint.pformat(context, indent=4)
            msg = ('UnicodeDecodeError found while rendering:\n\n%s\n\n'
                   'Using the following context:\n\n%r\n\n')
            om.out.debug(msg % (smart_str(template_str),
                                smart_str(context_pp)))
            raise

        return rendered_desc

    def get_id(self):
        """
        :return: All the ids associated with the instances stored in self.infos
        """
        all_ids = []
        for info in self.infos:
            all_ids.extend(info.get_id())
        return list(set(all_ids))

    def get_urls(self):
        """
        :return: All the URLs associated with the instances stored in self.infos
        """
        all_urls = []
        for info in self.infos:
            all_urls.append(info.get_url())
        return list(set(all_urls))

    def get_uris(self):
        """
        :return: All the URIs associated with the instances stored in self.infos
        """
        all_urls = []
        for info in self.infos:
            all_urls.append(info.get_uri())
        return list(set(all_urls))

    def get_mutant(self):
        """
        :return: An EmptyMutant instance. Note that there is no setter for
                 self._mutant, this is correct since we always want to return
                 an empty mutant

                 This method was added mostly to ease the initial implementation
                 and avoid major changes in output plugins which were already
                 handling Info instances.
        """
        return self._mutant

    def to_json(self):
        """
        :return: A dict containing all (*) the information from this InfoSet
                 instance, which can be serialized using python's json module.

                 (*) There is some loss of fidelity, make sure you read the
                     implementation before using it for anything other than
                     writing a report.
        """
        attributes = {}
        long_description = None
        fix_guidance = None
        fix_effort = None
        tags = None
        wasc_ids = None
        wasc_urls = None
        cwe_urls = None
        cwe_ids = None
        references = None
        owasp_top_10_references = None

        for k, v in self.first_info.iteritems():
            attributes[str(k)] = str(v)

        if self.has_db_details():
            long_description = self.get_long_description()
            fix_guidance = self.get_fix_guidance()
            fix_effort = self.get_fix_effort()
            tags = self.get_tags()
            wasc_ids = self.get_wasc_ids()
            cwe_ids = self.get_cwe_ids()

            # These require special treatment since they are iterators
            wasc_urls = [u for u in self.get_wasc_urls()]
            cwe_urls = [u for u in self.get_cwe_urls()]

            owasp_top_10_references = []
            for owasp_version, risk_id, ref in self.get_owasp_top_10_references():
                data = {'owasp_version': owasp_version,
                        'risk_id': risk_id,
                        'link': ref}
                owasp_top_10_references.append(data)

            references = []
            for ref in self.get_references():
                data = {'url': ref.url,
                        'title': ref.title}
                references.append(data)

        _data = {'url': str(self.get_url()),
                 'urls': [str(u) for u in self.get_urls()],
                 'var': self.get_token_name(),
                 'response_ids': self.get_id(),
                 'vulndb_id': self.get_vulndb_id(),
                 'name': self.get_name(),
                 'desc': self.get_desc(with_id=False),
                 'long_description': long_description,
                 'fix_guidance': fix_guidance,
                 'fix_effort': fix_effort,
                 'tags': tags,
                 'wasc_ids': wasc_ids,
                 'wasc_urls': wasc_urls,
                 'cwe_urls': cwe_urls,
                 'cwe_ids': cwe_ids,
                 'references': references,
                 'owasp_top_10_references': owasp_top_10_references,
                 'plugin_name': self.get_plugin_name(),
                 'severity': self.get_severity(),
                 'attributes': attributes,
                 'highlight': list(self.get_to_highlight()),
                 'uniq_id': self.get_uniq_id()}

        return _data

    def get_method(self):
        return self.first_info.get_method()

    def get_url(self):
        """
        :return: One of the potentially many URLs which are related to this
                 InfoSet. Use with care, usually as an example of a vulnerable
                 URL to show to the user.

                 For the complete list of URLs see get_urls()
        """
        return self.first_info.get_url()

    def get_uri(self):
        """
        :return: One of the potentially many URIs which are related to this
                 InfoSet. Use with care, usually as an example of a vulnerable
                 URL to show to the user.

                 For the complete list of URLs see get_uris()
        """
        return self.first_info.get_uri()

    def get_plugin_name(self):
        return self.first_info.get_plugin_name()

    def get_to_highlight(self):
        return self.first_info.get_to_highlight()

    def get_token_name(self):
        """
        :return: None, since the Info objects stored in this InfoSet might have
                 completely different values for it, and it's not possible to
                 return one that represents all.
        """
        return None

    def get_token(self):
        """
        :return: None, since the Info objects stored in this InfoSet might have
                 completely different values for it, and it's not possible to
                 return one that represents all.
        """
        return None

    def get_uniq_id(self):
        """
        :return: A uniq identifier for this InfoSet instance. Since InfoSets are
                 persisted to SQLite and then re-generated for showing them to
                 the user, we can't use id() to know if two info objects are
                 the same or not.
        """
        return self._uniq_id

    def get_attribute(self, attr_name):
        return self.first_info.get(attr_name, None)

    def __getitem__(self, item):
        """
        Does the same as get_attribute but with a different signature, had to
        add it to make the InfoSet behave more like an Info
        """
        return self.first_info[item]

    def get_severity(self):
        return self.first_info.get_severity()

    def match(self, info):
        """
        When an Info sub-class wants to know if it should be added to an InfoSet
        it calls InfoSet.match(Info).

        In case it's not clear, this is the method which controls how Infos are
        grouped in InfoSets.

        :param info: The Info instance which wants to know if it matches this
                     InfoSet

        :return: True if they do match
        """
        assert self.ITAG is not None, 'Need to specify unique id tag'

        return (info.get(self.ITAG, None) is not None and
                info.get(self.ITAG) == self.get_attribute(self.ITAG)
                and info.get_name() == self.get_name())

    def has_db_details(self):
        return self.first_info.has_db_details()

    def get_vulndb_id(self):
        return self.first_info.get_vulndb_id()

    def get_long_description(self):
        return self.first_info.get_long_description()

    def get_fix_guidance(self):
        return self.first_info.get_fix_guidance()

    def get_fix_effort(self):
        return self.first_info.get_fix_effort()

    def get_tags(self):
        return self.first_info.get_tags()

    def get_wasc_ids(self):
        return self.first_info.get_wasc_ids()

    def get_wasc_urls(self):
        return self.first_info.get_wasc_urls()

    def get_cwe_urls(self):
        return self.first_info.get_cwe_urls()

    def get_cwe_ids(self):
        return self.first_info.get_cwe_ids()

    def get_references(self):
        return self.first_info.get_references()

    def get_owasp_top_10_references(self):
        return self.first_info.get_owasp_top_10_references()

    def get_vuln_info_from_db(self):
        return self.first_info.get_vuln_info_from_db()

    def __eq__(self, other):
        self_json = self.to_json()
        self_json.pop('uniq_id')

        other_json = self.to_json()
        other_json.pop('uniq_id')

        return self_json == other_json

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<info_set instance for: "%s" - len: %s>' % (self.get_name(),
                                                            len(self.infos))

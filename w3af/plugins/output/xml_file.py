"""
xml_file.py

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
import os
import gzip
import time
import base64
import jinja2

from jinja2 import Environment, select_autoescape, FileSystemLoader, StrictUndefined

import w3af.core.data.kb.config as cf
import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.controllers.misc import get_w3af_version
from w3af.core.controllers.exceptions import BaseFrameworkException, DBException
from w3af.core.controllers.misc.temp_dir import get_temp_dir
from w3af.core.data.db.history import HistoryItem
from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import OUTPUT_FILE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.constants.encodings import DEFAULT_ENCODING

TIME_FORMAT = '%a %b %d %H:%M:%S %Y'

TEMPLATE_ROOT = os.path.join(ROOT_PATH, 'plugins/output/xml_file/')


class xml_file(OutputPlugin):
    """
    Print all messages to a xml file.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    XML_OUTPUT_VERSION = '2.1'

    def __init__(self):
        OutputPlugin.__init__(self)

        # These attributes hold the file pointers
        self._file = None

        # User configured parameters
        self._file_name = '~/report.xml'
        self._timestamp = str(int(time.time()))
        self._long_timestamp = str(time.strftime(TIME_FORMAT, time.localtime()))

        # Set defaults for scan metadata
        self._plugins_dict = {}
        self._options_dict = {}

        # Keep internal state
        self._is_working = False

        # List with additional xml elements
        self._errors = DiskList()

    def _open_file(self):
        self._file_name = os.path.expanduser(self._file_name)
        try:
            self._file = open(self._file_name, 'wb')
        except IOError, io:
            msg = 'Can\'t open report file "%s" for writing, error: %s.'
            args = (os.path.abspath(self._file_name), io.strerror)
            raise BaseFrameworkException(msg % args)
        except Exception, e:
            msg = 'Can\'t open report file "%s" for writing, error: %s.'
            args = (os.path.abspath(self._file_name), e)
            raise BaseFrameworkException(msg % args)

    def do_nothing(self, *args, **kwds):
        pass

    debug = information = vulnerability = console = log_http = do_nothing

    def error(self, message, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for error messages.
        """
        #
        # Note that while the call to "get_caller()" is costly, it only happens
        # when an error occurs, so it shouldn't impact performance
        #
        error_data = (message, self.get_caller())
        self._errors.append(error_data)

    def set_options(self, option_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using
        get_options()

        This method MUST be implemented on every plugin.

        :return: No value is returned.
        """
        self._file_name = option_list['output_file'].get_value()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Output file name where to write the XML data'
        o = opt_factory('output_file', self._file_name, d, OUTPUT_FILE)
        ol.add(o)

        return ol

    def log_enabled_plugins(self, plugins_dict, options_dict):
        """
        This method is called from the output manager object. This method should
        take an action for the enabled plugins and their configuration. Usually,
        write the info to a file or print it somewhere.

        :param plugins_dict: A dict with all the plugin types and the enabled
                             plugins for that type of plugin.
        :param options_dict: A dict with the options for every plugin.
        """
        # See doc for _log_enabled_plugins_to_xml to understand why we don't write
        # to the XML just now.
        self._plugins_dict = plugins_dict
        self._options_dict = options_dict

    def end(self):
        """
        This method is called when the scan has finished.
        """
        self.flush()

        # Free some memory and disk space
        self._plugins_dict = {}
        self._options_dict = {}
        self._errors.cleanup()

    def flush(self):
        """
        Write the XML to the output file
        :return: None
        """
        # If for some reason the xml_file plugin takes a lot of time to run
        # and the output manager calls flush() for a second time while we're
        # still running the first call, just ignore.
        if self._is_working:
            return

        self._is_working = True

        context = dotdict({})

        try:
            self._add_root_info_to_context(context)
            self._add_scan_info_to_context(context)
            self._add_findings_to_context(context)
            self._add_errors_to_context(context)

            self._write_context_to_file(context)
        finally:
            self._is_working = False

    def _add_root_info_to_context(self, context):
        context.start_timestamp = self._timestamp
        context.start_time_long = self._long_timestamp
        context.xml_version = self.XML_OUTPUT_VERSION
        context.w3af_version = get_w3af_version.get_w3af_version()

    def _add_scan_info_to_context(self, context):
        scan_targets = ','.join([t.url_string for t in cf.cf.get('targets')])

        scan_info = ScanInfo(scan_targets, self._plugins_dict, self._options_dict)
        context.scan_info = scan_info.to_string()

    def _add_errors_to_context(self, context):
        context.errors = self._errors

    def _add_findings_to_context(self, context):
        context.findings = (Finding(i).to_string() for i in kb.kb.get_all_findings())

    def _write_context_to_file(self, context):
        """
        Write xml report to the file by rendering the context
        :return: None
        """
        env_config = {'undefined': StrictUndefined,
                      'trim_blocks': True,
                      'autoescape': select_autoescape(['xml']),
                      'lstrip_blocks': True}

        jinja2_env = Environment(**env_config)
        jinja2_env.loader = FileSystemLoader(TEMPLATE_ROOT)
        jinja2_env.filters['escape_attr_val'] = jinja2_attr_value_escape_filter

        template = jinja2_env.get_template('root.tpl')

        # We use streaming as explained here:
        #
        # http://flask.pocoo.org/docs/0.12/patterns/streaming/
        #
        # To prevent having the whole XML in memory
        report_stream = template.stream(context)
        report_stream.enable_buffering(5)

        self._open_file()

        # Write each report section to the output file
        for report_section in report_stream:
            self._file.write(report_section.encode(DEFAULT_ENCODING))

        self._file.close()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin creates an XML file containing all of w3af's findings.

        One configurable parameter exists:
            - output_file

        When using the contents of the XML file it's important to notice that
        the long-description and fix-guidance tags contain text in markdown
        format.

        The generated XML file validates against the report.xsd file which is
        distributed with the plugin.
        """


class XMLNode(object):

    TEMPLATE = None
    TEMPLATE_INST = None

    def get_template(self, template_name):
        if self.TEMPLATE_INST:
            return self.TEMPLATE_INST

        env_config = {'undefined': StrictUndefined,
                      'trim_blocks': True,
                      'autoescape': select_autoescape(['xml']),
                      'lstrip_blocks': True}

        jinja2_env = Environment(**env_config)
        jinja2_env.loader = FileSystemLoader(TEMPLATE_ROOT)
        jinja2_env.filters['escape_attr_val'] = jinja2_attr_value_escape_filter

        self.TEMPLATE_INST = jinja2_env.get_template(template_name)
        return self.TEMPLATE_INST


class CachedXMLNode(XMLNode):

    COMPRESSION_LEVEL = 2

    def get_cache_key(self):
        raise NotImplementedError

    def get_node_from_cache(self):
        filename = os.path.join(get_temp_dir(), self.get_cache_key())
        node = gzip.open(filename, 'rb', compresslevel=self.COMPRESSION_LEVEL).read()
        return node.decode('utf-8')

    def save_node_to_cache(self, node):
        filename = os.path.join(get_temp_dir(), self.get_cache_key())
        node = node.encode('utf-8')
        gzip.open(filename, 'wb', compresslevel=self.COMPRESSION_LEVEL).write(node)

    def is_in_cache(self):
        filename = os.path.join(get_temp_dir(), self.get_cache_key())
        return os.path.exists(filename)


class HTTPTransaction(CachedXMLNode):

    TEMPLATE = 'http_transaction.tpl'

    def __init__(self, _id):
        """
        :param _id: The HTTP request / response ID from w3af. This is is used to query
                    the history and get the information. In most cases we'll get the
                    information from the cache and return the XML node.

        """
        self._id = _id

    def get_cache_key(self):
        return 'http-transaction-%s.data' % self._id

    def to_string(self):
        """
        :return: An xml node (as a string) representing the HTTP request / response.

        <http-transaction id="...">
            <http-request>
                <status></status>
                <headers>
                    <header>
                        <field></field>
                        <content></content>
                    </header>
                </headers>
                <body content-encoding="base64"></body>
            </http-request>

            <http-response>
                <status></status>
                <headers>
                    <header>
                        <field></field>
                        <content></content>
                    </header>
                </headers>
                <body content-encoding="base64"></body>
            </http-response>
        </http-transaction>

        One of the differences this class has with the previous implementation is
        that the body is always encoded, no matter the content-type. This helps
        prevent encoding issues.
        """
        # Get the data from the cache
        if self.is_in_cache():
            return self.get_node_from_cache()

        # HistoryItem to get requests/responses
        req_history = HistoryItem()

        # This might raise a DBException in some cases (which I still
        # need to identify and fix). When an exception is raised here
        # the caller needs to handle it by ignoring this part of the
        # HTTP transaction
        details = req_history.read(self._id)

        request = details.request
        response = details.response

        data = request.get_data() or ''
        b64_encoded_request_body = base64.encodestring(smart_str_ignore(data))

        body = response.get_body() or ''
        b64_encoded_response_body = base64.encodestring(smart_str_ignore(body))

        context = {'id': self._id,
                   'request': {'status': request.get_request_line().strip(),
                               'headers': request.get_headers(),
                               'body': b64_encoded_request_body},
                   'response': {'status': response.get_status_line().strip(),
                                'headers': response.get_headers(),
                                'body': b64_encoded_response_body}}

        context = dotdict(context)

        template = self.get_template(self.TEMPLATE)
        transaction = template.render(context)
        self.save_node_to_cache(transaction)

        return transaction


class ScanInfo(CachedXMLNode):
    TEMPLATE = 'scan_info.tpl'

    def __init__(self, scan_target, plugins_dict, options_dict):
        """
        Represents the w3af scan information

        :param plugins_dict: The plugins which were enabled
        :param options_dict: The options for each plugin
        """
        self._scan_target = scan_target
        self._plugins_dict = plugins_dict
        self._options_dict = options_dict

    def get_cache_key(self):
        return 'scan-info.data'

    def to_string(self):
        # Get the data from the cache
        if self.is_in_cache():
            return self.get_node_from_cache()

        context = {'enabled_plugins': self._plugins_dict,
                   'plugin_options': self._options_dict,
                   'scan_target': self._scan_target}

        template = self.get_template(self.TEMPLATE)
        transaction = template.render(context)
        self.save_node_to_cache(transaction)

        return transaction


class Finding(XMLNode):
    TEMPLATE = 'finding.tpl'

    def __init__(self, info):
        """
        Represents a finding in the w3af framework, which will be serialized
        as an XML node
        """
        self._info = info

    def to_string(self):
        info = self._info
        context = dotdict({})

        context.id_list = info.get_id()
        context.http_method = info.get_method()
        context.name = info.get_name()
        context.plugin_name = info.get_plugin_name()
        context.severity = info.get_severity()
        context.url = info.get_url()
        context.var = info.get_token_name()
        context.description = info.get_desc(with_id=False)

        #
        #   Add the information from the vuln db (if any)
        #
        context.long_description = None

        if info.has_db_details():
            context.long_description = info.get_long_description()
            context.fix_guidance = info.get_fix_guidance()
            context.fix_effort = info.get_fix_effort()
            context.references = info.get_references()

        #
        #   Add the HTTP transactions
        #
        context.http_transactions = []
        for transaction in info.get_id():
            try:
                xml = HTTPTransaction(transaction).to_string()
            except DBException:
                msg = 'Failed to retrieve request with id %s from DB.'
                print(msg % transaction)
                continue
            else:
                context.http_transactions.append(xml)

        template = self.get_template(self.TEMPLATE)
        transaction = template.render(context)

        return transaction


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


ATTR_VALUE_ESCAPES = {
    '"': '&quot;',
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;'
}


def jinja2_attr_value_escape_filter(value):
    if not isinstance(value, basestring):
        return value

    retval = []

    for letter in value:
        if letter in ATTR_VALUE_ESCAPES:
            retval.append(ATTR_VALUE_ESCAPES[letter])
        else:
            retval.append(letter)

    return jinja2.Markup(''.join(retval))

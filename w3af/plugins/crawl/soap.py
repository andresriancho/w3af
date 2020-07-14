import contextlib
import sys
from cStringIO import StringIO

import zeep
from zeep.exceptions import XMLSyntaxError

import w3af.core.data.kb.knowledge_base as kb
from w3af.core.controllers import output_manager
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.data.kb.info import Info
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options import option_types
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest


@contextlib.contextmanager
def redirect_stdout(new_stdout):
    old_stdout = sys.stdout
    try:
        sys.stdout = new_stdout
        yield
    finally:
        sys.stdout = old_stdout


class soap(CrawlPlugin):
    def __init__(self):
        super(soap, self).__init__()
        self._is_first_run = True
        self.service_url = ''
        self.verbosity_level = 0

    def crawl(self, fuzzable_request, debugging_id):
        url_to_crawl = fuzzable_request.get_url().url_string
        if self._is_first_run:
            self._is_first_run = False
            url_to_crawl = self.service_url
        urls_discovered = self.parse_wsdl(url_to_crawl)
        self._save_results(urls_discovered)

    def get_options(self):
        option_list = super(soap, self).get_options()

        option = opt_factory(
            'service_url',
            default_value=self.service_url,
            desc='URL pointing to WSDL specification',
            help=(
                "Web applications which are based on SOAP protocol exposes their"
                "specification in WSDL format. The WSDL specification gives us info"
                "what methods are available and how to use them. It's a road map"
                "for SOAP client."
            ),
            _type=option_types.STRING,
        )
        option_list.add(option)

        option = opt_factory(
            'verbosity_level',
            default_value=self.verbosity_level,
            desc='Verbosity level',
            help=(
                "You can specify number as below:\n"
                "0: No verbosity. Plugin will only detect new URLs.\n"
                "1: Plugin will detect URLs and it will add info to knowledge base"
                "about possible operations on given URL.\n"
                "2: Plugin will detect URLs and dump all info from WSDL spec."
            ),
            _type=option_types.INT,
        )
        option_list.add(option)

        return option_list

    def set_options(self, options_list):
        super(soap, self).set_options(options_list)
        self.service_url = options_list['service_url'].get_value()
        self.verbosity_level = options_list['verbosity_level'].get_value()

    def get_long_desc(self):
        return (
            "This plugin parses SOAP according to provided WSDL specification."
            "User should specify the WSDL URL."
        )

    def parse_wsdl(self, wsdl_url):
        """
        :param str wsdl_url: string address pointing to wsdl spec.
        :return list: all urls discovered when parsing the wsdl.
        """
        discovered_urls = set()
        try:
            wsdl_client = zeep.Client(wsdl_url)
        except XMLSyntaxError:
            exception_description = (
                "The result of url: {} seems not to be valid XML.".format(wsdl_url)
            )
            self._report_parsing_failure(exception_description, wsdl_url)
            return discovered_urls

        if not wsdl_client.wsdl.services:
            exception_description = (
                "The result of url: {} seems not to be valid WSDL".format(wsdl_url)
            )
            self._report_parsing_failure(exception_description, wsdl_url)
            return discovered_urls

        if self.verbosity_level == 2:
            dump_capturer = StringIO()
            with redirect_stdout(dump_capturer):
                wsdl_client.wsdl.dump()
            self._report_wsdl_dump(dump_capturer.getvalue())

        for service_name in wsdl_client.wsdl.services:
            service = wsdl_client.bind(service_name)
            ports = wsdl_client.wsdl.services[service_name].ports
            for _, port in ports.items():
                operation_url = port.binding_options['address']
                if self.verbosity_level == 1 and operation_url not in discovered_urls:
                    self._report_all_operations_for_url(service, operation_url)
                discovered_urls.add(operation_url)
        return discovered_urls

    def _save_results(self, urls_discovered):
        for url in urls_discovered:
            fuzzable_request = FuzzableRequest(URL(url))
            self.output_queue.put(fuzzable_request)

    def _report_parsing_failure(self, description, url):
        exception_info = Info(
            name='Failed to parse WSDL in SOAP plugin',
            desc=description,
            response_ids=[],
            plugin_name=self.get_name(),
        )
        exception_info.set_url(URL(url))
        kb.kb.append(self, 'soap', exception_info)
        if url == self.service_url:
            output_manager.out.error(exception_info.get_desc())
        else:
            output_manager.out.information(exception_info.get_desc())

    def _report_all_operations_for_url(self, service, url):
        operation_names_for_description = "".join(
            ["- {}\n".format(operation[0]) for operation in service]
        )
        description = (
            "Following operations discovered for url {}: \n"
            "{}"
        ).format(url, operation_names_for_description)
        operations_info = Info(
            name='SOAP operations discovered',
            desc=description,
            response_ids=[],
            plugin_name=self.get_name(),
        )
        kb.kb.append(self, 'soap', operations_info)

    def _report_wsdl_dump(self, dump_string):
        dump_info = Info(
            name='SOAP details',
            desc=dump_string,
            response_ids=[],
            plugin_name=self.get_name(),
        )
        kb.kb.append(self, 'soap', dump_info)

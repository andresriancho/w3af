import pytest

from w3af.plugins.crawl.soap import soap


class TestSoap:
    def setup_class(self):
        self.plugin_options = {
            'service_url': 'http://example.com/webservice.asmx?WSDL',
        }

    def test_soap_plugin_finds_all_endpoints(
        self,
        plugin_runner,
        knowledge_base,
        soap_domain,
    ):
        plugin_runner.run_plugin(
            soap,
            plugin_config=self.plugin_options,
            mock_domain=soap_domain,
        )
        urls_discovered = [url for url in knowledge_base.get_all_known_urls()]
        assert len(urls_discovered) == 1

    def test_soap_plugin_adds_info_to_knowledge_base_if_it_cant_parse_xml(
        self,
        plugin_runner,
        knowledge_base,
        soap_domain,
    ):
        plugin_runner.run_plugin(
            soap,
            plugin_config=self.plugin_options,
            mock_domain=soap_domain,
        )
        result = knowledge_base.dump()
        assert result.get('soap') and 'XML' in str(result['soap']['soap'])

    def test_soap_plugin_will_report_if_it_gets_wrong_wsdl_spec(
        self,
        plugin_runner,
        knowledge_base,
        soap_domain,
    ):
        soap_domain['/webservice.asmx?WSDL'] = '<div>some strange things</div>'
        plugin_runner.run_plugin(
            soap,
            plugin_config=self.plugin_options,
            mock_domain=soap_domain,
        )
        result = knowledge_base.dump()
        assert result.get('soap') and 'WSDL' in str(result['soap']['soap'][0])
        urls_discovered = [url for url in knowledge_base.get_all_known_urls()]
        assert not urls_discovered

    def test_soap_plugin_wont_work_without_specified_service_url(
        self,
        plugin_runner,
    ):
        with pytest.raises(ValueError):
            plugin_runner.run_plugin(soap)

    def test_soap_plugin_will_handle_wsdl_if_it_comes_as_fuzzable_request_not_service_url(
        self,
        plugin_runner,
        soap_domain,
        knowledge_base,
    ):
        # let's swap soap_domain URLs, so crawler's target will be wrong, but
        # global target will be right
        soap_domain['/'] = soap_domain['/webservice.asmx?WSDL']
        soap_domain['/webservice.asmx?WSDL'] = '<div>wrong wsdl</div>'
        plugin_runner.run_plugin(
            soap,
            plugin_config=self.plugin_options,
            mock_domain=soap_domain,
        )
        urls_discovered = [url for url in knowledge_base.get_all_known_urls()]
        assert len(urls_discovered) == 1

    def test_soap_can_parse_wsdl_with_both_kinds_of_syntax(
            self,
            plugin_runner,
            soap_domain,
            soap_domain_2,
            knowledge_base,
    ):
        plugin_runner.run_plugin(
            soap,
            plugin_config=self.plugin_options,
            mock_domain=soap_domain,
        )
        urls_discovered = [url for url in knowledge_base.get_all_known_urls()]

        knowledge_base.cleanup()

        assert len(urls_discovered) == 1
        plugin_runner.run_plugin(
            soap,
            plugin_config=self.plugin_options,
            mock_domain=soap_domain_2,
        )
        urls_discovered = [url for url in knowledge_base.get_all_known_urls()]
        assert len(urls_discovered) == 1

    def test_soap_plugin_verbosity_works(self, plugin_runner, soap_domain, knowledge_base):
        self.plugin_options['verbosity_level'] = 1
        plugin_runner.run_plugin(
            soap,
            plugin_config=self.plugin_options,
            mock_domain=soap_domain,
        )
        result = knowledge_base.dump()
        verbosity_infos = [
            info
            for info in result['soap']['soap']
            if 'Following operations discovered for url' in str(info)
        ]
        assert len(verbosity_infos) == 1
        assert all(
            word
            in str(verbosity_infos[0])
            for word in ['NumberToDollars', 'NumberToWords']
        )

        self.plugin_options['verbosity_level'] = 2
        plugin_runner.run_plugin(
            soap,
            plugin_config=self.plugin_options,
            mock_domain=soap_domain,
        )
        result = knowledge_base.dump()
        assert result['soap']['soap']
        assert any([
            'Service: NumberConversion' in str(info) and
            'NumberToDollars' in str(info) and
            'NumberToWords' in str(info)
            for info in result['soap']['soap']
        ])

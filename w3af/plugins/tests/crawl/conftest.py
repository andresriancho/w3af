import pytest


@pytest.fixture
def soap_domain():
    with open('w3af/plugins/tests/crawl/soap/wsdl_example.xml', 'r') as file_:
        return {
            '/': 'example.com',
            '/webservice.asmx': '<div>some strange things</div>',
            '/webservice.asmx?WSDL': file_.read(),
        }


@pytest.fixture
def soap_domain_2():
    with open('w3af/plugins/tests/crawl/soap/wsdl_example_2.xml', 'r') as file_:
        return {
            '/': 'example.com',
            '/webservice.asmx': '<div>some strange things</div>',
            '/webservice.asmx?WSDL': file_.read(),
        }

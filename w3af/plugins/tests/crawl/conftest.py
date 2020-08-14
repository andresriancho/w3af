import pytest


@pytest.fixture
def soap_domain():
    with open('w3af/plugins/tests/crawl/soap/wsdl_example.xml', 'r') as file_:
        wsdl_content = file_.read()
    with open('w3af/plugins/tests/crawl/soap/soap_service_example.html', 'r') as file_:
        soap_service_content = file_.read()

    return {
        '/': (
            '<a href="http://example.com/webservice.asmx">wrong</a>"'
            '<a href="http://example.com/webservice.asmx?WSDL">good</a>'
        ),
        '/webservice.asmx': '<div>some strange things</div>',
        '/webservice.asmx?WSDL=': wsdl_content,
        '/webservicesserver/NumberConversion.wso': soap_service_content,
    }


@pytest.fixture
def soap_domain_2():
    with open('w3af/plugins/tests/crawl/soap/wsdl_example.xml', 'r') as file_:
        wsdl_content = file_.read()
    with open('w3af/plugins/tests/crawl/soap/soap_service_example.html', 'r') as file_:
        soap_service_content = file_.read()

    return {
        '/': 'example.com',
        '/webservice.asmx': '<div>some strange things</div>',
        '/webservice.asmx?WSDL=': wsdl_content,
        '/webservicesserver/NumberConversion.wso': soap_service_content,
    }

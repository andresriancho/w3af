import pytest
from mock import MagicMock, call, patch

from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.plugins.tests.plugin_testing_tools import NetworkPatcher, patch_network

"""
Unit tests for plugin_testing_tools.py
"""


@pytest.fixture
def network_patcher():
    return NetworkPatcher()


class TestNetworkPatcher:
    def setup_class(self):
        self.url_opener = ExtendedUrllib()

    def test_it_works_and_hits_mocked_server(self):
        mocked_server = MagicMock()
        network_patcher = NetworkPatcher(mocked_server=mocked_server)
        with network_patcher:
            self.url_opener.GET(MagicMock())
        assert call.mock_GET in mocked_server.method_calls

    def test_it_stops_all_patchers(self, network_patcher):
        with network_patcher:
            pass
        for patcher in network_patcher.patchers:
            with pytest.raises(RuntimeError):
                patcher.stop()

    def test_it_starts_all_patchers(self, network_patcher):
        """
        This test additionally tests if __exit__ can handle already stopped patchers
        """
        with network_patcher:
            for patcher in network_patcher.patchers:
                patcher.stop()  # no error here

    def test_with_as_works(self):
        with NetworkPatcher() as network_patcher:
            assert isinstance(network_patcher, NetworkPatcher)

    def test_it_works_as_a_decorator(self):
        mocked_server = MagicMock()
        network_patcher_from_class = (
            lambda *args, **kwargs: NetworkPatcher(mocked_server=mocked_server)
        )
        with patch(
            'w3af.plugins.tests.plugin_testing_tools.NetworkPatcher',
            network_patcher_from_class,
        ):
            @patch_network
            def decorated_function():
                self.url_opener.GET(MagicMock())
            decorated_function()
        assert mocked_server.mock_GET.called

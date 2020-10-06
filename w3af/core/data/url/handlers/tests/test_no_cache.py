from mock import MagicMock

from w3af.core.data.url.handlers.cache_backend.no_chache import NoCachedResponse


def test_it_implements_all_static_methods_required():
    NoCachedResponse.init()
    NoCachedResponse.clear()
    NoCachedResponse.exists_in_cache(MagicMock())
    NoCachedResponse.store_in_cache(MagicMock(), MagicMock())


def test_response_wont_exist_in_cache(http_request, http_response):
    NoCachedResponse.store_in_cache(http_request, http_response)
    assert not NoCachedResponse.exists_in_cache(http_request)

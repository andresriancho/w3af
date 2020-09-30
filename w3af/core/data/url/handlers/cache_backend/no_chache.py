from w3af.core.data.url.handlers.cache_backend.cached_response import CachedResponse


class NoCachedResponse(CachedResponse):
    @staticmethod
    def init():
        pass

    @staticmethod
    def exists_in_cache(request):
        return False

    @staticmethod
    def clear():
        pass

    @staticmethod
    def store_in_cache(request, response):
        pass

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.info_set import InfoSet


class cdn_providers(GrepPlugin):
    """
    Check CDN (Content Delivery Network) providers used by the website.

    :author: Jakub Peczke (qback.contact@gmail.com)
    """
    # CDN headers stored in format ['header-name', 'header-value', 'provider's name']
    cdn_headers = (
        ["server", "cloudflare", "Cloudflare"],
        ["server", "yunjiasu", "Yunjiasu"],
        ["server", "ECS", "Edgecast"],
        ["server", "ECAcc", "Edgecast"],
        ["server", "ECD", "Edgecast"],
        ["server", "NetDNA", "NetDNA"],
        ["server", "Airee", "Airee"],
        ["X-CDN-Geo", "", "OVH CDN"],
        ["X-CDN-Pop", "", "OVH CDN"],
        ["X-Px", "", "CDNetworks"],
        ["X-Instart-Request-ID", "instart", "Instart Logic"],
        ["Via", "CloudFront", "Amazon CloudFront"],
        ["X-Edge-IP", "", "CDN"],
        ["X-Edge-Location", "", "CDN"],
        ["X-HW", "", "Highwinds"],
        ["X-Powered-By", "NYI FTW", "NYI FTW"],
        ["X-Delivered-By", "NYI FTW", "NYI FTW"],
        ["server", "ReSRC", "ReSRC.it"],
        ["X-Cdn", "Zenedge", "Zenedge"],
        ["server", "leasewebcdn", "LeaseWeb CDN"],
        ["Via", "Rev-Cache", "Rev Software"],
        ["X-Rev-Cache", "", "Rev Software"],
        ["Server", "Caspowa", "Caspowa"],
        ["Server", "SurgeCDN", "Surge"],
        ["server", "sffe", "Google"],
        ["server", "gws", "Google"],
        ["server", "GSE", "Google"],
        ["server", "Golfe2", "Google"],
        ["Via", "google", "Google"],
        ["server", "tsa_b", "Twitter"],
        ["X-Cache", "cache.51cdn.com", "ChinaNetCenter"],
        ["X-CDN", "Incapsula", "Incapsula"],
        ["X-Iinfo", "", "Incapsula"],
        ["X-Ar-Debug", "", "Aryaka"],
        ["server", "gocache", "GoCache"],
        ["server", "hiberniacdn", "HiberniaCDN"],
        ["server", "UnicornCDN", "UnicornCDN"],
        ["server", "Optimal CDN", "Optimal CDN"],
        ["server", "Sucuri/Cloudproxy", "Sucuri Firewall"],
        ["x-sucuri-id", "", "Sucuri Firewall"],
        ["server", "Netlify", "Netlify"],
        ["section-io-id", "", "section.io"],
        ["server", "Testa/", "Naver"],
        ["server", "BunnyCDN", "BunnyCDN"],
        ["server", "MNCDN", "Medianova"],
        ["server", "Roast.io", "Roast.io"],
        ["x-rocket-node", "", "Rocket CDN"],
    )

    def grep(self, request, response):
        """
        Check if all responses has CDN header included
        """
        headers = response.get_headers()
        for cdn_header in self.cdn_headers:
            cdn_header_name = cdn_header[0]
            if cdn_header_name in headers:
                if cdn_header[1] == headers[cdn_header_name]:
                    detected_cdn_provider = cdn_header[2]
                    description = 'The URL {} is served using CDN provider: {}'.format(
                        response.get_url(),
                        detected_cdn_provider
                    )
                    info = Info(
                        'Content Delivery Network Provider detected',
                        description,
                        response.id,
                        self.get_name()
                    )
                    info[CDNProvidersInfoSet.ITAG] = detected_cdn_provider
                    info.set_url(response.get_url())
                    self.kb_append_uniq_group(
                        self,
                        'cdn_providers',
                        info,
                        group_klass=CDNProvidersInfoSet
                    )

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Check CDN (Content Delivery Network) providers used by the website.
        """


class CDNProvidersInfoSet(InfoSet):
    ITAG = 'provider'
    TEMPLATE = (
        'The remote web server sent {{ uris|length }} HTTP responses '
        'recognized as served by {{ provider }}. The first ten URLs are: \n'
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )

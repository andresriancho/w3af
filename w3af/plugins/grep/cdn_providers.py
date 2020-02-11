"""
cdn_providers.py

Copyright 2020 Andres Riancho

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
        ['server', 'cloudflare', 'Cloudflare'],
        ['server', 'yunjiasu', 'Yunjiasu'],
        ['server', 'ECS', 'Edgecast'],
        ['server', 'ECAcc', 'Edgecast'],
        ['server', 'ECD', 'Edgecast'],
        ['server', 'NetDNA', 'NetDNA'],
        ['server', 'Airee', 'Airee'],
        ['X-CDN-Geo', '', 'OVH CDN'],
        ['X-CDN-Pop', '', 'OVH CDN'],
        ['X-Px', '', 'CDNetworks'],
        ['X-Instart-Request-ID', 'instart', 'Instart Logic'],
        ['Via', 'CloudFront', 'Amazon CloudFront'],
        ['X-Edge-IP', '', 'CDN'],
        ['X-Edge-Location', '', 'CDN'],
        ['X-HW', '', 'Highwinds'],
        ['X-Powered-By', 'NYI FTW', 'NYI FTW'],
        ['X-Delivered-By', 'NYI FTW', 'NYI FTW'],
        ['server', 'ReSRC', 'ReSRC.it'],
        ['X-Cdn', 'Zenedge', 'Zenedge'],
        ['server', 'leasewebcdn', 'LeaseWeb CDN'],
        ['Via', 'Rev-Cache', 'Rev Software'],
        ['X-Rev-Cache', '', 'Rev Software'],
        ['Server', 'Caspowa', 'Caspowa'],
        ['Server', 'SurgeCDN', 'Surge'],
        ['server', 'sffe', 'Google'],
        ['server', 'gws', 'Google'],
        ['server', 'GSE', 'Google'],
        ['server', 'Golfe2', 'Google'],
        ['Via', 'google', 'Google'],
        ['server', 'tsa_b', 'Twitter'],
        ['X-Cache', 'cache.51cdn.com', 'ChinaNetCenter'],
        ['X-CDN', 'Incapsula', 'Incapsula'],
        ['X-Iinfo', '', 'Incapsula'],
        ['X-Ar-Debug', '', 'Aryaka'],
        ['server', 'gocache', 'GoCache'],
        ['server', 'hiberniacdn', 'HiberniaCDN'],
        ['server', 'UnicornCDN', 'UnicornCDN'],
        ['server', 'Optimal CDN', 'Optimal CDN'],
        ['server', 'Sucuri/Cloudproxy', 'Sucuri Firewall'],
        ['x-sucuri-id', '', 'Sucuri Firewall'],
        ['server', 'Netlify', 'Netlify'],
        ['section-io-id', '', 'section.io'],
        ['server', 'Testa/', 'Naver'],
        ['server', 'BunnyCDN', 'BunnyCDN'],
        ['server', 'MNCDN', 'Medianova'],
        ['server', 'Roast.io', 'Roast.io'],
        ['x-rocket-node', '', 'Rocket CDN'],
    )

    # CDN domains stored in format ['required part of a domain', 'provider's name']
    cdn_domains = [
        ['.akamai.net', 'Akamai'],
        ['.akamaized.net', 'Akamai'],
        ['.akamaiedge.net', 'Akamai'],
        ['.akamaihd.net', 'Akamai'],
        ['.edgesuite.net', 'Akamai'],
        ['.edgekey.net', 'Akamai'],
        ['.srip.net', 'Akamai'],
        ['.akamaitechnologies.com', 'Akamai'],
        ['.akamaitechnologies.fr', 'Akamai'],
        ['.tl88.net', 'Akamai China CDN'],
        ['.llnwd.net', 'Limelight'],
        ['edgecastcdn.net', 'Edgecast'],
        ['.systemcdn.net', 'Edgecast'],
        ['.transactcdn.net', 'Edgecast'],
        ['.v1cdn.net', 'Edgecast'],
        ['.v2cdn.net', 'Edgecast'],
        ['.v3cdn.net', 'Edgecast'],
        ['.v4cdn.net', 'Edgecast'],
        ['.v5cdn.net', 'Edgecast'],
        ['hwcdn.net', 'Highwinds'],
        ['.simplecdn.net', 'Simple CDN'],
        ['.instacontent.net', 'Mirror Image'],
        ['.footprint.net', 'Level 3'],
        ['.fpbns.net', 'Level 3'],
        ['.ay1.b.yahoo.com', 'Yahoo'],
        ['.yimg.', 'Yahoo'],
        ['.yahooapis.com', 'Yahoo'],
        ['.google.', 'Google'],
        ['googlesyndication.', 'Google'],
        ['youtube.', 'Google'],
        ['.googleusercontent.com', 'Google'],
        ['googlehosted.com', 'Google'],
        ['.gstatic.com', 'Google'],
        ['.doubleclick.net', 'Google'],
        ['.insnw.net', 'Instart Logic'],
        ['.inscname.net', 'Instart Logic'],
        ['.internapcdn.net', 'Internap'],
        ['.cloudfront.net', 'Amazon CloudFront'],
        ['.netdna-cdn.com', 'NetDNA'],
        ['.netdna-ssl.com', 'NetDNA'],
        ['.netdna.com', 'NetDNA'],
        ['.kxcdn.com', 'KeyCDN'],
        ['.cotcdn.net', 'Cotendo CDN'],
        ['.cachefly.net', 'Cachefly'],
        ['bo.lt', 'BO.LT'],
        ['.cloudflare.com', 'Cloudflare'],
        ['.afxcdn.net', 'afxcdn.net'],
        ['.lxdns.com', 'ChinaNetCenter'],
        ['.wscdns.com', 'ChinaNetCenter'],
        ['.wscloudcdn.com', 'ChinaNetCenter'],
        ['.ourwebpic.com', 'ChinaNetCenter'],
        ['.att-dsa.net', 'AT&T'],
        ['.vo.msecnd.net', 'Microsoft Azure'],
        ['.azureedge.net', 'Microsoft Azure'],
        ['.azure.microsoft.com', 'Microsoft Azure'],
        ['.voxcdn.net', 'VoxCDN'],
        ['.bluehatnetwork.com', 'Blue Hat Network'],
        ['.swiftcdn1.com', 'SwiftCDN'],
        ['.cdngc.net', 'CDNetworks'],
        ['.gccdn.net', 'CDNetworks'],
        ['.panthercdn.com', 'CDNetworks'],
        ['.fastly.net', 'Fastly'],
        ['.fastlylb.net', 'Fastly'],
        ['.nocookie.net', 'Fastly'],
        ['.gslb.taobao.com', 'Taobao'],
        ['.gslb.tbcache.com', 'Alimama'],
        ['.mirror-image.net', 'Mirror Image'],
        ['.yottaa.net', 'Yottaa'],
        ['.cubecdn.net', 'cubeCDN'],
        ['.cdn77.net', 'CDN77'],
        ['.cdn77.org', 'CDN77'],
        ['.incapdns.net', 'Incapsula'],
        ['.bitgravity.com', 'BitGravity'],
        ['.r.worldcdn.net', 'OnApp'],
        ['.r.worldssl.net', 'OnApp'],
        ['tbcdn.cn', 'Taobao'],
        ['.taobaocdn.com', 'Taobao'],
        ['.ngenix.net', 'NGENIX'],
        ['.pagerain.net', 'PageRain'],
        ['.ccgslb.com', 'ChinaCache'],
        ['cdn.sfr.net', 'SFR'],
        ['.azioncdn.net', 'Azion'],
        ['.azioncdn.com', 'Azion'],
        ['.azion.net', 'Azion'],
        ['.cdncloud.net.au', 'MediaCloud'],
        ['.rncdn1.com', 'Reflected Networks'],
        ['.cdnsun.net', 'CDNsun'],
        ['.mncdn.com', 'Medianova'],
        ['.mncdn.net', 'Medianova'],
        ['.mncdn.org', 'Medianova'],
        ['cdn.jsdelivr.net', 'jsDelivr'],
        ['.nyiftw.net', 'NYI FTW'],
        ['.nyiftw.com', 'NYI FTW'],
        ['.resrc.it', 'ReSRC.it'],
        ['.zenedge.net', 'Zenedge'],
        ['.lswcdn.net', 'LeaseWeb CDN'],
        ['.lswcdn.eu', 'LeaseWeb CDN'],
        ['.revcn.net', 'Rev Software'],
        ['.revdn.net', 'Rev Software'],
        ['.caspowa.com', 'Caspowa'],
        ['.twimg.com', 'Twitter'],
        ['.facebook.com', 'Facebook'],
        ['.facebook.net', 'Facebook'],
        ['.fbcdn.net', 'Facebook'],
        ['.cdninstagram.com', 'Facebook'],
        ['.rlcdn.com', 'Reapleaf'],
        ['.wp.com', 'WordPress'],
        ['.aads1.net', 'Aryaka'],
        ['.aads-cn.net', 'Aryaka'],
        ['.aads-cng.net', 'Aryaka'],
        ['.squixa.net', 'section.io'],
        ['.bisongrid.net', 'Bison Grid'],
        ['.cdn.gocache.net', 'GoCache'],
        ['.hiberniacdn.com', 'HiberniaCDN'],
        ['.cdntel.net', 'Telenor'],
        ['.raxcdn.com', 'Rackspace'],
        ['.unicorncdn.net', 'UnicornCDN'],
        ['.optimalcdn.com', 'Optimal CDN'],
        ['.kinxcdn.com', 'KINX CDN'],
        ['.kinxcdn.net', 'KINX CDN'],
        ['.stackpathdns.com', 'StackPath'],
        ['.hosting4cdn.com', 'Hosting4CDN'],
        ['.netlify.com', 'Netlify'],
        ['.b-cdn.net', 'BunnyCDN'],
        ['.pix-cdn.org', 'Advanced Hosters CDN'],
        ['.roast.io', 'Roast.io'],
        ['.cdnvideo.ru', 'CDNvideo'],
        ['.cdnvideo.net', 'CDNvideo'],
        ['.trbcdn.ru', 'TRBCDN'],
        ['.cedexis.net', 'Cedexis'],
        ['.streamprovider.net', 'Rocket CDN'],
    ]

    def grep(self, request, response):
        """
        Check if responses are hosted by CDN provider
        """
        headers = response.get_headers()
        for cdn_header_name, cdn_header_value, provider_name in self.cdn_headers:
            if cdn_header_name in headers:
                if cdn_header_value == headers[cdn_header_name]:
                    self._save_found_cdn_to_kb(response, provider_name)
                    return  # We don't want to check the URL also

        url = request.get_url()
        domain = url.get_domain()
        for cdn_domain, provider_name in self.cdn_domains:
            if cdn_domain in domain:
                self._save_found_cdn_to_kb(response, provider_name)

    def _save_found_cdn_to_kb(self, response, provider_name):
        """
        Save grep result to knowledge base
        """
        description = 'The URL {} is served using CDN provider: {}'.format(
            response.get_url(),
            provider_name
        )
        info = Info(
            'Content Delivery Network Provider detected',
            description,
            response.id,
            self.get_name()
        )
        info[CDNProvidersInfoSet.ITAG] = provider_name
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
        Identify any CDN (Content Delivery Network) providers used by the target website.
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

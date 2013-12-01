'''
php_eggs.py

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

'''
import hashlib

from itertools import repeat, izip
from collections import namedtuple

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb

from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.controllers.misc.decorators import runonce
from core.controllers.exceptions import w3afException, w3afRunOnce
from core.controllers.threads.threadpool import one_to_many
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from core.data.kb.info import Info


class php_eggs(InfrastructurePlugin):
    '''
    Fingerprint the PHP version using documented easter eggs that exist in PHP.
    :author: Andres Riancho (andres.riancho@gmail.com)
    '''
    PHP_EGGS = [('?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000', 'PHP Credits'),
                ('?=PHPE9568F34-D428-11d2-A769-00AA001ACF42', 'PHP Logo'),
                ('?=PHPE9568F35-D428-11d2-A769-00AA001ACF42', 'Zend Logo'),
                ('?=PHPE9568F36-D428-11d2-A769-00AA001ACF42', 'PHP Logo 2')]

    #
    # This is a list of hashes and description of the egg for every PHP version.
    # PHP versions 4.0.0 - 4.0.6
    # PHP versions 4.1.0 - 4.1.3
    # PHP versions 4.2.0 - 4.2.3
    # PHP versions 4.3.0 - 4.3.11
    # PHP versions 4.4.0 - 4.4.9
    # PHP versions 5.0.0 - 5.0.5
    # PHP versions 5.1.0 - 5.1.6
    # PHP versions 5.2.0 - 5.2.17
    # PHP versions 5.3.0 - 5.3.27
    # PHP versions 5.4.0 - 5.4.22 (still in progress)
    # Remark: PHP versions 5.5.x has no PHP-Eggs.
    # Remark: PHP Logo 2 is not always available. 
    
    
    EGG_DB = {}
    EGG_DB["4.0.0"] = [
        ("7c75d38f7b26b7cc13ed1d7bbedd0bb8", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.0.1"] = [
        ("31e2dd536176af3f7f142c18eef1aa4e", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.0.2"] = [
        ("34591272f6dd5cf9953b65dfdb390259", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.0.3pl1"] = [
        ("34591272f6dd5cf9953b65dfdb390259", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.0.4pl1"] = [
        ("bee683d024c0065a6e7ae57458416f60", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.0.5"] = [
        ("34040cf89a0574e7de5c643da6d9eab8", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.0.6"] = [
        ("5bd3e883d03543baf7f39749d526c5a4", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.1.0"] = [
        ("744aecef04f9ed1bc39ae773c40017d1", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.1.1"] = [
        ("744aecef04f9ed1bc39ae773c40017d1", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.1.2"] = [
        ("744aecef04f9ed1bc39ae773c40017d1", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.1.3"] = [
        ("744aecef04f9ed1bc39ae773c40017d1", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.2.0"] = [
        ("8bc001f58bf6c17a67e1ca288cb459cc", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.2.1"] = [
        ("8bc001f58bf6c17a67e1ca288cb459cc", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.2.2"] = [
        ("8bc001f58bf6c17a67e1ca288cb459cc", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.2.3"] = [
        ("3422eded2fcceb3c89cabb5156b5d4e2", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.0"] = [
        ("1e04761e912831dd29b7a98785e7ac61", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.1"] = [
        ("1e04761e912831dd29b7a98785e7ac61", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.2"] = [
        ("22d03c3c0a9cff6d760a4ba63909faea", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.3"] = [
        ("8a4a61f60025b43f11a7c998f02b1902", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.4"] = [
        ("8a4a61f60025b43f11a7c998f02b1902", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.5"] = [
        ("8a4a61f60025b43f11a7c998f02b1902", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.6"] = [
        ("913ec921cf487109084a518f91e70859", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.7"] = [
        ("913ec921cf487109084a518f91e70859", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.8"] = [
        ("913ec921cf487109084a518f91e70859", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.9"] = [
        ("913ec921cf487109084a518f91e70859", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.10"] = [
        ("8fbf48d5a2a64065fc26db3e890b9871", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.10-18"] = [
        ("1e8fe4ae1bf06be222c1643d32015f0c", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.11"] = [
        ("8fbf48d5a2a64065fc26db3e890b9871", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.2"] = [
        ("8a8b4a419103078d82707cf68226a482", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.3.9"] = [
        ("f9b56b361fafd28b668cc3498425a23b", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB['4.3.10'] = [
        ('b233cc756b06655f47489aa2779413d7', 'PHP Credits'),
        ('7b27e18dc6f846b80e2f29ecf67e4133', 'PHP Logo'),
        ('185386dd4b2eff044bd635d22ae7dd9e', 'PHP Logo 2'),
        ('43af90bcfa66f16af62744e8c599703d', 'Zend Logo')]
    EGG_DB["4.4.0"] = [
        ("ddf16ec67e070ec6247ec1908c52377e", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.0 for Windows"] = [
        ("6d974373683ecfcf30a7f6873f2d234a", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.1"] = [
        ("55bc081f2d460b8e6eb326a953c0e71e", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.2"] = [
        ("bed7ceff09e9666d96fdf3518af78e0e", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.3"] = [
        ("bed7ceff09e9666d96fdf3518af78e0e", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.4"] = [
        ("bed7ceff09e9666d96fdf3518af78e0e", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.4-8+etch6"] = [
        ("31a2553efc348a21b85e606e5e6c2424", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.5"] = [
        ("692a87ca2c51523c17f597253653c777", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.6"] = [
        ("692a87ca2c51523c17f597253653c777", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.7"] = [
        ("692a87ca2c51523c17f597253653c777", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.7"] = [
        ("72b7ad604fe1362f1e8bf4f6d80d4edc", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.8"] = [
        ("50ac182f03fc56a719a41fc1786d937d", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.8"] = [
        ("4cdfec8ca11691a46f4f63839e559fc5", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["4.4.9"] = [
        ("50ac182f03fc56a719a41fc1786d937d", "PHP Credits"),
        ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo")]
    EGG_DB["5.0.0RC1"] = [
        ("314e92ddb1a8abc0781ab87d5b66e960", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("37e194b799d4aaff10e39c4e3b2679a2", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.0.0RC2"] = [
        ("e54dbf41d985bfbfa316dba207ad6bce", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("37e194b799d4aaff10e39c4e3b2679a2", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.0.0RC3"] = [
        ("e54dbf41d985bfbfa316dba207ad6bce", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("37e194b799d4aaff10e39c4e3b2679a2", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.0.0"] = [
        ("e54dbf41d985bfbfa316dba207ad6bce", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("37e194b799d4aaff10e39c4e3b2679a2", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.0.1"] = [
        ("3c31e4674f42a49108b5300f8e73be26", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("37e194b799d4aaff10e39c4e3b2679a2", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.0.2"] = [
        ("3c31e4674f42a49108b5300f8e73be26", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("37e194b799d4aaff10e39c4e3b2679a2", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.0.3"] = [
        ("3c31e4674f42a49108b5300f8e73be26", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("37e194b799d4aaff10e39c4e3b2679a2", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.0.4"] = [
        ("3c31e4674f42a49108b5300f8e73be26", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.0.5"] = [
        ("6be3565cdd38e717e4eb96868d9be141", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.0RC1"] = [
        ("2673a94df41739ef8b012c07518b6c6f", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.0"] = [
        ("5518a02af41478cfc492c930ace45ae5", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.1"] = [
        ("5518a02af41478cfc492c930ace45ae5", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.2"] = [
        ("6cb0a5ba2d88f9d6c5c9e144dd5941a6", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.2"] = [
        ("b83433fb99d0bef643709364f059a44a", "PHP Credits"),
        ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"),
        ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.3"] = [
        ("82fa2d6aa15f971f7dadefe4f2ac20e3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.4"] = [
        ("82fa2d6aa15f971f7dadefe4f2ac20e3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.5"] = [
        ("82fa2d6aa15f971f7dadefe4f2ac20e3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.6"] = [
        ("82fa2d6aa15f971f7dadefe4f2ac20e3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.1.6"] = [
        ("4b689316409eb09b155852e00657a0ae", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.0"] = [
        ("e566715bcb0fd2cb1dc43ed076c091f1", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.0-8+etch10"] = [
        ("e566715bcb0fd2cb1dc43ed076c091f1", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.0-8+etch7"] = [
        ("307f5a1c02155ca38744647eb94b3543", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.1"] = [
        ("d3894e19233d979db07d623f608b6ece", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.2"] = [
        ("56f9383587ebcc94558e11ec08584f05", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.3"] = [
        ("c37c96e8728dc959c55219d47f2d543f", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.3-1+b1"] = [
        ("c37c96e8728dc959c55219d47f2d543f", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.4"] = [
        ("74c33ab9745d022ba61bc43a5db717eb", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.4-2ubuntu5.3"] = [
        ("f26285281120a2296072f21e21e7b4b0", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.4-2ubuntu5.14"] = [
        ("c37c96e8728dc959c55219d47f2d543f", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.5"] = [
        ("c37c96e8728dc959c55219d47f2d543f", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.5"] = [
        ("f26285281120a2296072f21e21e7b4b0", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.5-3"] = [
        ("b7e4385bd7f07e378d92485b4722c169", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("0152ed695f4291488741d98ba066d280", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.6"] = [
        ("bbd44c20d561a0fc5a4aa76093d5400f", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.6RC4-pl0-gentoo"] = [
        ("d03b2481f60d9e64cb5c0f4bd0c87ec1", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.7"] = [
        ("1ffc970c5eae684bebc0e0133c4e1f01", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.8"] = [
        ("1ffc970c5eae684bebc0e0133c4e1f01", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.8-pl1-gentoo"] = [
        ("40410284d460552a6c9e10c1f5ae7223", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.9"] = [
        ("54f426521bf61f2d95c8bfaa13857c51", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.10"] = [
        ("54f426521bf61f2d95c8bfaa13857c51", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.11"] = [
        ("54f426521bf61f2d95c8bfaa13857c51", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.12"] = [
        ("54f426521bf61f2d95c8bfaa13857c51", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.13"] = [
        ("54f426521bf61f2d95c8bfaa13857c51", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.14"] = [
        ("54f426521bf61f2d95c8bfaa13857c51", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.15"] = [
        ("adb361b9255c1e5275e5bd6e2907c5fb", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.16"] = [
        ("adb361b9255c1e5275e5bd6e2907c5fb", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.2.17"] = [
        ("adb361b9255c1e5275e5bd6e2907c5fb", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.0"] = [
        ("db23b07a9b426d0d033565b878b1e384", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.1"] = [
        ("a4c057b11fa0fba98c8e26cd7bb762a8", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.2"] = [
        ("a4c057b11fa0fba98c8e26cd7bb762a8", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.3"] = [
        ("b34501471d51cebafacdd45bf2cd545d", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.4"] = [
        ("e3b18899d0ffdf8322ed18d7bce3c9a0", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.5"] = [
        ("e3b18899d0ffdf8322ed18d7bce3c9a0", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.6"] = [
        ("2e7f5372931a7f6f86786e95871ac947", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.7"] = [
        ("f1f1f60ac0dcd700a1ad30aa81175d34", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.8"] = [
        ("f1f1f60ac0dcd700a1ad30aa81175d34", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.9"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.10"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.11"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.12"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.13"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.14"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.15"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.16"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.17"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.18"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.19"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.20"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.21"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.22"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.21-pl1-gentoo"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.23"] = [
        ("5e8e6736635920a0a97ba79d69c55b30", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.23"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.24"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.25"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.26"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.3.27"] = [
        ("23f183b78eb4e3ba8b3df13f0a15e5de", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.0"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.1"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.2"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.3"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.4"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.5"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.6"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.7"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.8"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.9"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.10"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.11"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.12"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.13"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.14"] = [
        ("85da0a620fabe694dab1d55cbf1e24c3", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.15"] = [
        ("ebf6d0333d67af5f80077438c45c8eaa", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.16"] = [
        ("ebf6d0333d67af5f80077438c45c8eaa", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.17"] = [
        ("ebf6d0333d67af5f80077438c45c8eaa", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.18"] = [
        ("ebf6d0333d67af5f80077438c45c8eaa", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.19"] = [
        ("ebf6d0333d67af5f80077438c45c8eaa", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.20"] = [
        ("ebf6d0333d67af5f80077438c45c8eaa", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.21"] = [
        ("ebf6d0333d67af5f80077438c45c8eaa", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]
    EGG_DB["5.4.22"] = [
        ("ebf6d0333d67af5f80077438c45c8eaa", "PHP Credits"),
        ("c48b07899917dfb5d591032007041ae3", "PHP Logo"),
        ("fb3bbd9ccc4b3d9e0b3be89c5ff98a14", "PHP Logo 2"),
        ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo")]

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Already analyzed extensions
        self._already_analyzed_ext = ScalableBloomFilter()

    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzable_request):
        '''
        Nothing strange, just do some GET requests to the eggs and analyze the
        response.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        # Get the extension of the URL (.html, .php, .. etc)
        ext = fuzzable_request.get_url().get_extension()

        # Only perform this analysis if we haven't already analyzed this type
        # of extension OR if we get an URL like http://f00b5r/4/     (Note that
        # it has no extension) This logic will perform some extra tests... but
        # we won't miss some special cases. Also, we aren't doing something like
        # "if 'php' in ext:" because we never depend on something so changable
        # as extensions to make decisions.
        if ext not in self._already_analyzed_ext:

            # Now we save the extension as one of the already analyzed
            self._already_analyzed_ext.add(ext)

            # Init some internal variables
            query_results = self._GET_php_eggs(fuzzable_request, ext)

            if self._are_php_eggs(query_results):
                # analyze the info to see if we can identify the version
                self._extract_version_from_egg(query_results)

    def _GET_php_eggs(self, fuzzable_request, ext):
        '''
        HTTP GET the URLs for PHP Eggs
        :return: A list with the HTTP response objects
        '''
        def http_get(fuzzable_request, (egg_url, egg_desc)):
            egg_URL = fuzzable_request.get_url().uri2url().url_join(egg_url)
            try:
                response = self._uri_opener.GET(egg_URL, cache=True)
            except w3afException, w3:
                raise w3
            else:
                return response, egg_URL, egg_desc

        # Send the requests using threads:
        query_results = []
        EggQueryResult = namedtuple('EggQueryResult', ['http_response',
                                                       'egg_desc',
                                                       'egg_URL'])
        
        http_get = one_to_many(http_get)
        fr_repeater = repeat(fuzzable_request)
        args_iterator = izip(fr_repeater, self.PHP_EGGS)
        pool_results = self.worker_pool.imap_unordered(http_get,
                                                       args_iterator)

        for response, egg_URL, egg_desc in pool_results:
            eqr = EggQueryResult(response, egg_desc, egg_URL)
            query_results.append(eqr)

        return query_results

    def _are_php_eggs(self, query_results):
        '''
        Now I analyze if this is really a PHP eggs thing, or simply a response that
        changes a lot on each request. Before, I had something like this:

            if relative_distance(original_response.get_body(), response.get_body()) < 0.1:

        But I got some reports about false positives with this approach, so now I'm
        changing it to something a little bit more specific.
        '''
        images = 0
        not_images = 0
        for query_result in query_results:
            if 'image' in query_result.http_response.content_type:
                images += 1
            else:
                not_images += 1

        if images == 3 and not_images == 1:
            #
            #   The remote web server has expose_php = On. Report all the findings.
            #
            for query_result in query_results:
                desc = 'The PHP framework running on the remote server has a'\
                       ' "%s" easter egg, access to the PHP egg is possible'\
                       ' through the URL: "%s".'
                desc = desc % (query_result.egg_desc, query_result.egg_URL)
                
                i = Info('PHP Egg', desc, query_result.http_response.id, self.get_name())
                i.set_url(query_result.egg_URL)
                
                kb.kb.append(self, 'eggs', i)
                om.out.information(i.get_desc())

            return True

        return False

    def _extract_version_from_egg(self, query_results):
        '''
        Analyzes the eggs and tries to deduce a PHP version number
        ( which is then saved to the kb ).
        '''
        if not query_results:
            return None
        else:
            cmp_list = []
            for query_result in query_results:
                body = query_result.http_response.get_body()
                if isinstance(body, unicode): body = body.encode('utf-8')
                hash_str = hashlib.md5(body).hexdigest()
                
                cmp_list.append((hash_str, query_result.egg_desc))
                
            cmp_set = set(cmp_list)

            found = False
            matching_versions = []
            for version in self.EGG_DB:
                version_hashes = set(self.EGG_DB[version])

                if len(cmp_set) == len(cmp_set.intersection(version_hashes)):
                    matching_versions.append(version)
                    found = True

            if matching_versions:
                desc = 'The PHP framework version running on the remote'\
                       ' server was identified as:\n- %s'
                versions = '\n- '.join(matching_versions)
                desc = desc % versions
                
                response_ids = [r.http_response.get_id() for r in query_results]
                
                i = Info('Fingerprinted PHP version', desc, response_ids,
                         self.get_name())
                i['version'] = matching_versions
                
                kb.kb.append(self, 'version', i)
                om.out.information(i.get_desc())

            if not found:
                version = 'unknown'
                powered_by_headers = kb.kb.raw_read('server_header',
                                                    'powered_by_string')
                try:
                    for v in powered_by_headers:
                        if 'php' in v.lower():
                            version = v.split('/')[1]
                except:
                    pass
                
                msg = 'The PHP version could not be identified using PHP eggs,'\
                      ', please send this signature and the PHP version to the'\
                      ' w3af project develop mailing list. Signature:'\
                      ' EGG_DB[\'%s\'] = %s\n'
                msg = msg % (version, str(list(cmp_set)))
                om.out.information(msg)

    def get_plugin_deps(self):
        '''
        :return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['infrastructure.server_header']

    def get_long_desc(self):
        '''
        :return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to find the documented easter eggs that exist in PHP
        and identifies the remote PHP version using the easter egg content.
        Known PHP easter eggs are visible in versions 4.0 - 5.4.
        The easter eggs that this plugin verifies are:

        PHP Credits, Logo, Zend Logo, PHP Logo 2:
            - http://php.net/?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000
            - http://php.net/?=PHPE9568F34-D428-11d2-A769-00AA001ACF42
            - http://php.net/?=PHPE9568F35-D428-11d2-A769-00AA001ACF42
            - http://php.net/?=PHPE9568F36-D428-11d2-A769-00AA001ACF42
        '''

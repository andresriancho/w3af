'''
test_list_kernel_modules.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
from plugins.attack.payloads.tests.payload_test_helper import PayloadTestHelper
from plugins.attack.payloads.payload_handler import exec_payload


class test_list_kernel_modules(PayloadTestHelper):
    
    EXPECTED_RESULT = {   u'ac97_bus': { 'used': u'snd_ac97_codec'},
                          u'btrfs': { 'used': ''},
                          u'e1000': { 'used': ''},
                          u'ext2': { 'used': ''},
                          u'fat': { 'used': u'vfat,msdos'},
                          u'hfs': { 'used': ''},
                          u'hfsplus': { 'used': ''},
                          u'hid': { 'used': u'usbhid'},
                          u'i2c_piix4': { 'used': ''},
                          u'jfs': { 'used': ''},
                          u'joydev': { 'used': ''},
                          u'libcrc32c': { 'used': u'btrfs'},
                          u'lp': { 'used': ''},
                          u'mac_hid': { 'used': ''},
                          u'minix': { 'used': ''},
                          u'msdos': { 'used': ''},
                          u'ntfs': { 'used': ''},
                          u'parport': { 'used': u'ppdev,parport_pc,lp'},
                          u'parport_pc': { 'used': ''},
                          u'ppdev': { 'used': ''},
                          u'psmouse': { 'used': ''},
                          u'qnx4': { 'used': ''},
                          u'reiserfs': { 'used': ''},
                          u'serio_raw': { 'used': ''},
                          u'snd': { 'used': u'snd_intel8x0,snd_ac97_codec,snd_pcm,snd_timer'},
                          u'snd_ac97_codec': { 'used': u'snd_intel8x0'},
                          u'snd_intel8x0': { 'used': ''},
                          u'snd_page_alloc': { 'used': u'snd_intel8x0,snd_pcm'},
                          u'snd_pcm': { 'used': u'snd_intel8x0,snd_ac97_codec'},
                          u'snd_timer': { 'used': u'snd_pcm'},
                          u'soundcore': { 'used': u'snd'},
                          u'ufs': { 'used': ''},
                          u'usbhid': { 'used': ''},
                          u'vesafb': { 'used': ''},
                          u'vfat': { 'used': ''},
                          u'xfs': { 'used': ''},
                          u'zlib_deflate': { 'used': u'btrfs'}}

    def test_list_kernel_modules(self):
        result = exec_payload(self.shell, 'list_kernel_modules', use_api=True)
        self.assertEquals(self.EXPECTED_RESULT, result)
        

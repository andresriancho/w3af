#!/bin/bash -x

pip install pyOpenSSL==0.14
pip install jinja2==2.7.3
pip install -U --force-reinstall git+git://github.com/mitmproxy/netlib.git@55c2133b69bc39ad43c6ce1ab14b32019878e56a
pip install -U --force-reinstall git+git://github.com/mitmproxy/mitmproxy.git@05a8c52f8f6c4fb5f1820475b9682da5a1eeadda

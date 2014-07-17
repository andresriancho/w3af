#!/bin/bash -x

pip install pyOpenSSL==0.14 jinja2
pip install git+git://github.com/mitmproxy/netlib.git@52c6ba8880363ba5d82b5e767559afbc72371272
pip install git+git://github.com/mitmproxy/mitmproxy.git@05a8c52f8f6c4fb5f1820475b9682da5a1eeadda

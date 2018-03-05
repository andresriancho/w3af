# Generate new CA

```python
from netlib import http_auth, certutils

ca_dir = '/home/pablo/pch/w3af/w3af/core/controllers/daemons/proxy/ca/'
certutils.CertStore.create_store(ca_dir, 'mitmproxy', o='w3af MITM CA', cn='w3af MITM CA')
```

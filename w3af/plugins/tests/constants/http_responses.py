APACHE_403_FMT = """
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>403 Forbidden</title>
</head><body>
<h1>Forbidden</h1>
<p>You don't have permission to access %s on this server.</p>
<hr>
<address>Apache/2.2.22 (Ubuntu) Server at %s Port 443</address>
</body></html>
"""


def get_apache_403(path, domain):
    return APACHE_403_FMT % (path, domain)
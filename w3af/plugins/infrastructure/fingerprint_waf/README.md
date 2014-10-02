## waf_fingerprints.json

The waf_fingerprints.json describes how to detect WAFs by analyzing the response
of various requests.

The detection is done according HTTP headers, response codes and content
of the response page. For each, a condition to be matched can be defined
in the  waf_checks  table.

The data syntax is as follows:
    * all entries are strings or regex (if prefixed with r)
    * each row describes one WAF (a specific vendor/model)
    * empty strings, aka '', are treated as N/A (not applicapble)
    * columns (from left to right):
      WAF-ID        - unique ID of the WAF, should be the product name
      Code          - status code returned by WAF in error cases
      Status        - pattern to detect in status response
      Content       - pattern to detect in response body (page)
                      the matching string/pattern must be grouped here
                      using the REGEX group braces ()
      Testing URL   - URL for actively testing (passive test if empty)
      Description   - free text description
      Header        - pattern to detect for any HTTP header
      ...           - any number of headers are possible,
                      at least one empty header must exist

All values except WAF-ID, Code and Description, are a pattern for regex.
If all patterns and the Code are empty, detection of that WAF is not yet
possible, obviously. The detection for that entry will be skipped then.

All  none empty values  will be checked.  The detection will return true
(meaning that this WAF is detected) if at least one value matches.

NOTE: empty here means: ''

## waf_vendors.json

The waf_vendors.json file contains following data:
      WAF-ID        - unique ID of the WAF, should be the product name
      Vendor        - WAF vendor
      Product       - WAF product name
      Description   - free text description

All values are simple string constants. The first column, WAF-ID, must
match the one in the array  waf_checks .

## TODO

Comments according WAF detections to be implemented:

- ACE_XML:
	header is actually   Server: ACE XML Gateway
- BinarySec:
	lazy approach, returns Server: BinarySec and/or x-binarysec-via and/or x-binarysec-nocache
- CloudFlare:
    need "weight" for "Headers" as CF-RAY and CF-Cache-Status are not realy an indication for the WAF
- ModSecurity:
	nothing specific to detect :-(
	However, Trustwaves ModSecurity often returns status 501
- SecureIIS:
	needs special handling
- URLScan:
	needs special handling (headers and 404)
	probably following header returned:   r'^Transfer-Encoding:', r'^Translate:', r'^Lock-Token:'
- ISA Server:
	may return 2 different strings:
	The server denied the specified Uniform Resource Locator (URL). Contact the server administrator.
	The ISA Server denied the specified Uniform Resource Locator (URL)
- Profense:
	unsure if cookie is PLBSID or APLBSID
- Proventia:
	probaly contains /Admin_Files/ as URL in page
- rWeb:  page with content is optional
- TrafficShield:
	some also use HTTP-Header   F5-TrafficShield
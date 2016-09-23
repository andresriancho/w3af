The default file was taken from the fuzzdb project http://code.google.com/p/fuzzdb/
(errors.txt in folder regex) and w3af's error_pages plugin. It is able to
find more generic strings which leads to more false positives but simplifies
the process of finding customized error messages.

Adam Muntner added a new file, also from the fuzzdb project, containing regular
expressions that will find PII (such as US SSN) for different countries.

The fuzzdb file was extended with more strings.

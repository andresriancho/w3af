## JS Crawler

w3af's JS crawler is based on [gryffin](https://github.com/yahoo/gryffin). The architecture is simple:

 * w3af runs javascript code inside phantomjs which loads a URL and extracts links and forms
 * The phantomjs binary is configured to use a w3af initiated proxy, which is used to capture HTTP requests
 * The javascript code outputs JSON encoded messages to stdout with the links and forms
 * w3af parses stdout to get the JSON objects
 
## Requirements

For the user the requirement is very simple: "Install phantomjs version > 2.0". This
is solved with `apt install phantomjs` in Debian based distributions.

## Running the crawler
 
The JS crawler can be run without w3af (mostly for dev and QA):

```
phantomjs --ssl-protocol=any --ignore-ssl-errors=true --proxy=127.0.0.1:8080 \
          --proxy-type=http render.js http://192.168.0.40:8899/pages/11.php
```

Remember to start Burp suite or any other proxy on `127.0.0.1:8080` before running that
command. Also note that the target URL is set to WIVET's test number 11, change the URL
to the real target you want to crawl.

## Debugging

`--debug=true` is very powerful and can be added as a phantomjs parameter.

`'{"debug":true}'` will be parsed by `render.js` and used to print debugging information.

```
phantomjs --debug=true ... render.js <url> '{"debug":true}'
```
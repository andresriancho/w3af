# JavaScript Crawling Developer Documentation

## Introduction

JavaScript crawling in w3af was implemented using headless Chrome. The main
components for the solution are:

 * `process.py`: runs the headless chrome process with very specific command line
 flags, allows the developer to capture stdout and kill the process.
 
 * `proxy.py`: a specially crafted HTTP proxy which handles all the traffic for
 Chrome browsers. The main goal of this proxy is to capture the traffic generated
 by the browser while events are handled and send it to the w3af core. 
 
 * `devtools.py`: implements the communication between w3af main process and
 the chrome process using the devtools protocol.
 
 * `instrumented.py`: an abstraction around process, proxy and devtools. It starts
 the proxy, then the process, and finally connects to the browser using devtools.
 This abstraction allows the user to load a URL in the browser, capture all
 the generated traffic using the proxy, and dispatch events (eg. clicks).
 
 * `pool.py`: holds free and in-use instrumented chrome instances which are
 spawned and killed when needed. 
 
 * `crawler.py`: crawls a site using chrome instrumented instances. Uses the
 pool to get the instances. 
 
 * `crawl.web_spider`: the crawl plugin calls `crawler.py` to extract new URLs
 and sends them to the core.
 
## Different processes

There are different processes in this solution:

 * `w3af` main process: runs the scan, `crawl.web_spider`, etc.
 * `chrome` processes: are run by `process.py` and referenced from the pool.
 
Multiple processes were used to prevent issues with a hanging Chrome instance
breaking the scan.

## Crawling

There are multiple definitions of JavaScript crawling, for `w3af` crawling includes
all of the following steps:

 * **Loading a page in a browser**: this will load any external resources such as JS and
 CSS to render the page. This step might also send `XmlHttpRequest`s to REST APIs to retrieve
 information that is then displayed in the view.
 
 * **Extracting links from the page**: once the page has finished loading the DOM, dump
 it and perform HTML parsing on it. Note that the loaded DOM and the HTTP response body
 can be **very different**, thus it makes sense to HTML-parse the loaded DOM.
 
 * **Firing events**: once the page has loaded dispatch events on all DOM nodes.
 This should trigger all the actions which are commonly performed by a user when
 browsing the site, such as: clicking on an element, typing on an input, choosing one 
 option in a select tag, submitting a form, etc. 

 Pseudo-code for this feature looks like:

```python
events = browser.get_events()
for event in events:
    if not should_dispatch(event):
        continue
           
   browser.send_event(event)
   
   if browser.navigated_to_different_page():
       browser.back(dom) 
```

If you're interested in reading the real implementation take a look at [ChromeCrawlerJS._crawl_impl](https://github.com/andresriancho/w3af/blob/feature/js/w3af/core/controllers/chrome/crawler/js.py#L75)

## Testing the JS crawler

Create a simple crawling script named `crawl-js.txt`:

```
http-settings
set max_requests_per_second 30
set max_http_retries 2
set timeout 0
back

back
plugins
crawl web_spider
crawl config web_spider
set follow_regex .*
back

output text_file
output config text_file
set output_file /tmp/crawl-js.txt
set http_output_file /tmp/crawl-js.http
back
back

target set target http://w3af.org/

start
exit
```

Run the scan:

```
./w3af_console -s crawl-js.txt
```

Manually analyze the results by reading the log `/tmp/crawl-js.txt`. 
Some interesting searches for you to make in the file are:

 * `Processing event`
 * ` on CSS selector `
 * `seconds in crawl strategy JS events`
 * `new HTTP requests from`

You can also analyze the results in an automated way using `w3af`'s scan
log analysis tool. This will show you **a lot of information**, much of it
is not related with JS crawling:

```
python w3af/core/controllers/profiling/scan_log_analysis.py /tmp/crawl-js.txt 
```

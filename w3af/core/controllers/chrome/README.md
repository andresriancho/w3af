# JavaScript Crawling Developer Documentation

## Introduction

JavaScript crawling in w3af was implemented using headless chrome. The main
components for the solution are:

 * `process.py`: runs the headless chrome process with very specific flags,
 allows the developer to capture stdout and kill the process.
 
 * `proxy.py`: a specially crafted HTTP proxy which handles all the traffic for
 chrome browsers. The main goal of this proxy is to capture the traffic generated
 by the browser and send it to the w3af core. 
 
 * `devtools.py`: implements the communication between w3af main process and
 the chrome process using the devtools protocol.
 
 * `instrumented.py`: an abstraction around process, proxy and devtools. It starts
 the proxy, then the process, and finally connects to the browser using devtools.
 This abstraction allows the user to load a URL in the browser and capture all
 the generated traffic using the proxy.
 
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
 
Multiple processes were used to prevent issues with a hanging chrome instance
breaking the scan.

## Crawling

There are multiple definitions of JavaScript crawling, for `w3af` crawling includes
all of the following steps:

 * **Loading a page in a browser**: this will load any external resources such as JS and
 CSS to render the page.
 
 * **Extracting links from the page**: once the page has loaded use a tool such as JQuery
 to extract links (`a[href]`) from the page. Send these links to the browser controller.
 
 * **Firing events**: once the page has loaded fire all the events on all DOM nodes.
 This should trigger all the actions which are commonly performed by a user when
 browsing the site, such as: browsing to another page, typing on an input, choosing one 
 option in a select tag, submitting a form, etc. 

 Pseudo-code for this feature looks like:

```python
dom = browser.get_dom()
for event in EVENTS:
    for elem in dom.get_all_children():
        if not has_event_handler(elem, event):
            continue
        if has_changed(dom, browser.get_dom()):
            browser.set_dom(dom)
       browser.send_event(elem, event)
       browser.wait_until_done() 
```

## Debugging the JS crawler

Use a simple crawling script:

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

Run the scan with debugging information:

```
rm -rf /tmp/w3af-*psutil ; W3AF_PSUTILS=1 DEBUG=1 ./w3af_console -s crawl-js.txt
```

Analyze the results:

```
rm -rf crawl-js
mkdir crawl-js
mv /tmp/w3af-*psutil crawl-js/

wget https://gist.githubusercontent.com/andresriancho/08e5110043b1f9fac57dc985f98aa77d/raw/664663e4683fff970a041ef6771fa78ac7d07691/analyze-memory-usage.py

python analyze-memory-usage.py crawl-js/

reset; python w3af/core/controllers/profiling/scan_log_analysis.py /tmp/crawl-js.txt 
```

// 
// TODO
// 1. Cookie suuport for auth protected web apps
// 2. forms
// 3. maxDiscoveryTime option
// 4. max_deep from w3af controling
// 5. replace console.log with casper.log()
//
var casper, current_deep, max_deep, process_page, target, target_domain, states, to_visit, terminate_url;

casper = require('casper').create();
current_deep = 0;
max_deep = 3;
states = [];
to_visit = []

var casper = require('casper').create({
    verbose: false,
    logLevel: "debug"
});

target = casper.cli.get(0);
terminate_url = casper.cli.get(0);
to_visit.push(target);

function get_domain(url) {
    chunks = url.split('/');
    return chunks[2];
}

target_domain = get_domain(target);

function getClickable() {
    // 
    // http://stackoverflow.com/questions/4588119/get-elements-css-selector-without-element-id
    //
    function fullPath(el) {
      var names = [];
      while (el.parentNode) {
        if (el.id) {
          names.unshift('#'+el.id);
          break;
        } else {
          for (var c=1,e=el; e.previousElementSibling; e=e.previousElementSibling, c++);
          names.unshift(el.tagName+":nth-child("+c+")");
          el = el.parentNode;
        }
      }
      return names.join(" > ");
    }

    var links =  __utils__.findAll('a, img');
    var paths = [];
    for (var i=0; i<links.length; i++) {
        var tmp = {
            url: null, 
            href: links[i].getAttribute('href'),
            path: fullPath(links[i])
        };
        paths.push(tmp);
    }
    return paths;
}

casper.start(target, function() {});

process_page = function() {
    var url;
    if (to_visit.length > 0) {
        url = to_visit.pop();
        states.push(url)
    } else {
        return;
    }
    this.thenOpen(url, function() {
        var links = this.evaluate(getClickable);
        for (var i=0; i<links.length; i++) {
            this.echo('Click on "' + links[i].path + '" with href "' + links[i].href + '"');
            if (this.exists(links[i].path)) {
                this.thenClick(links[i].path).then(function(){
                    this.wait(300, function() {
                        var tmp_url = this.getCurrentUrl();
                        if (url !== tmp_url) {
                            this.echo('We are inside "' + tmp_url + '". Lets go back!' );
                            if (get_domain(tmp_url) == target_domain) {
                                if (states.indexOf(tmp_url) == -1) {
                                    to_visit.push(tmp_url)
                                }
                            }
                            this.back();
                        }
                    });
                });
            } else {
                this.echo(links[i].path + ' doesnt exist on ' + this.getCurrentUrl());
            }
        }
    });
};

for (var i=0; i<=max_deep; i++) {
    casper.then(process_page);
}

casper.then(function() {
    this.echo('=====================')
    this.echo('States:');
    this.each(states, function(self, state) {this.echo(' '+state)});
    if (to_visit.length) {
        this.echo('To visit:');
        this.each(to_visit, function(self, state) {this.echo(' '+state)});
    }
});
casper.thenOpen(terminate_url, function(){});
casper.run(function() {
    this.echo('Quit').exit();
});

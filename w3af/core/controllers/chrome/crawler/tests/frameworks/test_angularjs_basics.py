"""
test_angular_basics.py

Copyright 2019 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
import pytest

from w3af.core.controllers.chrome.crawler.tests.base import BaseChromeCrawlerTest
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler


@pytest.mark.skip('uses internet')
class AngularBasicTest(BaseChromeCrawlerTest):
    def test_angular_click(self):
        self._unittest_setup(AngularButtonClickRequestHandler)
        self._crawl(self.url.url_string)

        expected_messages = '''
        Dispatching "click" on CSS selector "button"
        Chrome handled an alert dialog generated by the page
        The JS crawler found a total of 1 event listeners
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])

    def test_angular_two_button_click_103(self):
        self._unittest_setup(AngularTwoButtonClickRequestHandler103)
        self._crawl(self.url.url_string)

        expected_messages = '''
        Dispatching "click" on CSS selector "[ng-click="spicy
        Chrome handled an alert dialog generated by the page. The message was: "chili"
        Dispatching "click" on CSS selector "[ng-click="spicy
        Chrome handled an alert dialog generated by the page. The message was: "undefined"
        Already processed 2 events with types: {u'click': 2}
        The JS crawler found a total of 2 event listeners
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])

    def test_angular_two_button_click_179(self):
        self._unittest_setup(AngularTwoButtonClickRequestHandler103)
        self._crawl(self.url.url_string)

        expected_messages = '''
        Dispatching "click" on CSS selector "[ng-click="spicy
        Chrome handled an alert dialog generated by the page. The message was: "chili"
        Dispatching "click" on CSS selector "[ng-click="spicy
        Chrome handled an alert dialog generated by the page. The message was: "undefined"
        Already processed 2 events with types: {u'click': 2}
        The JS crawler found a total of 2 event listeners
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])

    @pytest.mark.deprecated
    def test_angular_example_conduit(self):
        url = 'https://angularjs.realworld.io/'

        self._crawl(url)

        expected_messages = '''
        GET https://conduit.productionready.io/api/articles?limit=10&offset=0
        GET https://conduit.productionready.io/api/profiles/
        GET https://conduit.productionready.io/api/tags
        GET https://conduit.productionready.io/api/articles?author=       
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])


class AngularButtonClickRequestHandler(ExtendedHttpRequestHandler):
    # Live at http://embed.plnkr.co/F7TcI8/preview
    RESPONSE_BODY = '''\
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8" />
                        <title>ng-click in AngularJs</title>
                        <script src="https://code.angularjs.org/1.4.1/angular.js"></script>
                        <script>
                            var app = angular.module('myApp', []);
                            app.controller('ngClickCtrl', ["$scope", function ($scope) {
                                $scope.domain = "code-sample.com";
                                $scope.IsDisplay = false;
                                $scope.clickMe = function (clicked) {
                                        alert(" My Click function is called.");
                                    $scope.IsDisplay = clicked == true ? false : true;
                                };
                            }]);
                        </script>
                    </head>
                    <body ng-app="myApp">
                        <div ng-controller="ngClickCtrl">
                            <div><h2>ng-click in AngularJs</h2> </div>
                            <div>
                                Domain name:
                                    <input type="text" ng-model="domain">
                                    <button type="button" ng-click="clickMe(IsDisplay)">NG-CLICK</button>   
                            </div>
                            <div>
                                <div ng-show="IsDisplay">
                                    My Click function is called.
                                    <br />
                                    <h3 style="color:green;">Display User detail: {{domain}} </h3>
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                    '''


class AngularTwoButtonClickRequestHandler103(ExtendedHttpRequestHandler):
    # Live at http://embed.plnkr.co/zbGwOkhPB8m60ChTtOQj
    RESPONSE_BODY = '''\
                    <!DOCTYPE html>
                    <html ng-app="angularjs-starter">
                      
                      <head lang="en">
                        <meta charset="utf-8">
                        <title>Controller example Plunker</title>
                        <script src="//ajax.googleapis.com/ajax/libs/angularjs/1.0.3/angular.min.js"></script>
                        <link rel="stylesheet" href="style.css">
                        <script>
                          document.write('<base href="' + document.location + '" />');
                        </script>
                        <script>
                          var app = angular.module('angularjs-starter', []);
                    
                          app.controller('SpicyCtrl', function($scope) {
                            $scope.spice = 'very';
                            $scope.spicy = function(spice) {
                              $scope.spice = spice;
                              alert(spice);
                            };
                          });
                    
                        </script>
                      </head>
                      
                      <body>
                        <h1>Welcome</h1>
                        <div>Controller example</div>
                        
                        <div ng-controller="SpicyCtrl">
                          <input ng-model="customSpice" />
                          <button ng-click="spicy('chili')">Chili</button>
                          <button ng-click="spicy(customSpice)">Custom spice</button>
                          <p>The food is {{spice}} spicy!</p>
                        </div>
                        
                        
                      </body>
                    
                    </html>
                    '''


class AngularTwoButtonClickRequestHandler179(ExtendedHttpRequestHandler):
    """
    Same as AngularTwoButtonClickRequestHandler103 but with different angularjs version
    """
    RESPONSE_BODY = '''\
                    <!DOCTYPE html>
                    <html ng-app="angularjs-starter">

                      <head lang="en">
                        <meta charset="utf-8">
                        <title>Controller example Plunker</title>
                        <script src="//ajax.googleapis.com/ajax/libs/angularjs/1.7.9/angular.min.js"></script>
                        <link rel="stylesheet" href="style.css">
                        <script>
                          document.write('<base href="' + document.location + '" />');
                        </script>
                        <script>
                          var app = angular.module('angularjs-starter', []);

                          app.controller('SpicyCtrl', function($scope) {
                            $scope.spice = 'very';
                            $scope.spicy = function(spice) {
                              $scope.spice = spice;
                              alert(spice);
                            };
                          });

                        </script>
                      </head>

                      <body>
                        <h1>Welcome</h1>
                        <div>Controller example</div>

                        <div ng-controller="SpicyCtrl">
                          <input ng-model="customSpice" />
                          <button ng-click="spicy('chili')">Chili</button>
                          <button ng-click="spicy(customSpice)">Custom spice</button>
                          <p>The food is {{spice}} spicy!</p>
                        </div>


                      </body>

                    </html>
                    '''

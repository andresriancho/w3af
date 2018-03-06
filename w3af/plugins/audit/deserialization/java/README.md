## Build the ysoserial tool

```
git clone https://github.com/frohoff/ysoserial.git
cd ysoserial
mvn clean package -DskipTests
cd target
cp ysoserial-0.0.6-SNAPSHOT-all.jar ~/tools/w3af/w3af/plugins/audit/deserialization/java/
```

## Run the generator

```
cd w3af/plugins/audit/deserialization/java/
python generator.py
```

## Testing the payloads

Start the deserialize server:

```
git clone https://github.com/yolosec/deserialize-server.git
./gradlew bootRun
```

Take one of the payloads from the JSON file and send it:

```
curl  --insecure 'http://localhost:8222/suffer' -d 'PAYLOAD'
```

Or send all payloads:

```
grep 'payload' *json | cut -d '"' -f 4 | xargs -L1 ./send-payload.sh
```

The expected result is a delay while waiting for the `curl` command
to finish.
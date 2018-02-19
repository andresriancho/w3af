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


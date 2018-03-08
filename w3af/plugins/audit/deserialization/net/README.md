## Introduction

Watch [this video](https://www.youtube.com/watch?v=ZBfBYoK_Wr0).

## Install the software

The ysoserial.net application only works in windows + visual studio.

You will have to install Windows, Visual Studio, and then get the
tool from: `git clone https://github.com/pwntester/ysoserial.net.git`

After building the tool you'll get a `ysoserial.exe`, now you're
ready to create some payloads.

## Creating payloads

Run this command to create the payload:

```
ysoserial.exe -o base64 -g ObjectDataProvider -f FastJson -c "FOR /L %A IN (0,1,77) do ping localhost -n 2"
```

Redirect the payload to a shared folder, so you can gain access to it
from Linux and then insert it into the `generator.py`.

Change the `77` number in the for loop in order to modify how much time to delay.

## Status

[These comments]()https://github.com/andresriancho/w3af/issues/16280#issuecomment-371280578)
show the status of the .NET payloads.

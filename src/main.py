import os
from modes.gateway import gateway
from modes.publisher import publisher
from modes.subscriber import subscriber

mode = os.environ.get("MODE", "")
print("Mode: " + mode)
if mode == "publisher":
    publisher()
elif mode == "subscriber":
    subscriber()
elif mode == "gateway":
    gateway()

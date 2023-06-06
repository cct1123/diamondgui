import os
import time
import datetime
pid = os.getpid()
print(pid)
# import dash
for i in range(10):
    time.sleep(0.001)
    print(f"I am dumdum No.{i+1}, the time now is '{datetime.datetime.now()}'")


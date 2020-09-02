#!/usr/bin/env python
# encoding: utf-8

import time
import sys
import re

def replace_func(s):
    datestr = s.group();
    if s.group(3) is not None:
        fmt = '%a %b %d %H:%M:%S %Z %Y'
    else:
        fmt = '%a %b %d %H:%M:%S %Y'
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.strptime(datestr,fmt))

for line in sys.stdin.readlines():
    timeStr = re.sub(r'(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2}(\s+[a-zA-Z]{3})?\s+\d{4}',replace_func,line)
    print(timeStr)

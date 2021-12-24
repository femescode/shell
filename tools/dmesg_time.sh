#!/bin/bash

dmesg | awk 'BEGIN{getline <"/proc/uptime";s=int($1)} match($0,/^\[(\w+)\.\w+\]/,l){$1=strftime("%FT%T%z", systime()-s+l[1]); print $0}'

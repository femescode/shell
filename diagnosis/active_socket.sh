#!/bin/bash

t="${1:-2000}"
ss -natpeoi | sed '1!{N;s/\n//;}' | awk -v t=$t ' match($0,/lastsnd:([0-9]+)/,a) && a[1]<t'
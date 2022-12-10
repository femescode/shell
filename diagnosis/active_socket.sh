#!/bin/bash

b="${1:-0}"
e="${2:-2000}"
ss -natpeoi | sed '1!{N;s/\n//;}' | awk -v b=$b -v e=$e ' match($0,/lastsnd:([0-9]+)/,a) && a[1]>b && a[1]<e'
#!/bin/bash

awk -v P="$1" 'function gettime(l){return systime()} match($0,P,a){t=gettime($0);if(!pt){pt=t};if(t-pt>=1){print i/(t-pt);pt=t;i=0};i++}'

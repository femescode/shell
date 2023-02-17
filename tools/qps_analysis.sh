#!/bin/bash

grep  --line-buffered -P "${1:-.}" | awk 'function gettime(l){return systime()} 
    {
        t=gettime($0);
        if(!pt){pt=t}
        if(t-pt>=1){print i/(t-pt);pt=t;i=0}
        i++
    }'

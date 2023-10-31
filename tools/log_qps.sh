#!/bin/bash

if [[ "$#" -lt 2 ]];then
    echo "Usage: $0 Error app_*.log" >&2;
    exit 1;
fi

pat="$1";
shift 1;

tail -n 0 -f "$@" | grep  --line-buffered -P  | awk 'function gettime(l){return systime()} 
    {
        t=gettime($0);
        if(!pt){pt=t}
        if(t-pt>=1){print i/(t-pt);pt=t;i=0}
        i++
    }'

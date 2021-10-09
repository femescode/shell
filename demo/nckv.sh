#!/bin/bash

# usage: ncat -lk 8080 -e nckv.sh

storefile="/tmp/tmp.516mtLp8Uk"
echo "The store file: $storefile"  >&2
while read c k v; do
    case "$c" in
        set) echo "$k:$v" >> "$storefile" ;;
        get) tac "$storefile" | grep -m1 -oP "^$k:\K.*" ;;
        del) echo "$k:" >> "$storefile" ;;
        getall) cat "$storefile" | awk 'match($0,/^([^:]+):(.*)/,a){ if(a[2]){ S[a[1]]=a[2] }else{ delete S[a[1]] } } END{for(k in S){print k " -> " S[k]}}' ;;
        help|*) [[ -n "$c" ]] && echo -e "Usage:\n 1) set k v \n 2) get k \n 3) del k \n 4) getall" ;;
    esac
done

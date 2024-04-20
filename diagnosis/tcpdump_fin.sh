#!/bin/bash

if [[ $# -lt 1 || $@ =~ '-h' || $@ =~ '--help' ]]; then
    echo -e "Trace peer side active close tcp connection." >&2
    echo -e "Usage: bash tcpdump_fin.sh 'tcp and port 80' 80" >&2
    exit 1
fi

tcpdump -tttt -i any -l -nnn -A -s 1024 "$1" |stdbuf -oL sed 's/^202[4-9]-/b361528a75ef11ed86d800155d5fe859 &/'| awk -v RS=b361528a75ef11ed86d800155d5fe859 -v port="${2:-80}" '
function append(    arr,item,limit){
    min_idx=0
    max_idx=0
    PROCINFO["sorted_in"] = "@ind_num_asc";
    for(i in arr){
        if(min_idx==0){
            min_idx=i
        }
        max_idx=i
    }
    arr[max_idx+1]=item
    # print "offer:" (max_idx+1) "\t" item
    if(length(arr) > limit){
        if(min_idx > 0){
            # print "pop:" min_idx "\t" arr[min_idx]
            delete arr[min_idx]
        }
    }
}
{
    split($4,s,/\./)
    $6=gensub(/:$/, "", "g", $6)
    split($6,d,/\./)
    if($7 != "Flags" || $8 ~ /\[.\]/){
        next
    }
    dstport = d[length(d)]
    if(int(dstport) == port){
        key = $4 "-" $6
        cmap[key][0]=0
        delete cmap[key][0]
        if($8 !~ /F/){
            append(cmap[key], $0, 2)
        }else{
            delete cmap[key]
        }
    }else{
        key = $6 "-" $4
        cmap[key][0]=0
        delete cmap[key][0]
        if($8 !~ /F/){
            append(cmap[key], $0, 2)
        }else{
            if(length(cmap[key])>0){
                print "peer close"
                sb=""
                PROCINFO["sorted_in"] = "@ind_num_asc";
                for(i in cmap[key]){
                    sb = sb "\n" cmap[key][i]
                    last = cmap[key][i]
                }
                if(last !~ /Connection: close/){
                    print sb
                    print $0
                    fflush()
                    # exit(0)
                }
            }
            delete cmap[key]
        }
    }
}' 

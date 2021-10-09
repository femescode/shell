#!/bin/bash

# usage: echo "my name is user_id"|bash replace_by_grep.sh '\w+(_\w+)+'

pat=$1
sb=""
IFS="\n"
while read -r line;do
    let pre_end=0;
    while read -r cw;do
        if [[ ! $cw ]];then
            continue;
        fi
        let cur_idx=$(cut <<<"$cw" -d: -f1)
        cur_str=$(cut <<<"$cw" -d: -f2-)
        let cur_len=${#cur_str}
        pre_str=${line:$pre_end:$(($cur_idx-$pre_end))}
        replace_str=$(echo -n "$cur_str"|sed 's/_/ /g'|sed 's/\b./\u&/g'|sed 's/ //g'|sed 's/^./\l&/g')
        sb="$sb$pre_str$replace_str"
        let pre_end=$(($cur_idx + $cur_len))
    done <<< $(grep <<<"$line" -b -oP "$pat")
    sb="$sb${line:$pre_end}"$'\n'
done
echo -n "$sb"

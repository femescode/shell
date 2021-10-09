#!/bin/bash

# usage: echo "my name is user_id" | bash replace_by_bash.sh

IFS=$'\n';
while read -r line;do
        if [[ $line =~ ([a-z]+(_[a-z]+)+) ]];then
                rep=$(echo ${BASH_REMATCH[1]}|sed 's/_/ /g'|sed 's/\b./\u&/g'|sed 's/ //g'|sed 's/^./\l&/g');
                echo ${line/${BASH_REMATCH[1]}/$rep};
        else
                echo $line;
        fi;
done

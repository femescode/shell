#!/bin/bash

log_prefix(){
    echo -n "[$(date +'%Y-%m-%d %H:%M:%S')] [monitorJvm] [$(ifconfig|awk -v RS= '/eth0/{print $6}')] [INFO] hostname: $(hostname) $@"
}

logfile="$1";
while sleep 1; do
    res=$(curl --connect-timeout 2 --max-time 2 -sS http://localhost:8080/healthCheck/serviceExistence 2>&1|tr '\r\n' ' ')
    echo $res
    if [[ ! $res =~ "ok" ]];then
        { log_prefix; bash <(curl -sS https://gitee.com/fmer/shell/raw/master/diagnosis/system_and_jvm_info.sh) 2|sed -z 's/\n/\\n/g' ; } >> $logfile
    fi
done



#!/bin/bash

kill_connection(){
    read local_ip local_port remote_ip remote_port <<<"$@"
    seqno=$(hping3 $local_ip -a $remote_ip -s $remote_port -p $local_port --syn -V -c 1 |grep -oP 'ack=\K\d+')
    if [[ $seqno ]]; then
        echo "kill-connect:$local_ip:$local_port->$remote_ip:$remote_port, seq:$seqno"
        hping3 $local_ip -a $remote_ip -s $remote_port -p $local_port --rst --win 0 --setseq $seqno -q -c 1 &>/dev/null
    fi
}
while read state recv_q send_q local_addr remote_addr; do
    IFS=: read local_ip local_port <<<"$local_addr"
    IFS=: read remote_ip remote_port <<<"$remote_addr"
    kill_connection $local_ip $local_port $remote_ip $remote_port
    kill_connection $remote_ip $remote_port $local_ip $local_port
done < <(ss -nt "$@" | sed 1d)

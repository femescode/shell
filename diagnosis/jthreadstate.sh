#!/bin/bash

awk_script='
/^"/ && NF>30 {
    s = $0;
    match(s,/^"([^"]+)"/,m);
    name = gensub(/[0-9]+/, "n", "g", m[1]);

    if(match(s,/java.lang.Thread.State: (\w+)/,m)){
        state = m[1];
    }else{
        if(match(s,/nid=\w+ Object.wait\(\)/,m)){
            state = "WAITING"
        }else if(match(s,/nid=\w+ waiting on condition/,m)){
            state = "WAITING";
        }else if(match(s,/nid=\w+ runnable/,m)){
            state = "RUNNABLE";
        }
    }
    if(state == "BLOCKED"){
        state = "SYNCHRONIZED"
    }else if(state == "TIMED_WAITING" && match(s,/java.lang.Thread.sleep/,m)){
        state = "SLEEP"
    }else if(state == "WAITING" && match(s,/AbstractQueuedSynchronizer.acquire/,m)){
        state = "WAIT_LOCK"
    }else if(state == "WAITING" && match(s,/ThreadPoolExecutor.getTask/,m)){
        state = "WAIT_TASK"
    }else if(state == "RUNNABLE" && match(s,/SelectorImpl.select/,m)){
        state = "WAIT_EPOLL"
    }else if(state == "RUNNABLE" && match(s,/com.mysql.jdbc.MysqlIO/,m)){
        state = "WAIT_MYSQL"
    }else if(state == "RUNNABLE" && match(s,/CloseableHttpClient.execute/,m)){
        state = "WAIT_HTTP"
    }else if(state == "RUNNABLE" && match(s,/java.net.SocketInputStream.read/,m)){
        state = "WAIT_SOCKET"
    }
    
    method=""
    n=0
    for(i=1;i<=NF;i++){
        if(!match($i,/^\s*at \w+\./,m)){
            continue;
        }
        if(match($i,/^\s*at (java|javax|sun)\./,m)){
            continue;
        }
        method = method ? (method "\n" $i) : $i
        n++
        if(n >= 4){
            break;
        }
    }
    method = method ? method : "-"

    
    S[name "\t" state "\n" method]++
}
END{
    asorti(S,sorted_key_arr,"@val_num_desc") 
    for(i in sorted_key_arr){
        thread_key=sorted_key_arr[i]
        print S[thread_key],thread_key
    }
}
'

pid="$1"
[[ ! "$pid" ]] && { pid=`ps h -o pid --sort=-pmem -C java|head -n1`; }
[[ ! "$pid" ]] && { echo 'not found java process, usage: $0 pid' >&2; exit 1; }

jstack $pid|awk -F'\n' -v RS= "$awk_script" 

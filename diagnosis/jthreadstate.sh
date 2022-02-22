#!/bin/bash

awk_script='
/^"/{
    s = $0;
    match(s,/^"([^"]+)"/,m);
    name = m[1];
    match(s,/java.lang.Thread.State: (\w+)/,m);
    state = m[1];
    if(state == "BLOCKED"){
        state = "wait_synchronized"
    }else if(state == "TIMED_WAITING" && match(s,/java.lang.Thread.sleep/,m)){
        state = "sleep"
    }else if(state == "WAITING" && match(s,/AbstractQueuedSynchronizer.acquire/,m)){
        state = "wait_lock"
    }else if(state == "WAITING" && match(s,/ThreadPoolExecutor.getTask/,m)){
        state = "wait_task"
    }else if(state == "RUNNABLE" && match(s,/SelectorImpl.select/,m)){
        state = "wait_epoll"
    }else if(state == "RUNNABLE" && match(s,/com.mysql.jdbc.MysqlIO/,m)){
        state = "wait_mysql"
    }else if(state == "RUNNABLE" && match(s,/java.net.SocketInputStream.read/,m)){
        state = "wait_sock_read"
    }
    print name "\t" state;
}
'

pid="$1"
[[ ! "$pid" ]] && { pid=`ps h -o pid --sort=-pmem -C java|head -n1`; }
[[ ! "$pid" ]] && { echo 'not found java process, usage: $0 pid' >&2; exit 1; }

jstack $pid|tr -d '\n'|sed -E 's/("[^"]+")/\n\1/g'|awk "$awk_script" |sed -E 's/[0-9]+/n/g'|sort|uniq -c|sort -nr|column -t -s$'\t'
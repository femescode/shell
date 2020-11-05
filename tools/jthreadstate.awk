#!/usr/bin/awk -f

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

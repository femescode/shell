#!/usr/bin/env python
# encoding: utf-8

import re,datetime,time,json,sys,argparse,subprocess,os,io
from collections import defaultdict
from functools import cmp_to_key
import traceback

DEV_NULL = os.open(os.devnull, os.O_RDWR)

syscall_all = "0:read 1:write 2:open 3:close 4:stat 5:fstat 6:lstat 7:poll 8:lseek 9:mmap 10:mprotect 11:munmap 12:brk 13:rt_sigaction 14:rt_sigprocmask 15:rt_sigreturn 16:ioctl 17:pread64 18:pwrite64 19:readv 20:writev 21:access 22:pipe 23:select 24:sched_yield 25:mremap 26:msync 27:mincore 28:madvise 29:shmget 30:shmat 31:shmctl 32:dup 33:dup2 34:pause 35:nanosleep 36:getitimer 37:alarm 38:setitimer 39:getpid 40:sendfile 41:socket 42:connect 43:accept 44:sendto 45:recvfrom 46:sendmsg 47:recvmsg 48:shutdown 49:bind 50:listen 51:getsockname 52:getpeername 53:socketpair 54:setsockopt 55:getsockopt 56:clone 57:fork 58:vfork 59:execve 60:exit 61:wait4 62:kill 63:uname 64:semget 65:semop 66:semctl 67:shmdt 68:msgget 69:msgsnd 70:msgrcv 71:msgctl 72:fcntl 73:flock 74:fsync 75:fdatasync 76:truncate 77:ftruncate 78:getdents 79:getcwd 80:chdir 81:fchdir 82:rename 83:mkdir 84:rmdir 85:creat 86:link 87:unlink 88:symlink 89:readlink 90:chmod 91:fchmod 92:chown 93:fchown 94:lchown 95:umask 96:gettimeofday 97:getrlimit 98:getrusage 99:sysinfo 100:times 101:ptrace 102:getuid 103:syslog 104:getgid 105:setuid 106:setgid 107:geteuid 108:getegid 109:setpgid 110:getppid 111:getpgrp 112:setsid 113:setreuid 114:setregid 115:getgroups 116:setgroups 117:setresuid 118:getresuid 119:setresgid 120:getresgid 121:getpgid 122:setfsuid 123:setfsgid 124:getsid 125:capget 126:capset 127:rt_sigpending 128:rt_sigtimedwait 129:rt_sigqueueinfo 130:rt_sigsuspend 131:sigaltstack 132:utime 133:mknod 134:uselib 135:personality 136:ustat 137:statfs 138:fstatfs 139:sysfs 140:getpriority 141:setpriority 142:sched_setparam 143:sched_getparam 144:sched_setscheduler 145:sched_getscheduler 146:sched_get_priority_max 147:sched_get_priority_min 148:sched_rr_get_interval 149:mlock 150:munlock 151:mlockall 152:munlockall 153:vhangup 154:modify_ldt 155:pivot_root 156:_sysctl 157:prctl 158:arch_prctl 159:adjtimex 160:setrlimit 161:chroot 162:sync 163:acct 164:settimeofday 165:mount 166:umount2 167:swapon 168:swapoff 169:reboot 170:sethostname 171:setdomainname 172:iopl 173:ioperm 174:create_module 175:init_module 176:delete_module 177:get_kernel_syms 178:query_module 179:quotactl 180:nfsservctl 181:getpmsg 182:putpmsg 183:afs_syscall 184:tuxcall 185:security 186:gettid 187:readahead 188:setxattr 189:lsetxattr 190:fsetxattr 191:getxattr 192:lgetxattr 193:fgetxattr 194:listxattr 195:llistxattr 196:flistxattr 197:removexattr 198:lremovexattr 199:fremovexattr 200:tkill 201:time 202:futex 203:sched_setaffinity 204:sched_getaffinity 205:set_thread_area 206:io_setup 207:io_destroy 208:io_getevents 209:io_submit 210:io_cancel 211:get_thread_area 212:lookup_dcookie 213:epoll_create 214:epoll_ctl_old 215:epoll_wait_old 216:remap_file_pages 217:getdents64 218:set_tid_address 219:restart_syscall 220:semtimedop 221:fadvise64 222:timer_create 223:timer_settime 224:timer_gettime 225:timer_getoverrun 226:timer_delete 227:clock_settime 228:clock_gettime 229:clock_getres 230:clock_nanosleep 231:exit_group 232:epoll_wait 233:epoll_ctl 234:tgkill 235:utimes 236:vserver 237:mbind 238:set_mempolicy 239:get_mempolicy 240:mq_open 241:mq_unlink 242:mq_timedsend 243:mq_timedreceive 244:mq_notify 245:mq_getsetattr 246:kexec_load 247:waitid 248:add_key 249:request_key 250:keyctl 251:ioprio_set 252:ioprio_get 253:inotify_init 254:inotify_add_watch 255:inotify_rm_watch 256:migrate_pages 257:openat 258:mkdirat 259:mknodat 260:fchownat 261:futimesat 262:newfstatat 263:unlinkat 264:renameat 265:linkat 266:symlinkat 267:readlinkat 268:fchmodat 269:faccessat 270:pselect6 271:ppoll 272:unshare 273:set_robust_list 274:get_robust_list 275:splice 276:tee 277:sync_file_range 278:vmsplice 279:move_pages 280:utimensat 281:epoll_pwait 282:signalfd 283:timerfd_create 284:eventfd 285:fallocate 286:timerfd_settime 287:timerfd_gettime 288:accept4 289:signalfd4 290:eventfd2 291:epoll_create1 292:dup3 293:pipe2 294:inotify_init1 295:preadv 296:pwritev 297:rt_tgsigqueueinfo 298:perf_event_open 299:recvmmsg 300:fanotify_init 301:fanotify_mark 302:prlimit64 303:name_to_handle_at 304:open_by_handle_at 305:clock_adjtime 306:syncfs 307:sendmmsg 308:setns 309:getcpu 310:process_vm_readv 311:process_vm_writev 312:kcmp 313:finit_module 314:sched_setattr 315:sched_getattr 316:renameat2 317:seccomp 318:getrandom 319:memfd_create 320:kexec_file_load 321:bpf 322:execveat 323:userfaultfd 324:membarrier 325:mlock2 326:copy_file_range 327:preadv2 328:pwritev2 329:pkey_mprotect 330:pkey_alloc 331:pkey_free 332:statx 333:io_pgetevents 334:rseq 424:pidfd_send_signal 425:io_uring_setup 426:io_uring_enter 427:io_uring_register 428:open_tree 429:move_mount 430:fsopen 431:fsconfig 432:fsmount 433:fspick 434:pidfd_open 435:clone3"
syscall_map = {}
for word in syscall_all.split():
    (syscall_id, syscall_name) = word.split(":")
    syscall_map[syscall_id] = syscall_name

syscall_with_fd_set = set(["read","write","pread64","pwrite64","fsync","fdatasync","recvfrom","sendto","recvmsg","sendmsg","epoll_wait","ioctl","accept","accept4"])

special_fd_map = {"0":"(stdin)", "1":"(stdout)", "2":"(stderr)"}

def exists_cmd(cmd):
    return subprocess.call(["which", cmd],stdout=DEV_NULL) == 0

def run_cmd(cmd_args, shell=False):
    proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    stdout, stderr = proc.communicate()
    stdout = stdout.decode('UTF-8')
    stderr = stderr.decode('UTF-8')
    if stderr:
        sys.stderr.write(stderr)
        sys.exit(1)
    return stdout.strip()

def re_search(regex, text, result):
    m = re.search(regex, text)
    result[0] = m
    return m is not None

def get_java_pid():
    return run_cmd("ps h -o pid --sort=-pmem -C java|head -n1", shell=True)

def get_thread_state(text):
    m = [None]
    if re_search(r'java.lang.Thread.State: (\w+)', text, m):
        state = m[0].group(1)
    else:
        if re_search(r'nid=\w+ Object.wait\(\)', text, m):
            state = "WAITING"
        elif re_search(r'nid=\w+ waiting on condition', text, m): 
            state = "WAITING"
        elif re_search(r'nid=\w+ runnable', text, m): 
            state = "RUNNABLE"
    if state == "BLOCKED":
        state = "SYNCHRONIZED"
    elif (state == "TIMED_WAITING" and re_search(r'java.lang.Thread.sleep', text,m)):
        state = "SLEEP"
    elif (state == "WAITING" and re_search(r'AbstractQueuedSynchronizer.acquire', text ,m)):
        state = "WAIT_LOCK"
    elif (state == "WAITING" and re_search(r'ThreadPoolExecutor.getTask', text,m)):
        state = "WAIT_TASK"
    elif (state == "RUNNABLE" and re_search(r'SelectorImpl.select', text,m)):
        state = "WAIT_EPOLL"
    elif (state == "RUNNABLE" and re_search(r'com.mysql.jdbc.MysqlIO', text,m)):
        state = "WAIT_MYSQL"
    elif (state == "RUNNABLE" and re_search(r'CloseableHttpClient.execute', text,m)):
        state = "WAIT_HTTP"
    elif (state == "RUNNABLE" and re_search(r'java.net.SocketInputStream.read', text,m)):
        state = "WAIT_SOCKET"
    return state

def get_thread_info_by_top(pid):
    top_ret = run_cmd("top -d 0.1 -b -n2 -w 207 -H -p %s" % (str(pid)), shell=True)
    thread_text = re.split(r'\n\n+', top_ret)[-1]
    thread_map = {}
    for threadline in thread_text.splitlines():
        if 'PID' in threadline:
            continue
        split_lines = re.split("                                 +", threadline.strip())
        if len(split_lines) == 2:
            thread_fields = re.split(r'\s+',split_lines[0].strip(), maxsplit=11)
        else:
            thread_fields = re.split(r'\s+',threadline.strip(), maxsplit=11)
        tid = int(thread_fields[0])
        thread_map[tid] = {'stat':thread_fields[7], 'cpu':thread_fields[8], 'mem':thread_fields[9], 'cpu_time':thread_fields[10], "threadname": thread_fields[11], "threadstate": thread_fields[7]}
    return thread_map

def get_stack_by_jstack(pid):
    jstack_ret = run_cmd("jstack %s" % (str(pid)), shell=True)
    stack_list = re.split(r'\n\n+', jstack_ret)
    stack_map = {}
    for stackinfo in stack_list:
        stacklines = stackinfo.splitlines()
        m = re.search(r'^"([^"]+)" .* nid=(\w+)', stacklines[0])
        if not m:
            continue
        threadname = m.group(1)
        tid = int(m.group(2),base=16)

        line_list = stacklines[1:]
        stack_info = {'threadname':threadname,'threadstate': get_thread_state(stackinfo),'stack_list':line_list}
        stack_map[tid] = stack_info
    return stack_map

def get_stack_by_pstack(pid):
    pstack_ret = run_cmd(r"pstack %s" % (str(pid)), shell=True)
    stack_map = defaultdict(lambda :{'stack_list':[]})
    tid = 0
    for line in pstack_ret.splitlines():
        m = re.search(r'^Thread.+LWP (\d+)', line)
        if m:
            tid = int(m.group(1))
            continue
        stackframe = re.split(r'\s+', line, 1)[1]
        if re.search(r'^\w+ in ', stackframe):
            stackframe = re.sub(r'^\w+ in ', '        ', stackframe)
        else:
            stackframe = '        ' + stackframe
        stack_map[tid].get('stack_list').append(stackframe)
    return stack_map

def get_kstack_by_proc(pid, tid):
    stackfile = "/proc/%s/task/%s/stack" % (str(pid), str(tid))
    try:
        with io.open(stackfile, "r", encoding='utf-8') as f:
            lines = []
            for stackframe in f.readlines():
                stackframe = stackframe.strip()
                if re.search(r'^[^ ]+ ', stackframe):
                    stackframe = re.sub(r'^[^ ]+ ', '        ', stackframe)
                else:
                    stackframe = '        ' + stackframe
                lines.append(stackframe)
            return lines
    except (IOError) as e:
        if not e.errno in [2,13]:
            sys.stderr.write(traceback.format_exc())
        return []

def get_wchan_by_proc(pid, tid):
    procfile = "/proc/%s/task/%s/wchan" % (str(pid), str(tid))
    try:
        with io.open(procfile, "r", encoding='utf-8') as f:
            return f.read().strip()
    except (IOError) as e:
        if not e.errno in [2,13]:
            sys.stderr.write(traceback.format_exc())
        return []

def get_syscall_by_proc(pid, tid):
    procfile = "/proc/%s/task/%s/syscall" % (str(pid), str(tid))
    try:
        with io.open(procfile, "r", encoding='utf-8') as f:
            return f.read().strip()
    except (IOError) as e:
        if not e.errno in [2,13]:
            sys.stderr.write(traceback.format_exc())
        return []

def jstack_with_cpu(args, pid, has_pstack, has_jstack):
    thread_map = get_thread_info_by_top(pid)
    jstack_map = {}
    if has_jstack and args.java_stack:
        jstack_map = get_stack_by_jstack(pid)
    pstack_map = {}
    if has_pstack and args.user_stack:
        pstack_map = get_stack_by_pstack(pid)
    for tid, thread_info in thread_map.items():
        thread_info["wchan"] = get_wchan_by_proc(pid, tid)
        syscall_arr = get_syscall_by_proc(pid, tid).split()
        syscall_name = syscall_map.get(syscall_arr[0])
        thread_info["syscall"] = syscall_name
        if syscall_name in syscall_with_fd_set:
            fdnum = str(int(syscall_arr[1], 16))
            filename = run_cmd("readlink /proc/%s/fd/%s" % (str(pid), str(fdnum)), shell=True)
            if fdnum in special_fd_map:
                filename = filename + special_fd_map[fdnum]
            thread_info["filename"] = filename

        if args.kernel_stack:
            kstack_list = get_kstack_by_proc(pid, tid)
            thread_info["kstack_list"] = kstack_list

        pstack_info = pstack_map.get(tid)
        if pstack_info:
            pstack_list = pstack_info.get("stack_list")
            thread_info["pstack_list"] = pstack_list
        
        jstack_info = jstack_map.get(tid)
        if jstack_info:
            thread_info["jstack_list"] = jstack_info.get("stack_list")
            thread_info["threadname"] = jstack_info["threadname"]
            thread_info["threadstate"] = jstack_info["threadstate"]
        
    return thread_map

def get_agg_stack_list(thread_info, regex):
    show_stack_list = []
    
    syscall = thread_info.get('syscall')
    if syscall and len(syscall) > 0:
        show_stack_list.append("        ---------------syscall----------------------")
        show_stack_list.append("        " + syscall + ":" + (thread_info.get('filename') or ""))

    wchan = thread_info.get('wchan')
    if wchan and len(wchan) > 0:
        show_stack_list.append("        ---------------wchan----------------------")
        show_stack_list.append("        " + wchan)

    kstack_list = thread_info.get('kstack_list')
    if kstack_list and len(kstack_list) > 0:
        show_stack_list.append("        ---------------kstack----------------------")
        show_stack_list.extend(kstack_list)

    pstack_list = thread_info.get('pstack_list')
    if pstack_list and len(pstack_list) > 0:
        show_stack_list.append("        ---------------pstack----------------------")
        show_stack_list.extend(pstack_list)
    
    jstack_list = thread_info.get('jstack_list')
    if jstack_list and len(jstack_list) > 0:
        show_jstack_list = []
        for stack_line in jstack_list:
            if not re.search(r'^\s*at \w+\.', stack_line):
                continue
            if regex:
                if re.search(regex, stack_line):
                    show_jstack_list.append(stack_line)
            else:
                show_jstack_list.append(stack_line)
        if len(show_jstack_list) > 0:
            show_stack_list.append("        ---------------jstack----------------------")
            show_stack_list.extend(show_jstack_list)
        
    return show_stack_list

def get_single_stack_list(thread_info):
    show_stack_list = []
    
    syscall = thread_info.get('syscall')
    if syscall and len(syscall) > 0:
        show_stack_list.append("        ---------------syscall----------------------")
        show_stack_list.append("        " + syscall + ":" + (thread_info.get('filename') or ""))

    wchan = thread_info.get('wchan')
    if wchan and len(wchan) > 0:
        show_stack_list.append("        ---------------wchan----------------------")
        show_stack_list.append("        " + wchan)

    kstack_list = thread_info.get('kstack_list')
    if kstack_list and len(kstack_list) > 0:
        show_stack_list.append("        ---------------kstack----------------------")
        show_stack_list.extend(kstack_list)

    pstack_list = thread_info.get('pstack_list')
    if pstack_list and len(pstack_list) > 0:
        show_stack_list.append("        ---------------pstack----------------------")
        show_stack_list.extend(pstack_list)
    
    jstack_list = thread_info.get('jstack_list')
    if jstack_list and len(jstack_list) > 0:
        show_jstack_list = []
        for stack_line in jstack_list:
            if re.search(r'^\s*java.lang.Thread.State:', stack_line):
                continue
            show_jstack_list.append(stack_line)
        if len(show_jstack_list) > 0:
            show_stack_list.append("        ---------------jstack----------------------")
            show_stack_list.extend(show_jstack_list)
    
    return show_stack_list

def main():
    parser = argparse.ArgumentParser(description='sample java thread stacktrace by jstack.')
    parser.add_argument("-c", "--count", type=int, default=sys.maxsize, help='record stacktrace count')
    parser.add_argument("-j", "--java_stack", action="store_true", help='show java stack')
    parser.add_argument("-u", "--user_stack", action="store_true", help='show user space stack')
    parser.add_argument("-k", "--kernel_stack", action="store_true", help='show kernel space stack')
    parser.add_argument("-r", "--frame_regex", type=str, help='show stack frame that match regex')
    parser.add_argument("-l", "--show_length", type=int, default=30, help='show stack depth over length')
    args = parser.parse_args()

    for cmd in ["ps", "top"]:
        if not exists_cmd(cmd):
            sys.stderr.write("%s command not found! please install it first. \n" % (cmd))
            sys.exit(1)

    pid = get_java_pid()
    if not pid:
        sys.stderr.write("not found java proccess! \n")
        sys.exit(1)

    has_pstack = False
    if args.user_stack:
        has_pstack = exists_cmd("pstack")
    has_jstack = False
    if args.java_stack:
        has_jstack = exists_cmd("jstack")
    if args.count == 1:
        thread_map = jstack_with_cpu(args, pid, has_pstack, has_jstack)
        for tid,thread_info in thread_map.items():
            stack_text = '\n'.join(get_single_stack_list(thread_info))
            segment_text = "%s \t %s(%s) \t %s(%s) \n%s \n" % (
                str(thread_info.get('cpu')), thread_info.get('threadstate'), thread_info.get('stat'), 
                thread_info.get('threadname'), str(tid), stack_text)
            print(segment_text.strip()+"\n")
    else:
        sys.stderr.write("collect java stacktrace begin, press Ctrl + c to stop... \n")
        agg_map = defaultdict(lambda :{'cpu':0.0,'count':0})
        try:
            i = 0
            while i < args.count:
                thread_map = jstack_with_cpu(args, pid, has_pstack, has_jstack)
                for tid,thread_info in thread_map.items():
                    agg_thread_name = re.sub(r'\d+', 'n', thread_info.get('threadname')) 
                    agg_stack_list = get_agg_stack_list(thread_info, args.frame_regex)
                    agg_stack_text = '\n'.join(agg_stack_list)
                    agg_key = agg_thread_name + agg_stack_text
                    agg_item = agg_map[agg_key]
                    agg_item["cpu"] = agg_item['cpu'] + float(thread_info.get('cpu'))
                    agg_item["count"] = agg_item['count'] + 1
                    agg_item["threadname"] = agg_thread_name
                    agg_item["stack"] = agg_stack_text
                    agg_item["stack_len"] = len(agg_stack_list)
                time.sleep(0.2)
                i = i + 1
        except (SystemExit, KeyboardInterrupt) as e:
            print("")
            pass

        def sort_by_cpu(o1, o2):
            return o1[1].get('cpu') - o2[1].get('cpu')
        agg_items = list(agg_map.items())
        agg_items.sort(key=cmp_to_key(sort_by_cpu), reverse=True)
        for agg_key,agg_info in agg_items:
            cpu = agg_info.get('cpu')
            count = agg_info.get('count')
            if args.show_length > 0 and agg_info.get('stack_len') <= args.show_length and (cpu < 10.0) :
                continue
            segment_text = "%s \t %s \t %s \n%s \n" % (
                str(cpu), str(count), agg_info.get('threadname'), agg_info.get('stack'))
            print(segment_text.strip()+"\n")

main()
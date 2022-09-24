#!/usr/bin/env python
# encoding: utf-8

import re,datetime,time,json,sys,argparse,subprocess,os,io
from collections import defaultdict
from functools import cmp_to_key
import traceback

DEV_NULL = os.open(os.devnull, os.O_RDWR)

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

def jstack_with_cpu(args, pid, has_pstack, has_jstack):
    thread_map = get_thread_info_by_top(pid)
    jstack_map = {}
    if has_jstack and args.java_stack:
        jstack_map = get_stack_by_jstack(pid)
    pstack_map = {}
    if has_pstack and args.user_stack:
        pstack_map = get_stack_by_pstack(pid)
    for tid, thread_info in thread_map.items():
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
        agg_items = agg_map.items()
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
#!/usr/bin/env python
# encoding: utf-8

import collections
import re,datetime,time,json,sys,argparse,subprocess,os
from collections import defaultdict
from functools import cmp_to_key

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

def jstack_with_cpu(pid):
    top_ret = run_cmd("top -d 0.1 -b -n2 -H -p %s" % (str(pid)), shell=True)
    thread_text = re.split(r'\n\n+', top_ret)[-1]
    thread_map = {}
    for threadline in thread_text.splitlines():
        if 'PID' in threadline:
            continue
        thread_fields = threadline.strip().split()
        tid = int(thread_fields[0])
        thread_map[tid] = {'stat':thread_fields[7], 'cpu':thread_fields[8], 'mem':thread_fields[9], 'cpu_time':thread_fields[10]}
    
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
        stack_info = {'threadname':threadname,'threadstate': get_thread_state(stackinfo),'stack_list':line_list, 'stack_len': len(line_list)}
        thread_info = thread_map.get(tid)
        if not thread_info:
            continue
        stack_map[tid] = {'thread_info':thread_info, 'stack_info': stack_info}
    return stack_map

def get_agg_text(stack_data, show_len, regex):
    stack_info = stack_data.get('stack_info')

    show_thread_name = re.sub(r'\d+', 'n', stack_info.get('threadname')) 
    show_stack_list = []
    i = 0
    j = 0
    for stack_line in stack_info.get('stack_list'):
        i = i + 1
        if i <= 3 or show_len > len(stack_info.get('stack_list')):
            show_stack_list.append(stack_line)
            if i == 3:
                show_stack_list.append('        ...')
        
        if not re.search(r'^\s*at \w+\.', stack_line):
            continue
        if re.search(r'^\s*at (java|javax|sun)\.', stack_line):
            continue
        j = j + 1
        if j <= show_len:
            show_stack_list.append(stack_line)
            if j == show_len:
                show_stack_list.append('        ...')
        
        if not regex or not re.search(regex, stack_line):
            continue
        show_stack_list.append(stack_line)
    return "%s \t %s \n %s \n" % (stack_info.get('threadstate'), show_thread_name, '\n'.join(show_stack_list))

def main():
    parser = argparse.ArgumentParser(description='sample java thread stacktrace by jstack.')
    parser.add_argument("-l", "--show_length", type=int, default=8, help='stacktrace show length')
    parser.add_argument("-r", "--regex", type=str, help='stacktrace filter regex')
    parser.add_argument("-f", "--filter_length", type=int, default=30, help='stacktrace filter length')
    parser.add_argument("-n", "--num", type=int, default=sys.maxint, help='record stacktrace num')
    args = parser.parse_args()

    for cmd in ["ps", "top", "jstack"]:
        if not exists_cmd(cmd):
            sys.stderr.write("%s command not found! please install it first. \n" % (cmd))
            sys.exit(1)

    pid = get_java_pid()
    if not pid:
        sys.stderr.write("not found java proccess! \n")
        sys.exit(1)

    sys.stderr.write("collect java stacktrace begin, press Ctrl + c to stop... \n")
    agg_map = defaultdict(lambda :{'cpu':0.0,'count':0})
    try:
        i = 0
        while i < args.num:
            stack_map = jstack_with_cpu(pid)
            for tid,stack_data in stack_map.items():
                agg_text = get_agg_text(stack_data, args.show_length, args.regex)
                cpu = float(stack_data.get('thread_info').get('cpu'))
                newcpu = agg_map[agg_text].get('cpu') + cpu
                newcount = agg_map[agg_text].get('count') + 1
                agg_map[agg_text]["cpu"] = newcpu
                agg_map[agg_text]["count"] = newcount
                agg_map[agg_text]["stack_len"] = stack_data.get('stack_info').get('stack_len')
            time.sleep(0.2)
            i = i + 1
    except (SystemExit, KeyboardInterrupt) as e:
        print("")
        pass

    def sort_by_cpu(o1, o2):
        return o1[1].get('cpu') - o2[1].get('cpu')
    agg_items = agg_map.items()
    agg_items.sort(key=cmp_to_key(sort_by_cpu), reverse=True)
    for agg_text,val in agg_items:
        cpu = val.get('cpu')
        count = val.get('count')
        stack_len = val.get('stack_len')
        if (not cpu > 0.0) and stack_len <= args.filter_length:
            continue
        print(str(cpu) + "\t" + str(count) + "\t" + agg_text)

main()
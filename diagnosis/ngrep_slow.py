#!/usr/bin/env python
# coding:utf-8

import collections
import io
import re,datetime,time,json,sys,argparse,subprocess,os
import tempfile

DEV_NULL = os.open(os.devnull, os.O_RDWR)

def exists_cmd(cmd):
    return subprocess.call(["which", cmd],stdout=DEV_NULL) == 0

def cost_show(cost):
    if cost > 1:
        return "%.3fs" % (cost)
    if cost * 1000 > 1:
        return "%.3fms" % (cost * 1000)
    if cost * 1000000 > 1:
        return "%.0fus" % (cost * 1000000)
    return str(cost) + 's'

def trace_ngrep_slow(args, inputStream, outputStream):
    pre_packet_map = {}
    for line in iter(inputStream.readline, b''):
        if not line:
            continue
        if outputStream:
            outputStream.write(line)
        line=line.strip()
        if not line.startswith('T '):
            continue
        columns = line.split(" ", 7)
        timestr = columns[1] + " " + columns[2]
        dt = datetime.datetime.strptime(timestr,"%Y/%m/%d %H:%M:%S.%f")
        timestamp = time.mktime(dt.timetuple()) + (dt.microsecond/1000000.0)
        src_addr = columns[3]
        direction = columns[4]
        dst_addr = columns[5]
        tcp_flag = columns[6]
        payload = columns[7]
        (src_ip, src_port) = src_addr.split(":")
        (dst_ip, dst_port) = dst_addr.split(":")
        if int(src_port) > 10000 and int(dst_port) < 10000 and (not args.request_regex or re.search(args.request_regex, payload)) and (args.all or re.search(r'^(POST|GET)', payload) or re.search(r'...(select|insert|update|delete|replace)', payload, re.I)):
            if tcp_flag == '[A]' and len(payload) < 30:
                continue
            # 发包，记录时间缀
            pre_packet_map[src_addr+"-"+dst_addr] = collections.OrderedDict({'start': timestamp, 'req': payload})
        elif int(src_port) < 10000 and int(dst_port) > 10000 and (args.request_regex or args.all or re.search(r'HTTP/1.[01]', payload) or re.search(r'.def.', payload, re.I)):
            # 收包，计算时间差
            addr_pair = dst_addr+"-"+src_addr
            pre_packet = pre_packet_map.get(addr_pair)
            if pre_packet is None:
                continue
            pre_timestamp = pre_packet.get('start')
            cost = timestamp - pre_timestamp
            if tcp_flag == '[A]' and len(payload) < 30:
                pre_packet['ack_rtt'] = cost_show(cost)
                continue
            pre_packet['cost'] = cost_show(cost)
            pre_packet['resp'] = payload
            pre_packet['conn'] = "%s %s %s %s %s" % (timestr, src_addr, direction, dst_addr, tcp_flag)
            if cost * 1000 > args.timeout:
                print(json.dumps(pre_packet))
                del pre_packet_map[addr_pair]

parser = argparse.ArgumentParser(description='ngrep traffic slow response trace tools.',
        usage="python -u ngrep_slow.py --timeout 1000 'port 80'|jq .")
parser.add_argument('bpf_filter', default="")
parser.add_argument('-r', '--request_regex', default=None, required=False)
parser.add_argument("-t", "--timeout", type=int, default=1000, help='the timeout millisecond.')
parser.add_argument("-a", "--all", action="store_true", help='trace all packet.')
parser.add_argument("-f", "--input_file", default=None, required=False, help='ngrep trace file.')
args = parser.parse_args()

if not exists_cmd("ngrep"):
    sys.stderr.write("ngrep not found! \n")
    sys.exit(1)

if not args.input_file:
    cmd_args = ["ngrep","-d","any","-W","single","-s","800","-t","-l",""]
    if args.bpf_filter != "":
        cmd_args.append(args.bpf_filter)
    sys.stderr.write("capture traffic with '%s'\n" % (" ".join(cmd_args)))
    proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tempfd, temppath = tempfile.mkstemp()
    try:
        with os.fdopen(tempfd, 'w') as outputStream:
            trace_ngrep_slow(args, proc.stdout, outputStream)
    finally:
        proc.stdout.close()
        sys.stderr.write(proc.stderr.read()+"\n")
        proc.stderr.close()
        proc.kill()
        sys.stderr.write("tempfile: %s\n" % temppath)
else:
    with io.open(args.input_file, "r", encoding='utf-8') as inputStream:
        trace_ngrep_slow(args, inputStream, None)


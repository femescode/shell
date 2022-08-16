#!/usr/bin/env python
# coding:utf-8

import re,datetime,time,json,sys,argparse
def trace_ngrep_slow(args):
    pre_packet_map = {}
    for line in sys.stdin:
        if not line:
            continue
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
        if int(src_port) > 10000 and int(dst_port) < 10000 and (args.all or re.search(r'^(POST|GET)', payload) or re.search(r'...(select|insert|update|delete|replace)', payload, re.I)):
            # 发包，记录时间缀
            pre_packet_map[src_addr+"-"+dst_addr] = {'start': timestamp, 'req': line}
        elif int(src_port) < 10000 and int(dst_port) > 10000 and (args.all or re.search(r'HTTP/1.[01]', payload) or re.search(r'.def.', payload, re.I)):
            # 收包，计算时间差
            addr_pair = dst_addr+"-"+src_addr
            pre_packet = pre_packet_map.get(addr_pair)
            if pre_packet is None:
                continue
            pre_timestamp = pre_packet.get('start')
            cost = int(timestamp - pre_timestamp)
            pre_packet['cost'] = str(cost) + 's'
            pre_packet['resp'] = line
            if cost * 1000 > args.timeout:
                print(json.dumps(pre_packet))
                del pre_packet_map[addr_pair]

parser = argparse.ArgumentParser(description='ngrep traffic slow response trace tools.',
        usage="ngrep -d any -W single -s 800 -t -l  '' 'port 80'|python -u ngrep_slow.py --timeout 1000 |jq .")
parser.add_argument("-t", "--timeout", type=int, default=1000, help='the timeout millisecond.')
parser.add_argument("-a", "--all", action="store_true", help='trace all packet.')
args = parser.parse_args()

trace_ngrep_slow(args)

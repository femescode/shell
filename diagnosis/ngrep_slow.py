#!/usr/bin/env python
# coding:utf-8

import collections
import io
import re,datetime,time,json,sys,argparse,subprocess,os
import tempfile

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

def cost_show(cost):
    if cost > 1:
        return "%.3fs" % (cost)
    if cost * 1000 > 1:
        return "%.3fms" % (cost * 1000)
    if cost * 1000000 > 1:
        return "%.0fus" % (cost * 1000000)
    return str(cost) + 's'

def is_request(args, payload, src_ip, src_port, dst_ip, dst_port):
    if args.in_request and dst_ip not in args.local_ip:
        return False
    if args.out_request and src_ip not in args.local_ip:
        return False
    if args.request_regex:
        if not (src_port >= args.min_local_port and dst_port < args.min_local_port):
            return False
        if re.search(args.request_regex, payload, re.I):
            return True
    else:
        if (src_port >= args.min_local_port and dst_port < args.min_local_port):
            return True
        if re.search(r'^(POST|GET) /[^ ]* HTTP/1.[01]', payload):
            return True
        if re.search(r'\.\.\.(select[\.\s].+[\.\s]from[\.\s]|insert[\.\s]+into[\.\s]|update[\.\s].+[\.\s]set[\.\s]|delete[\.\s]+from[\.\s]|replace[\.\s]+into[\.\s])', payload, re.I):
            return True
    return False

def trace_ngrep_slow(args, inputStream):
    pre_packet_map = {}
    for line in iter(inputStream.readline, b''):
        if not line:
            continue
        line=line.strip()
        if not line.startswith('T '):
            continue
        columns = line.split(" ", 7)
        if len(columns) < 8:
            continue
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
        packet_prefix = "%s %s %s %s %s" % (timestr, src_addr, direction, dst_addr, tcp_flag)
        addr_pair = dst_addr+"-"+src_addr
        if is_request(args, payload, src_ip, int(src_port), dst_ip, int(dst_port)):
            if tcp_flag == '[A]' and len(payload) < 30:
                continue
            # 发包，记录时间缀
            packet = collections.OrderedDict({})
            packet['start'] = timestamp
            packet['req'] = payload
            packet['resp'] = ''
            packet['packets'] = [packet_prefix]
            packet['cost'] = ''
            pre_packet_map[src_addr+"-"+dst_addr] = packet
        elif addr_pair in pre_packet_map:
            # 收包，计算时间差
            pre_packet = pre_packet_map.get(addr_pair)
            pre_timestamp = pre_packet.get('start')
            cost = timestamp - pre_timestamp
            if tcp_flag == '[A]' and len(payload) < 30:
                pre_packet['ack_rtt'] = cost_show(cost)
                continue
            pre_packet['cost'] = cost_show(cost)
            pre_packet['resp'] = payload
            pre_packet['packets'].append(packet_prefix)
            if cost * 1000 > args.timeout:
                print(json.dumps(pre_packet, indent=2))
            del pre_packet_map[addr_pair]

def main():
    parser = argparse.ArgumentParser(description='ngrep traffic slow response trace tools.',
            usage="python -u ngrep_slow.py 'port 80' -o -t 1000")
    parser.add_argument('bpf_filter', default="", help="bpf filter, eg: port 8080")
    parser.add_argument("-t", "--timeout", type=int, default=0, help='the timeout millisecond.')
    parser.add_argument("-i", "--in_request", action="store_true", help='trace in request packet.')
    parser.add_argument("-o", "--out_request", action="store_true", help='trace out request packet.')
    parser.add_argument('-r', '--request_regex', default=None, required=False)
    parser.add_argument("--min_local_port", type=int, default=32768, help='set tcp client min local port range')
    parser.add_argument("-I", "--input_file", default=None, required=False, help='read packet stream from pcap format file pcap_dump.')
    parser.add_argument("-O", "--output_file", default=None, required=False, help='dump matched packets in pcap format to pcap_dump')
    parser.add_argument("--local_ip", type=str, help='local ip list')
    args = parser.parse_args()

    if not exists_cmd("ngrep"):
        sys.stderr.write("ngrep not found! \n")
        sys.exit(1)
    
    if not args.local_ip:
        args.local_ip = run_cmd("ifconfig|awk -v RS= '!/lo/{print $6}'", shell=True).split()
    else:
        args.local_ip = args.local_ip.split()

    cmd_args = ["ngrep","-d","any","-W","single","-s","800","-t","-l"]
    if args.input_file:
        cmd_args.extend(["-I", args.input_file])
    if args.output_file:
        cmd_args.extend(["-O", args.output_file])
    cmd_args.append("")
    if args.bpf_filter != "":
        cmd_args.append(args.bpf_filter)
    sys.stderr.write("capture traffic with '%s'\n" % (" ".join(cmd_args)))
    proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
    try:
        trace_ngrep_slow(args, proc.stdout)
    except (KeyboardInterrupt) as e:
        pass
    finally:
        proc.stdout.close()
        sys.stderr.write(proc.stderr.read()+"\n")
        proc.stderr.close()
        proc.kill()

main()
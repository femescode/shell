#!/usr/bin/env python
# encoding: utf-8

import sys,requests,time,json,hashlib,base64,uuid,io,os,argparse,re,math
import traceback
from collections import defaultdict
from functools import cmp_to_key

s = requests.Session()
s.mount('https://', requests.adapters.HTTPAdapter(pool_connections=200, pool_maxsize=200))
s.mount('http://', requests.adapters.HTTPAdapter(pool_connections=200, pool_maxsize=200))

def http_ping(seq, args, logid):
    url = args.url
    headers = {}
    headers['User-Agent']='curl_' + str(logid)
    if args.header:
        for header in args.header:
            (key, value) = re.split(r'\s*:\s*', header.strip())
            headers[key] = value
    if args.request == "GET":
        resp = s.get(url,headers=headers, timeout=6000)
    else:
        resp = s.post(url,data=args.data,headers=headers, timeout=6000)
    ret = resp.content.decode("UTF-8").replace("\r","").replace("\n","")


parser = argparse.ArgumentParser(description='http ping test tools.')
parser.add_argument('url')
parser.add_argument('-X', "--request", type=str, choices=["GET", "POST"], default="GET", help='request method.')
parser.add_argument('-d', "--data", type=str, help='request data.')
parser.add_argument('-H', "--header", type=str, nargs='*', help='request header.')
parser.add_argument("-n", "--num", type=int, default=sys.maxsize, help='ping times.')
args = parser.parse_args()

min = max = sum = 0
cost_count_map = defaultdict(lambda: 0)
seq = 0
try:
    while seq < args.num :
        logid = uuid.uuid1().hex
        start = time.time()
        http_ping(seq, args, logid)
        end = time.time()
        cost = (end - start) * 1000
        print("time=%s seq=%d logid=%s cost=%.3fms" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start)), seq, logid, cost))
        seq = seq + 1
        if min == 0 or cost < min:
            min = cost 
        if max == 0 or cost > max:
            max = cost
        sum = sum + cost
        f = math.log(int(cost),2)
        ff = math.floor(f)
        cf = math.ceil(f)
        if ff == cf:
            cf = cf + 1
        cost_range = "%d-%dms" % (int(math.pow(2, ff)), int(math.pow(2, cf)))
        cost_count_map[cost_range] = cost_count_map[cost_range] + 1

        time.sleep(1)
except (KeyboardInterrupt) as e:
    pass
except (requests.exceptions.RequestException) as e:
    print(traceback.format_exc())

if seq > 0:
    print("\n rtt min/avg/max = %.3f/%.3f/%.3f ms" % (min, sum/seq, max))

print("\n %8s\t%s" % ("cost", "num"))
cost_arr = list(cost_count_map.keys())
def cmp_cost_key(x, y):
    return int(x.split("-")[0]) - int(y.split("-")[0])
cost_arr.sort(key=cmp_to_key(cmp_cost_key))
for k in cost_arr:
    print(" %8s\t%s" % (str(k), str(cost_count_map.get(k))))
#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import datetime,time
import decimal
import re
import binascii,uuid

class CostStatics:
    def __init__(self):
        self.min=None
        self.max=None
        self.count=0
        self.sum=0
        self.avg=None
    def append(self, cost):
        self.count = self.count + 1
        self.sum = self.sum + cost
        self.avg = (self.sum + 0.0) / self.count
        if self.min:
            self.min = min(self.min, cost)
        else:
            self.min = cost
        if self.max:
            self.max = max(self.max, cost)
        else:
            self.max = cost

def execSql(con, sql):
    cur = con.cursor(cursor=pymysql.cursors.DictCursor)
    cur.execute(sql)
    rows = cur.fetchall()
    return len(rows)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='command util.')
    parser.add_argument('sql')
    parser.add_argument('-H', "--host", required=True, help='host.')
    parser.add_argument('-P', "--port", required=True, type=int, help='port.')
    parser.add_argument('-u', "--user", required=True, help='user.')
    parser.add_argument('-p', "--password", required=True, help='password.')
    parser.add_argument('-D', "--database", required=True, help='database.')
    args = parser.parse_args()
    con = pymysql.connect(
                host=args.host,port=args.port,
                user=args.user,
                password=args.password,
                database=args.database,charset='utf8')
    costStatics = CostStatics()
    try:
        while True:
            uid = uuid.uuid1().hex
            sql = "%s /* trace_id: %s */" % (args.sql, uid)
            
            start_time = time.time()
            cnt = execSql(con, sql)
            end_time = time.time()
            cost = (end_time - start_time) * 1000
            
            costStatics.append(cost)
            print("%2d cost:%.2fms avg:%.2fms trace_id:%s " % (costStatics.count, cost, costStatics.avg, uid), flush=True)
            time.sleep(1)
    except (KeyboardInterrupt) as e:
        print("count:%d min:%.2fms max:%.2fms avg:%.2fms" % (costStatics.count, costStatics.min, costStatics.max, costStatics.avg))
        pass


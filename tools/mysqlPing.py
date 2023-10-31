#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import datetime,time
import decimal
import re
import binascii,uuid
import getpass

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

def execSql(con, rollback, sql):
    cur = con.cursor(cursor=pymysql.cursors.DictCursor)
    if not rollback and re.search(r'^\s*select', sql, re.I):
        cur.execute(sql)
        rows = cur.fetchall()
        return len(rows)
    else:
        con.begin()
        try:
            cur.execute(sql)
            return cur.rowcount
        finally:
            con.rollback()

def get_multi_input(promot):
    print(promot,end="")
    lines = []
    empty_num=0
    while True:
        line = input()
        if line:
            lines.append(line)
            empty_num=0
            if re.search(";\s*$", line):
                break
        else:
            empty_num=empty_num+1
        if empty_num >=3: 
            break
    return "\n".join(lines)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='command util.')
    parser.add_argument('sql', nargs='?')
    parser.add_argument('-H', "--host", required=True, help='host.')
    parser.add_argument('-P', "--port", required=True, type=int, help='port.')
    parser.add_argument('-u', "--user", required=True, help='user.')
    parser.add_argument('-p', "--password", required=False, help='password.')
    parser.add_argument('-D', "--database", required=True, help='database.')
    parser.add_argument('-r', "--rollback", action="store_true", help='rollback.')
    args = parser.parse_args()
    password = args.password
    if not args.password:
        password = getpass.getpass(prompt='Enter password: ')
        print("*" * len(password))
    input_sql = args.sql
    if not input_sql:
        input_sql=get_multi_input("Enter sql:>> \n")
        print("<< Execute sql begin...")
    con = pymysql.connect(
                host=args.host,port=args.port,
                user=args.user,
                password=password,
                database=args.database,charset='utf8')
    if not args.rollback and re.search(r'^\s*select', input_sql, re.I):
        con.autocommit(True)
    else:
        con.autocommit(False)
    costStatics = CostStatics()
    try:
        while True:
            uid = uuid.uuid1().hex
            sql = "%s /* trace_id: %s */" % (input_sql, uid)
            
            start_time = time.time()
            cnt = execSql(con, args.rollback, sql)
            end_time = time.time()
            cost = (end_time - start_time) * 1000
            
            costStatics.append(cost)
            print("%2d cost:%.2fms avg:%.2fms trace_id:%s " % (costStatics.count, cost, costStatics.avg, uid), flush=True)
            time.sleep(1)
    except (KeyboardInterrupt) as e:
        print("count:%d min:%.2fms max:%.2fms avg:%.2fms" % (costStatics.count, costStatics.min, costStatics.max, costStatics.avg))
        pass


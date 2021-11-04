#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import datetime
import decimal

def strval(v):
    return str(v).replace("'","\\'").replace("\n","\\n").replace("\t","\\t")

def dumpSqlFromRow(row, tableName):
    fields = []
    values = []
    for k in row.keys():
        v = row.get(k)
        if v is None:
            continue
        elif isinstance(v, str):
            values.append("'" + strval(v) + "'")
        elif isinstance(v, int) or isinstance(v, decimal.Decimal):
            values.append(strval(v))
        elif isinstance(v, datetime.datetime):
            values.append("'" + strval(v) + "'")
        elif isinstance(v, bytes):
            values.append("unhex('" + strval(v.hex()) + "')")
        else:
            values.append("'" + strval(v) + "'")
        fields.append("`" +k + "`")
    print("insert into %s(%s) values(%s);" % (tableName, ','.join(fields), ','.join(values)))

def getSqlRows(con, tableName, whereSql):
    cur = con.cursor(cursor=pymysql.cursors.DictCursor)
    cur.execute('select * from %s %s' % (tableName, whereSql))
    rows = cur.fetchall()
    return rows

def dumpSqlFromRows(rows, tableName):
    for row in rows:
        dumpSqlFromRow(row, tableName)

def dumpSql(con, tableName, whereSql):
    results = getSqlRows(con, tableName, whereSql)
    dumpSqlFromRows(results, tableName)

def exportSqlByWaybillId(con, oid, tid, wid):
    dumpSql(con, "deliver_item", " where wid=%s" % (wid))

def exportSqlByOrderId(con, oid, tid):
    dumpSql(con, "order_item", " where oid=%s" % (oid))

    rows = getSqlRows(con, "deliver", " where oid=%s" % (oid))
    for row in rows:
        dumpSqlFromRow(row, "deliver")
        exportSqlByWaybillId(con, oid, tid, str(row.get("wid")))

def exportSql(con, oid):
    rows = getSqlRows(con, "order", " where oid=%s limit 1" % (oid))
    for row in rows:
        dumpSqlFromRow(row, "order")
        exportSqlByOrderId(con, str(row.get("oid")), str(row.get("tid")))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='command util.')
    parser.add_argument('oids', nargs='+')
    args = parser.parse_args()
    con = pymysql.connect(host='localhost',port=3306,user='root',password='pass',database='shop',charset='utf8')
    for oid in args.oids:
        exportSql(con, oid)

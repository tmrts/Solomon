#!/usr/bin/python
# -*- coding: utf-8 -*-

import psycopg2
import sys

con = None

try:

    con = psycopg2.connect(host="localhost", dbname="solomon_db", user="solomon_user", password="solomon")

    cur = con.cursor()

    cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    cur.execute('DROP TABLE IF EXISTS log_visit')

    cur.execute(r'''CREATE TABLE log_visit(visitor_number SERIAL NOT NULL,
                                           visitor_id UUID NOT NULL PRIMARY KEY,
                                           visitor_country TEXT NOT NULL,
                                           visitor_city TEXT NOT NULL,
                                           visitor_first_action_time TIMESTAMP WITH TIME ZONE NOT NULL,
                                           visitor_last_action_time TIMESTAMP WITH TIME ZONE NOT NULL,
                                           visitor_returning BOOLEAN NOT NULL,
                                           visit_count SMALLINT NOT NULL,
                                           referer_url TEXT,
                                           referer_keyword TEXT,
                                           config_os CHAR(10) NOT NULL,
                                           config_browser_name CHAR(15) NOT NULL,
                                           config_browser_version CHAR(20) NOT NULL,
                                           config_resolution CHAR(9) NOT NULL,
                                           location_ip CIDR
                                           )''')

    cur.execute('DROP TABLE IF EXISTS log_metrics')

    cur.execute(r'''CREATE TABLE log_metrics(daily_date DATE NOT NULL PRIMARY KEY DEFAULT CURRENT_DATE,
                                             daily_bit_array BIT VARYING NOT NULL DEFAULT '0'
                                             )''')

    cur.execute('DROP TABLE IF EXISTS log_websocket')

    cur.execute(r'''CREATE TABLE log_websocket(websocket_use_id SERIAL NOT NULL PRIMARY KEY,
                                               visitor_id UUID NOT NULL REFERENCES log_visit(visitor_id)
                                               )''')



    con.commit()

finally:
    if con:
        con.close()



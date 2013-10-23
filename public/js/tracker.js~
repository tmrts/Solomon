# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
# Copyright (C) 2013  Tamer TAS
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
################################################################################

""" 
Observer is an asynchronous visitor tracking system built for high-traffic websites.
Nginx is used as the reverse-proxy and PostgreSQL is the database of choice.
The app was built using Tornado 3.1 and Python 3.2. Observer tracks users
by responding to a get request made by client for a 1x1 pixel and it initiates
a websocket connection to track number of online users
"""


__version__ = 1.0

import tornado.httpserver
import tornado.httputil
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.options

import os.path
import psycopg2
import momoko

import uuid
import httpagentparser
import functools
import struct

from tornado import web, gen
from sockjs.tornado import SockJSConnection, SockJSRouter

from time import localtime, strftime
from referer_parser import Referer

from tornado.options import define, options

define("port", default=8000, help="run on the given port", type=int)

define("debug", default=True, help="debug mode on/off", type=bool)

cookie_secret = "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=" #Use your own secret

# 1x1 Transparent Pixel in HEX Format
pixel_GIF = [0x47,0x49,0x46,0x38,0x39,0x61,
             0x01,0x00,0x01,0x00,0x80,0x00,
             0x00,0x00,0x00,0x00,0xff,0xff,
             0xff,0x21,0xf9,0x04,0x01,0x00,
             0x00,0x00,0x00,0x2c,0x00,0x00,
             0x00,0x00,0x01,0x00,0x01,0x00, 
             0x00,0x02,0x01,0x44,0x00,0x3b]


db = dict()
db["database"] = os.environ.get('MOMOKO_TEST_DB', 'observer_db')
db["user"] = os.environ.get('MOMOKO_TEST_USER', 'observer_user')
db["password"] = os.environ.get('MOMOKO_TEST_PASSWORD', 'observer')
db["host"] = os.environ.get('MOMOKO_TEST_HOST', 'localhost')
db["port"] = os.environ.get('MOMOKO_TEST_PORT', 5432)

enable_hstore = True if os.environ.get('MOMOKO_TEST_HSTORE', False) == '1' else False

dsn = '''dbname={database}
         user={user}
         password={password}
         host={host}
         port={port}'''.format(**db)

assert (db["database"] or db["user"] or db["password"] or db["host"] or db["port"]) is not None, (
    'Environment variables for the examples are not set. Please set the following '
    'variables: MOMOKO_TEST_DB, MOMOKO_TEST_USER, MOMOKO_TEST_PASSWORD, '
    'MOMOKO_TEST_HOST, MOMOKO_TEST_PORT'
    )


class BaseHandler(tornado.web.RequestHandler):

    def to_unicode(self, string):
        return tornado.escape.to_unicode(string)

    @property
    def db(self):
        if not hasattr(self.application, 'db'):
            self.application.db = momoko.Client(dsn)
        return self.application.db

    def get_current_user(self, cookie=None):
        user_json = self.get_secure_cookie(cookie)
        if user_json:
            user = self.to_unicode(user_json)
        else:
            user = None
        return user

    def sql_repr(self, item, keys=None):
        if item is not None:
            representation = repr(item)

        else:
            representation = repr("None")

        return representation

    def pack_into_binary(self, data):
        packed = str()
        for datum in data:
            packed += struct.pack('B', datum).decode("ISO-8859-1")
        return packed


class PixelHandler(BaseHandler):

    def initialize(self):
        self.pixel_binary = self.pack_into_binary(pixel_GIF)
        self.user = dict()
        
    @web.asynchronous
    @gen.coroutine
    def get(self):
        self.user["id"] = self.get_current_user("Observer.ID")

        self.user["session"] = self.get_secure_cookie("Observer.Session")

        self.user["time"] = self.sql_repr(strftime("%a, %d %b %Y %X", localtime()))

        if self.user["id"] is None:
            self.user["id"] = self.sql_repr(uuid.uuid4())
                
            headers = self.request.headers
            user_agent = httpagentparser.detect(headers.get("user-agent"))

            country = self.get_argument("ctry", default=None, strip=True)
            city = self.get_argument("cty", default=None, strip=True)
            referer = Referer(self.get_argument("ref", default=None, strip=True))

            #Use it for tracking visits to subdomains implement it later
            link = self.get_argument("hr", default=None, strip=True)
            #Use it for tracking visits to subdomains implement it later
            subdomain = self.get_argument("pn", default=None, strip=True)


            window_width = self.get_argument("ow", default=None, strip=True)
            window_height = self.get_argument("oh", default=None, strip=True)
            
            if window_height and window_width:
                resolution = window_width + "x" + window_height
            else:
                resolution = None

            self.user["country"] = self.sql_repr(country)
            self.user["city"] = self.sql_repr(city)

            self.user["returning_visitor"] = False
            self.user["visit_count"] = 1 #Change to default

            self.user["remote_ip"] = self.sql_repr(self.request.remote_ip)
            #Arguments after this
            self.user["referer_url"] = self.sql_repr(referer.referer)
            self.user["referer_keyword"] = self.sql_repr(referer.search_term)
            self.user["resolution"] = self.sql_repr(resolution)

            #Get arguments check from maxmind database if no geolocation
            #Implement User data updates(Users change OS, Browser etc.)

            #Existence check
            self.user["dist_name"] = self.sql_repr(user_agent["dist"]["name"])
            self.user["browser_name"] = self.sql_repr(user_agent["browser"]["name"])
            self.user["browser_version"] = self.sql_repr(user_agent["browser"]["version"])
            
            yield momoko.Op(self.db.execute,
                """INSERT INTO log_visit VALUES(DEFAULT,
                                                {id},
                                                {country},
                                                {city},
                                                CURRENT_TIMESTAMP,
                                                CURRENT_TIMESTAMP,
                                                {returning_visitor},
                                                {visit_count},
                                                {referer_url},
                                                {referer_keyword},
                                                {dist_name},
                                                {browser_name},
                                                {browser_version},
                                                {resolution},
                                                {remote_ip}
                                                )""".format(**self.user))

            self.set_secure_cookie("Observer.ID",
                                   self.user["id"],
                                   expires_days=(365 * 2))

        elif self.user["session"] is None:
            self.user["returning_visitor"] = True
                
            yield momoko.Op(self.db.execute, 
                """UPDATE log_visit SET visit_count = visit_count + 1,
                                        visitor_returning = {returning_visitor}
                                    WHERE visitor_id = {id}
                """.format(**self.user))
        #Poor Exception Handling
        #If it's a new user session, update the daily bit array
        #if self.user["session"] is None:
        #{    yield gen.Task(self.update_bit_array, self.user["id"])


        yield momoko.Op(self.db.execute,
                """UPDATE log_visit SET visitor_last_action_time = CURRENT_TIMESTAMP
                    WHERE visitor_id = {id}
                """.format(**self.user))

        self.set_secure_cookie("Observer.Session", "None", expires_days=(1 / 24))


        #1x1 Transparent Tracking Pixel
        self.set_header("Content-Length", 42)
        self.set_header("Content-Type", "image/gif")
        self.set_header("Pragma", "no-cache")
        self.set_header("Cache-Control", 
                        "no-store, "
                        "no-cache=Set-Cookie, "
                        "proxy-revalidate, "
                        "max-age=0, "
                        "post-check=0, pre-check=0"
                        )
        self.set_header("Expires", "Wed, 2 Dec 1837 21:00:12 GMT")
        self.write(self.pixel_binary)

        self.finish()

        raise gen.Return()

    @gen.coroutine
    def update_bit_array(self, identification):
        #Update the bit array for new and returning users
        cursor_number, cursor_bit_array = yield [
            momoko.Op(self.db.execute,
                """SELECT visitor_number FROM log_visit
                    WHERE visitor_id = {0}
                """.format(identification)),
            momoko.Op(self.db.execute,
		"""INSERT INTO log_metrics ("daily_date", "daily_bit_array") SELECT CURRENT_DATE, '0'
		   WHERE NOT EXISTS (SELECT daily_bit_array FROM log_metrics WHERE daily_date = CURRENT_DATE)
		   RETURNING daily_bit_array
                """)
            ]

        #Updating the bit array after user action
        visitor_number = int(cursor_number.fetchall()[0][0])
        bit_array_number = int(cursor_bit_array.fetchall()[0][0], 2)

        bit_array_string = "{0:b}".format(bit_array_number | (2 ** visitor_number))
        bit_array_updated = self.sql_repr(bit_array_string)
        #UPSERT
        yield momoko.Op(self.db.execute,
            """UPDATE log_metrics SET daily_bit_array = {0}
                WHERE daily_date = CURRENT_DATE
            """.format(bit_array_updated))

        raise gen.Return()

class WebSocketBaseHandler(SockJSConnection):

    def decode_signed_value(self, cookie_secret, cookie_name, cookie_value):
        return tornado.web.decode_signed_value(cookie_secret, cookie_name, cookie_value)

    def to_unicode(self, string):
        return tornado.escape.to_unicode(string)

    @property
    def db(self):
        return application.db

    def get_current_user(self, info, cookie_name):

        user_id = self.to_unicode(self.decode_signed_value(cookie_secret,
                                                         cookie_name,
                                                         info.get_cookie(cookie_name).value
                                                         ))

        return user_id


class WebSocketHandler(WebSocketBaseHandler):
    def initialize(self):
        self.user = dict()

    @gen.coroutine
    def on_open(self, info):
        self.user["id"] = self.get_current_user(info, "Observer.ID")

        try:
            yield [momoko.Op(self.db.execute,
                    """INSERT INTO log_websocket 
                        VALUES(DEFAULT, {id})
                    """.format(**self.user)),
                   momoko.Op(self.db.execute,# Update required.
                    """UPDATE log_metrics SET online_user_count = online_user_count + 1
                       WHERE daily_date = CURRENT_DATE
                    """.format(**self.user))
                   ]
        
        except Exception as error:
            self.write_message(str(error))
            self.close()


    def on_message(self, message):
        pass
    
    @gen.coroutine
    def on_close(self):
        try:
            yield [momoko.Op(self.db.execute,
                    """DELETE FROM log_websocket
                       WHERE websocket_user_id = {id}
                    """.format(**self.user)),
                   momoko.Op(self.db.execute, #Update required.
                    """UPDATE log_metrics SET online_user_count = online_user_count - 1
                       WHERE daily_date = CURRENT_DATE
                    """.format(**self.user))
                    ]

        except Exception as error:
            self.write_message(str(error))


if __name__ == '__main__':
    try:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

        tornado.options.parse_command_line()
        
        settings = {"debug": options.debug,
                    "cookie_secret": cookie_secret,
                    "xsrf_cookies": True,
                    "gzip": True
                    }

        WebSocketRouter = SockJSRouter(WebSocketHandler, '/ws')

        application = tornado.web.Application([(r'/', PixelHandler)]
                                                + WebSocketRouter.urls,                        
                                                **settings
                                                )

        application.db = momoko.Pool(dsn=dsn,
                                     size=10
                                     )

        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()

    except KeyboardInterrupt:
        print('\nExit')


#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse


def help():
    print("httpclient.py [GET/POST] [URL]\n")


class HTTPRequest(object):

    HTTP_VERSION = "HTTP/1.1"
    ENABLED_COMMANDS = ["GET", "POST"]

    def __init__(self):

        self.req_line = None
        self.req_headers = []
        self.req_body = None
        self.req = None

    def add_body(self, body):
        self.req_body = body

    def add_req_headers(self, key, value):
        self.req_headers.append("%s: %s\r\n" % (key, value))

    def gen_req_line(self, command, path):
        command = command.upper()
        # if command not in self.ENABLED_COMMANDS:
        #     return False
        self.req_line = "%s %s %s\r\n" % (command, path, self.HTTP_VERSION)

    def commit(self):
        req = ""

        # if not (self.req_line):
        #     return False
        req += self.req_line

        if self.req_headers:
            for header in self.req_headers:
                req += header

        # if "Host:" not in req:
        #     print("AH")
        #     return False

        req += '\r\n'

        if self.req_body:
            # if "Content-length: " not in req:
            #     return False
            req += self.req_body
        self.req = req
        return req

    def get_req(self):
        return self.req

    def reset(self):

        self.req_line = None
        self.req_headers = []
        self.req_body = None
        self.req = None


class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

    def __str__(self):
        return "%s %s" % (self.code, self.body)


class HTTPClient(object):

    def parse_url(self, url):
        parsed_url = urllib.parse.urlparse(url)
        hostname = parsed_url.hostname
        path = '/' if not parsed_url.path else parsed_url.path
        port = parsed_url.port
        if not port:
            port = 443 if parsed_url.scheme == "https" else 80

        return hostname, port, path

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        data = data.split('\r\n')
        res_line = data[0].split(" ")
        code = res_line[1]
        return int(code)

    def get_headers(self, data):
        data = data.split("\r\n")
        index = data.index("")
        return "\r\n".join(data[1:index])

    def get_body(self, data):
        data = data.split("\r\n")
        index = data.index("")
        return "\r\n".join(data[index + 1:])

    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        try:
            buffer = buffer.decode("utf-8")
        except UnicodeDecodeError:
            buffer = buffer.decode("iso-8859-1").encode("utf-8").decode()
        return buffer

    def GET(self, url, args=None):
        res_code = 500
        res_body = ""

        hostname, port, path = self.parse_url(url)

        req = HTTPRequest()
        req.gen_req_line("GET", path)
        req.add_req_headers("Host", hostname)
        req.add_req_headers("Connection", "close")
        req = req.commit()

        if not req:
            print("Unable to generate a request.")
            sys.exit()

        self.connect(hostname, port)
        self.sendall(req)

        res = self.recvall(self.socket)
        res_code = self.get_code(res)
        res_body = self.get_body(res)
        self.close()
        return HTTPResponse(res_code, res_body)

    def POST(self, url, args=None):
        res_code = 500
        res_body = ""
        hostname, port, path = self.parse_url(url)

        req = HTTPRequest()
        req.gen_req_line("POST", path)
        req.add_req_headers("Host", hostname)
        req.add_req_headers("Content-Type", "application/x-www-form-urlencoded")
        req.add_req_headers("Connection", "close")

        if not args:
            content_len = 0
        else:
            urlencoded_args = urllib.parse.urlencode(args)
            content_len = len(urlencoded_args.encode("utf-8"))
            req.add_body(urlencoded_args)

        req.add_req_headers("Content-length", content_len)
        req = req.commit()

        if not req:
            print("Unable to generate a request.")
            sys.exit()

        self.connect(hostname, port)
        self.sendall(req)
        res = self.recvall(self.socket)
        res_code = self.get_code(res)
        res_body = self.get_body(res)
        self.close()
        return HTTPResponse(res_code, res_body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST(url, args)
        else:
            return self.GET(url, args)


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command(sys.argv[2], sys.argv[1]))
    else:
        print(client.command(sys.argv[1]))

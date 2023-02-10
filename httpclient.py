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
import base64

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    #def get_host_port(self,url):

    def connect(self, host, port):
        print(f"Conecting to...\nhost: {host}\nport: {port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        print(f"Connected!\n")
        return None

    def get_code(self, data):
        return None

    def get_headers(self,data):
        return data.split("\r\n\r\n")[0]

    def get_body(self, data):
        return data.split("\r\n\r\n")[1]

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
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        address, port, short_url, path = get_info(url)

        payload = f'GET {path} HTTP/1.1\r\nHost: {get_domain(short_url)}\r\nUser-Agent: python/3\r\nAccept: */*\r\nConnection: close\r\n\r\n'
        self.connect(address, port)

        print("Request:\n", payload)
        self.sendall(payload)

        response = self.recvall(self.socket)
        self.close()
        print("Response:\n", response)

        header_lines = response.replace('\r', '').split('\n')
        status_code = header_lines[0].split(' ')[1]
        body = response.split("\r\n\r\n")[1]

        return HTTPResponse(int(status_code), body)

    def POST(self, url, args=None):
        address, port, short_url, path = get_info(url)

        req_body = ''
        counter = 1
        if args:
            for id, data in args.items():
                key = id
                value = data
                if is_binary(key): key = base64.b64encode(key.encode('ascii'))
                if is_binary(value): value = base64.b64encode(value.encode('ascii'))

                req_body += f"{key}={value}"
                if counter != len(args):
                    req_body += '&'
                counter += 1

        encoding_dict = {
            "%20": " ", "%21": "!", "%22": '"',
            "%23": "#", "%24": "$", "%25": "%",
            "%26": "&", "%27": "'", "%28": "(",
            "%29": ")", "%2B": " "
        }
        for key,val in encoding_dict.items():
            req_body = req_body.replace(key, val)

        payload = f"POST {path} HTTP/1.1\r\nHost: {get_domain(short_url)}\r\nAccept: */*\r\nContent-Length: {len(req_body.encode('utf-8'))}\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: close\r\n\r\n"
        if len(req_body) > 0:
            payload += f"{req_body}\r\n\r\n"

        self.connect(address, port)

        print("Request:\n", payload)
        self.sendall(payload)

        response = self.recvall(self.socket)
        self.close()
        print("Response:\n", response)
        print("\n")

        header_lines = response.replace('\r', '').split('\n')
        status_code = header_lines[0].split(' ')[1]
        body = response.split("\r\n\r\n")[1]

        return HTTPResponse(int(status_code), body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )



def get_domain(url):
    return url.split("/")[0]

def get_info(url):
    """
        params:
        - url: the entire address url
        returns: the meta data of the url like address, port, short_url, and path (specifics after root)
    """
    protocol, short_url = get_url_proto(url)
    host, port, is_IP = get_host_port(short_url, protocol)
    address = host
    if not is_IP:
        address = get_ip(host)
    path = get_specific_path(short_url)
    return address, port, short_url, path

def get_specific_path(url):
    """
        params:
        - url: the address string
        returns: the path in the url prefixed with "/"
    """
    (host, slash, path) = url.partition("/")
    return "/" + path


def get_url_proto(full_url):
    if full_url.startswith("https:"):
        return "https", full_url.partition("https://")[-1]
    elif full_url.startswith("http:"):
        return "http", full_url.partition("http://")[-1]
    else:
        # default http
        return "http", full_url


def get_ip(host):
    print(f'Getting IP for {host}')
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        print('Hostname could not be resolved in `get_remote_ip(host)`. Exiting.')
        sys.exit()
    else:
        print(f'{host} IP is {ip}')
        return ip


def is_binary(data):
    data = set(data)
    return data == {'0', '1'} or data == {'1'} or data == {'0'}


def get_host_port(url, protocol):
    """
        params:
        - url: the address string w/o the protocol
        - protocol: "http" or "https"
        returns: (host, port, is_IP) Note: if port is undefined, default 80 (if http) or 443 (if https)
    """
    full = url.split("/")[0]
    temp = full.split(":")
    if len(temp) == 1:
        if protocol == 'http':
            return temp[0], 80, False
        elif protocol == 'https':
            return temp[0], 443, False
    elif len(temp) == 2:
        return temp[0], int(temp[1]), True
    else:
        return "ERROR_host", "ERROR_port", None

if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))

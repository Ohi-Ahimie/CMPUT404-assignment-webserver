#  coding: utf-8 
import socketserver
import re
import urllib.parse
from enum import Enum, auto
import os
import mimetypes
from datetime import datetime
import time

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
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
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

# switcher code based on: https://jaxenter.com/implement-switch-case-statement-python-138315.html

class MyWebServer(socketserver.BaseRequestHandler):
    requestLine = []
    dataLines = []
    
    class ServerState(Enum):
        READ_DATA = auto()
        INVALID_REQUEST = auto()
        READ_METHOD = auto()
        INVALID_METHOD = auto()
        CHECK_URI = auto()
        FIX_URI = auto()
        INVALID_URI = auto()
        SERVE_DATA = auto()
        TERMINATE = auto()

    def getDate(self):
        d = datetime.now()
        return d.strftime('%a, %d %b %Y %H:%M:%S ') + time.tzname[0]


    def checkData(self):
        try:
            # print(self.data)
            self.dataLines = re.split('\n|\r\n', self.data.decode('utf-8'))
        except Exception as e:
            print('An error occured: ' + e)
            return self.ServerState.INVALID_REQUEST

        requestLine = self.dataLines[0].split()
        if len(requestLine) != 3:
            requestLine = []
            return self.ServerState.INVALID_REQUEST
        else:
            self.requestLine = requestLine
            return self.ServerState.READ_METHOD

    def checkMethod(self):
        if self.requestLine[0] == 'GET':
            return self.ServerState.CHECK_URI
        elif self.requestLine[0] == 'OPTIONS' or self.requestLine[0] == 'HEAD' or self.requestLine[0] == 'POST' or self.requestLine[0] == 'PUT' or self.requestLine[0] == 'DELETE' or self.requestLine[0] == 'TRACE' or self.requestLine[0] == 'CONNECT':
            return self.ServerState.INVALID_METHOD
        else:
            return self.ServerState.INVALID_REQUEST

    def checkUri(self):
        path = self.requestLine[1]
        if '..' in path:
            return self.ServerState.INVALID_URI
        
        pathLocated = os.path.isdir('./www' + path) 
        if (pathLocated and path.endswith('/')) or (os.path.isfile('./www' + path)):
            return self.ServerState.SERVE_DATA
        elif pathLocated:
            return self.ServerState.FIX_URI

        return self.ServerState.INVALID_URI
    
    def handle301(self):
        path = self.requestLine[1]
        self.request.sendall(bytearray("HTTP/1.1 301 Moved Permanently\r\nDate: " + self.getDate() + "\r\nLocation: http://127.0.0.1:8080" + path + '/\r\n' + "Connection: close\r\n\r\n",'utf-8'))
        return self.ServerState.TERMINATE

    def handle400(self):
        self.request.sendall(bytearray("HTTP/1.1 400 Bad Request\r\nDate: " + self.getDate() + "\r\nConnection: close\r\n\r\n",'utf-8'))
        return self.ServerState.TERMINATE

    def handle404(self):
        self.request.sendall(bytearray("HTTP/1.1 404 Page Not Found\r\nDate: " + self.getDate() + "\r\nConnection: close\r\n\r\n",'utf-8'))
        return self.ServerState.TERMINATE

    def handle405(self):
        self.request.sendall(bytearray("HTTP/1.1 405 Method Not Allowed\r\nDate: " + self.getDate() + "\r\nAllow: GET\r\nConnection: close\r\n\r\n",'utf-8'))
        return self.ServerState.TERMINATE

    def serve(self):
        path = self.requestLine[1]
        if os.path.isdir('./www' + path):
            f = open('./www' + path + 'index.html')            
            self.request.sendall(bytearray("HTTP/1.1 200 OK\r\nDate: " + self.getDate() + "\r\nContent-Type: text/html;\r\nConnection: close\r\n\r\n" + f.read(),'utf-8'))
            f.close()
        else:
            f = open('./www' + path)
            mime = mimetypes.guess_type('./www' + path)[0]
            if not mime:
                mime = 'application/octet-stream'
            self.request.sendall(bytearray("HTTP/1.1 200 OK\r\nDate: " + self.getDate() + "\r\nContent-Type: " + mime + ";\r\nConnection: close\r\n\r\n" + f.read(),'utf-8'))
            f.close()
        return self.ServerState.TERMINATE

    def handle(self):
        self.data = self.request.recv(1024).strip()
        
        switcher = {
            self.ServerState.READ_DATA : self.checkData,
            self.ServerState.INVALID_REQUEST : self.handle400,
            self.ServerState.READ_METHOD : self.checkMethod,
            self.ServerState.INVALID_METHOD : self.handle405,
            self.ServerState.CHECK_URI : self.checkUri,
            self.ServerState.FIX_URI : self.handle301,
            self.ServerState.INVALID_URI : self.handle404,
            self.ServerState.SERVE_DATA : self.serve           
        }

        state = self.ServerState.READ_DATA
        while state is not self.ServerState.TERMINATE:
            func = switcher.get(state)
            state = func()
            # print(state)

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()

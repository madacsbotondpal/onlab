#!/usr/bin/env python2.7

import socket
import SocketServer
import json

NAME = "MONITOR"
PORT = 5432

ROBOT_ADDR = ("192.168.0.113", 502)

# requests for registers
req_X =  "\x00\x04\x00\x00\x00\x06\x00\x03\x01\x90\x00\x01"  # 400
req_Y =  "\x00\x04\x00\x00\x00\x06\x00\x03\x01\x91\x00\x01"  # 401
req_Z =  "\x00\x04\x00\x00\x00\x06\x00\x03\x01\x92\x00\x01"  # 402

TOLERANCE = 0.001  # meters, 1 millimeter

def match_pos(actual, target):
    for i in range(3):
        if abs(actual[i] - target[i]) > TOLERANCE:
            return False
    return True

class TCPHandler(SocketServer.BaseRequestHandler):
    def request_coordinate(self, request):
        self.robot.send(request)
        resp = self.robot.recv(1024)
        resp = resp.replace("\x00\x04\x00\x00\x00\x05\x00\x03\x02", "")  # remove the clutter
        resp_hex = resp.encode("hex")
        if resp_hex == "":
            resp_hex = "0000"
        resp_int = int(resp_hex,16)
        if resp_int < 32768:
            return float(resp_int)/10000
        else:
            resp_int = 65535 - resp_int
            return float(resp_int)/10*-1/1000

    def retrieve_pos(self):
        position = [
            self.request_coordinate(req_X),
            self.request_coordinate(req_Y),
            self.request_coordinate(req_Z)
        ]
        return position

    def handle(self):
        self.robot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.robot.connect(ROBOT_ADDR)

        while True:
            self.data = self.request.recv(1024).strip()
            print('{} - From {} received {}'.format(NAME, self.client_address[0], self.data))
            requested_pos = json.loads(self.data.decode())
            actual_pos = [0, 0, 0]

            actual_pos = self.retrieve_pos()
            print('{} - Current position: {}'.format(NAME, actual_pos))
            
            while not match_pos(requested_pos, actual_pos):
                actual_pos = self.retrieve_pos()

            message = 'target reached'
            print('{} - Sending to {}: {}'.format(NAME, self.client_address[0], message))
            self.request.send(message.encode())

if __name__ == "__main__":
    server = SocketServer.TCPServer(('0.0.0.0', PORT), TCPHandler)
    server.serve_forever()

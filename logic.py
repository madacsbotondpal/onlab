#!/usr/bin/env python3

import socketserver
import itertools
import json

NAME = 'LOGIC '
PORT = 4321

TCP_LOCATIONS = [
    {'from': [0.35, -0.3, 0.042], 'to': [0.20, -0.3, 0.042]},
    {'from': [0.35, -0.2, 0.042], 'to': [0.20, -0.2, 0.042]},
    {'from': [0.35, -0.1, 0.042], 'to': [0.20, -0.1, 0.042]},
    {'from': [0.20, -0.3, 0.042], 'to': [0.35, -0.3, 0.042]},
    {'from': [0.20, -0.2, 0.042], 'to': [0.35, -0.2, 0.042]},
    {'from': [0.20, -0.1, 0.042], 'to': [0.35, -0.1, 0.042]}
]
TCP_ORIENTATION = [2.25, -2.25, 0]

GRIPPER_CLOSED = 57  # millimeters
GRIPPER_OPEN = 77  # millimeters

LIFT_HEIGHT = 0.08  # meters to lift the item before moving it horizontally
PAYLOAD = 0.15  # kilograms

class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        for tcp_location in itertools.cycle(TCP_LOCATIONS):
            self.data = self.request.recv(1024).strip()
            print('{} - From {} received {}'.format(NAME, self.client_address[0], self.data))

            control_data = {
                'from': {
                    'pose' : tcp_location['from'] + TCP_ORIENTATION,
                    'lift_height': LIFT_HEIGHT
                },
                'to': {
                    'pose': tcp_location['to'] + TCP_ORIENTATION,
                    'lift_height': LIFT_HEIGHT
                },
                'gripper': {
                    'close': GRIPPER_CLOSED,
                    'open': GRIPPER_OPEN,
                    'payload': PAYLOAD,
                }
            }
            message = json.dumps(control_data)

            print('{} - Sending to {}: {}'.format(NAME, self.client_address[0], message))
            self.request.send(message.encode())

if __name__ == "__main__":
    server = socketserver.TCPServer(('0.0.0.0', PORT), TCPHandler)
    server.serve_forever()

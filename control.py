#!/usr/bin/env python3

import socket
import requests
import json
import itertools
import time

NAME = 'CONTROL'

LOGIC_ADDR = ('logic', 4321)
MONITOR_ADDR = ('monitor', 5432)
GRIPPER_IP = '192.168.0.117'
GRIPPER_TOLERANCE = 2  # mm
ROBOT_ADDR = ('192.168.0.113', 30002)
ROBOT_HOME = [0.30, -0.2, 0.142, 2.25, -2.25, 0]

class Logic:
    def __init__(self, addr):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect(addr)

    def get_task(self):
        print("{} - Querying task".format(NAME))
        self.server.send('get'.encode())
        recv_pos = self.server.recv(1024).decode().strip()
        task = json.loads(recv_pos)
        print("{} - Received task: {}".format(NAME, json.dumps(task, indent=4)))
        return task

class Monitor:
    def __init__(self, addr):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect(addr)

    def wait(self, pose):
        position = pose[:3]
        print("{} - Waiting for move completion".format(NAME))
        self.server.send(json.dumps(position).encode())
        recv = self.server.recv(1024).decode().strip()
        print("{} - Move completed".format(NAME))

class Gripper:
    def __init__(self, ip):
        self.ip = ip

    def wait(self, width):
        actual_width = 1000  # outside range
        request = 'http://{}/sensor_data'.format(self.ip)
        while abs(actual_width - width) > GRIPPER_TOLERANCE:
            resp = requests.get(request)
            data = json.loads(resp.text)
            actual_width = data['devices'][0]['variable']['backpack']['width']
        print("{} - Gripper is set".format(NAME))

    def set_params(self, data):
        self.opened_mm = data['open']
        self.closed_mm = data['close']

    def set_width(self, width):
        print("{} - Setting gripper to {}mm".format(NAME, width))
        resp = requests.get('http://{}/api/dc/rg2ft/set_width/{}/40'.format(self.ip, width))
        if resp.status_code == 200:
            print("{} - OK".format(NAME))
            self.wait(width)
        else:
            raise Exception('Connection to gripper failed')

    def close(self):
        self.set_width(self.closed_mm)

    def open(self):
        self.set_width(self.opened_mm)

class Robot:
    def __init__(self, addr):
        self.robot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.monitor = Monitor(MONITOR_ADDR)
        self.gripper = Gripper(GRIPPER_IP)
        self.payload = 0
        self.robot.connect(addr)
        self._move_home()

    def _create_move_command(self, move_type, pose):
        return '{}(get_inverse_kin(p{}))\n'.format(move_type, json.dumps(pose))

    def _create_payload_command(self, payload):
        return 'set_payload({})\n'.format(payload)

    def _send_command(self, command):
        print("{} - Sending command - {}".format(NAME, command.strip()))
        self.robot.send(command.encode())

    def _move_home(self):
        command = self._create_move_command('movej', ROBOT_HOME)
        self._send_command(command)
        self.monitor.wait(ROBOT_HOME)

    def _move_above(self, data):
        pose = data['pose'].copy()
        pose[2] += data['lift_height']
        command = self._create_move_command('movej', pose)
        self._send_command(command)
        self.monitor.wait(pose)

    def _move_vertical(self, data, direction):
        if direction not in ['up', 'down']:
            raise Exception('Invalid parameter for direction - {}'.format(direction))

        pose = data['pose'].copy()
        if direction is 'up':
            pose[2] += data['lift_height']

        command = self._create_move_command('movel', pose)
        self._send_command(command)
        self.monitor.wait(pose)

    def _set_payload(self, payload):
        command = self._create_payload_command(payload)
        self._send_command(command)

    def setup_gripper(self, gripper_data):
        self.gripper.set_params(gripper_data)
        self.gripper.open()
        self.payload = gripper_data['payload']

    def pick_up(self, location_data):
        self._move_above(location_data)
        self._move_vertical(location_data, 'down')
        self._set_payload(self.payload)
        self.gripper.close()
        self._move_vertical(location_data, 'up')

    def put_down(self, location_data):
        self._move_above(location_data)
        self._move_vertical(location_data, 'down')
        self._set_payload(0)
        self.gripper.open()
        self._move_vertical(location_data, 'up')

if __name__ == "__main__":
    logic = Logic(LOGIC_ADDR)
    robot = Robot(ROBOT_ADDR)

    while True:
        task = logic.get_task()

        robot.setup_gripper(task['gripper'])
        robot.pick_up(task['from'])
        robot.put_down(task['to'])

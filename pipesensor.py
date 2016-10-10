## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME:
## STUDENT ID:
import sys
import struct
import select
import time
import numpy as np
from socket import *
from random import randint
from sensor import *


# Get random position in NxN grid.
def random_position(n):
    x = randint(0, n)
    y = randint(0, n)
    return (x, y)

class sensor:
    pos = ""
    val = ""
    srange = ""

    def __init__(self, pos, val, srange):
        self.pos = pos
        self.val = val
        self.srange = srange
    

def getDistance(pos1, pos2):
    return np.sqrt(np.power(pos1[0] - pos2[0], 2) + np.power(pos1[1] - pos2[1],
                                                             2))

def getNeighbours(peer, mcast_addr):
    enc_message = message_encode(0, 0, sensor.pos, (0, 0), 0, sensor.srange, 0)
    peer.sendto(enc_message, mcast_addr)
        

def initiateEcho(peer, neighbours, sequenceNumber, operation, sensor_val=0):
    payload = 0
    if operation == 3 or operation == 4:
        payload = sensor.val
    if neighbours == [] and operation == 1:
        address = peer.getsockname()
        message = message_encode(3, sequenceNumber, sensor.pos, (0,0), operation, sensor_val, 0)
        peer.sendto(message, address)
    elif neighbours == []:
        address = peer.getsockname()
        message = message_encode(3, sequenceNumber, sensor.pos, (0,0), operation, sensor_val, sensor_val)
        peer.sendto(message, address)
    else:
        for neighbour in neighbours:
            message = message_encode(2, sequenceNumber, sensor.pos, (0,0),
                                     operation, sensor_val, payload)
            peer.sendto(message, neighbour[0])
    sequenceNumber += 1
    return sequenceNumber


def forward_echo(peer, neighbours, init_seq, init_pos, operation, father_addr, payload, sensor_val=0):
    for neighbour in neighbours:
        if neighbour[0] != father_addr:
            message = message_encode(2, init_seq, init_pos, (0, 0), operation, sensor_val, payload)
            peer.sendto(message, neighbour[0])


def send_echo_reply(peer, init_seq, init_pos, father_addr, operation, payload, ident, sensor_val=0):
    if operation == 0:
        message = message_encode(3, init_seq, init_pos, (0, 0), 0, 0, 0)
        peer.sendto(message, father_addr)
    elif operation == 1:
        if ident != 2:
            payload = ident
        else:
            payload += 1
        message = message_encode(3, init_seq, init_pos, (0,0), operation, 0, payload)
        peer.sendto(message, father_addr)        
    elif operation == 2:
        if ident > 0:
            payload += sensor.val
        message = message_encode(3, init_seq, init_pos, (0,0), operation, 0, payload)
        peer.sendto(message, father_addr)
    elif operation == 3:
        if ident > 0 and payload > sensor.val:
            payload = sensor.val
        message = message_encode(3, init_seq, init_pos, (0,0), operation, 0, payload)
        peer.sendto(message, father_addr)
    elif operation == 4:
        if ident > 0 and payload < sensor.val:
            payload = sensor.val
        message = message_encode(3, init_seq, init_pos, (0,0), operation, 0, payload)
        peer.sendto(message, father_addr)
    elif operation == 5:
        if sensor.val == sensor_val and ident > 0:
            payload += 1
        message = message_encode(3, init_seq, init_pos, (0,0), operation, sensor_val, payload)
        peer.sendto(message, father_addr)


def main(mcast_addr,
    sensor_pos, sensor_range, sensor_val,
    grid_size, ping_period):
    """
    mcast_addr: udp multicast (ip, port) tuple.
    sensor_pos: (x,y) sensor position tuple.
    sensor_range: range of the sensor ping (radius).
    sensor_val: sensor value.
    grid_size: length of the  of the grid (which is always square).
    ping_period: time in seconds between multicast pings.
    """
    # -- Create the multicast listener socket. --
    mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    # Sets the socket address as reusable so you can run multiple instances
    # of the program on the same machine at the same time.
    mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    # Subscribe the socket to multicast messages from the given address.
    mreq = struct.pack('4sl', inet_aton(mcast_addr[0]), INADDR_ANY)
    mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
    if sys.platform == 'win32':  # windows special case
        mcast.bind(('localhost', mcast_addr[1]))
    else:  # should work for everything else
        mcast.bind(mcast_addr)

    # -- Create the peer-to-peer socket. --
    peer = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    # Set the socket multicast TTL so it can send multicast messages.
    peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)
    # Bind the socket to a random port.
    if sys.platform == 'win32':  # windows special case
        peer.bind(('localhost', INADDR_ANY))
    else:  # should work for everything else
        peer.bind(('', INADDR_ANY))

    getNeighbours(peer, mcast_addr)
    neighbours = []
    timeCounter = 0
    sequenceNumber = 0
    echo_log = {}
    operation_list = ["echo", "size", "sum", "min", "max", "same"]
    # -- This is the event loop. --
    # commandList = ["size", "sum", "max"]
    commandList = ["size", "min", "max", ""]
    indexCommand = 0
    counter = 0
    print(sensor.pos)
    while True:
        [rlist, wlist, xlist] = select.select([mcast, peer], [], [], 0)
        # add neighbors to list
        for neighbor_socket in rlist:
            data, address = neighbor_socket.recvfrom(512)
            dec_message = message_decode(data)

            messType = dec_message[0]
            sequence = dec_message[1]
            initPos = dec_message[2]
            neighPos = dec_message[3]
            operation = dec_message[4]
            capability = dec_message[5]
            payload = dec_message[6]
            if messType != 0 and messType != 1:
                print(dec_message)
            if messType == 0:
                pos_init = initPos
                distance = getDistance(pos_init, sensor.pos)
                if distance == 0:
                    continue
                elif distance < capability:
                    enc_message = message_encode(1, 0, pos_init, sensor.pos)
                    peer.sendto(enc_message, address)
            elif messType == 1:
                neighbours.append([address, neighPos])
            elif messType == 2:
                keyLog = str(sequence) + str(initPos)

                if echo_log.get(keyLog) != None:
                    send_echo_reply(peer, sequence, initPos, address, operation, payload, 0, capability)
                elif len(neighbours) == 1:
                    send_echo_reply(peer, sequence, initPos, address, operation, payload, 1, capability)
                else:
                    echo_log[keyLog] = []
                    echo_log[keyLog].append(len(neighbours) - 1)
                    opcode = operation
                    if opcode == 3 or opcode == 4:
                        echo_log[keyLog].append(sensor.val)
                    else:
                        echo_log[keyLog].append(0)
                        echo_log[keyLog].append(address)
                        forward_echo(peer, neighbours, sequence, initPos, operation,
                                     address, payload, capability)
            elif messType == 3:
                messLog = echo_log[str(sequence) + str(initPos)]
                if messLog[0] == 1 or messLog[0] == 0:
                    if sequence <= sequenceNumber and initPos == sensor.pos:

                        if operation == 1:
                            print("networksize " + str(payload + messLog[1] + 1) + "\n")
                            indexCommand += 1
                        elif operation == 2:
                            print("valuesum " + str(payload + messLog[1] + sensor.val) + "\n")
                            indexCommand += 1
                        elif operation == 3:
                            if messLog[1] > payload:
                                messLog[1] = payload
                            print("minimumval " + str(messLog[1]) + "\n")
                            indexCommand += 1
                        elif operation == 4:
                            if messLog[1] < payload:
                                messLog[1] = payload
                            print("maximumval " + str(messLog[1]) + "\n")
                            indexCommand += 1
                        elif operation == 5:
                            print("sameval " + str(payload + messLog[1] + 1) + "\n")
                            indexCommand += 1
                    else:
                        father_addr = messLog[2]
                        op_list = [1, 2, 5]
                        if operation in op_list:
                            send_echo_reply(peer, sequence, initPos, father_addr, operation, messLog[1] + payload, 2, capability)
                        elif operation == 3:
                            if messLog[1] > payload:
                                messLog[1] = payload
                                send_echo_reply(peer, sequence, initPos, father_addr, operation, messLog[1], 2, capability)
                        elif operation == 4:
                            if messLog[1] < payload:
                                messLog[1] = payload
                                send_echo_reply(peer, sequence, initPos, father_addr, operation, messLog[1], 2, capability)
                    del messLog
                else:
                    messLog[0] -= 1
                    if operation == 1 or operation == 2 or operation == 5:
                        messLog[1] += payload
                    elif operation == 3 and messLog[1] > payload:
                        messLog[1] = payload
                    elif operation == 4 and messLog[1] < payload:
                        messLog[1] = payload
        if (counter % 300) == 0 and timeCounter > 0:
            command = commandList[indexCommand]
            if command in operation_list:
                print("Command sent " + command)
                opcode = operation_list.index(command)
                echo_log[str(sequenceNumber) + str(sensor.pos)] = []
                echo_log[str(sequenceNumber) + str(sensor.pos)].append(len(neighbours))
                if opcode == 3 or opcode == 4:
                    echo_log[str(sequenceNumber) + str(sensor.pos)].append(sensor.val)
                else:
                    echo_log[str(sequenceNumber) + str(sensor.pos)].append(0)
                sequenceNumber = initiateEcho(peer, neighbours, sequenceNumber, opcode, sensor.val)
        time.sleep(0.01)
        timeCounter += 1
        counter += 1
        if timeCounter == ping_period:
            neighbours = []
            getNeighbours(peer, mcast_addr)
            timeCounter = 0

                



import argparse
p = argparse.ArgumentParser()
p.add_argument('--range', help='sensor range', default=50, type=int)
args = p.parse_args(sys.argv[1:])
pos = random_position(100)
value = randint(0, 100)
mcast_addr = ('224.1.1.1', 50100)
sensor = sensor(pos, value, args.range)
period = 200
grid = 100
main(mcast_addr, pos, args.range, value, grid, period)




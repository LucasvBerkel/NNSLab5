# Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
# NAME: Julian Main, Lucas van Berkel
# STUDENT ID: ... , 10747958
import sys
import struct
import select
import time
import numpy as np
from socket import *
from random import randint
from gui import MainWindow
from sensor import *


# Get random position in NxN grid.
def random_position(n):
    x = randint(0, n)
    y = randint(0, n)
    return (x, y)


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

    # -- make the gui --
    window = MainWindow()
    window.writeln('my address is %s:%s' % peer.getsockname())
    window.writeln('my position is (%s, %s)' % sensor.pos)
    window.writeln('my sensor value is %s' % sensor.val)

    getNeighbours(peer, mcast_addr)

    neighbours = []
    timeCounter = 0
    sequenceNumber = 0
    echo_log = {}
    operation_list = ["echo", "size", "sum", "min", "max", "same"]
    # -- This is the event loop. --
    while window.update():
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
                window.writeln(str(dec_message))
                if echo_log.get(keyLog) is not None:
                    send_echo_reply(peer, sequence, initPos,
                                    address, operation, payload, 0, capability)
                elif len(neighbours) == 1:
                    send_echo_reply(peer, sequence, initPos, address,
                                    operation, payload, 1, capability)
                else:
                    echo_log[keyLog] = []
                    echo_log[keyLog].append(len(neighbours) - 1)
                    opcode = operation
                    if opcode == 3 or opcode == 4:
                        echo_log[keyLog].append(sensor.val)
                    else:
                        echo_log[keyLog].append(0)
                    echo_log[keyLog].append(address)
                    forward_echo(peer, neighbours, sequence,
                                 initPos, operation,
                                 address, payload, capability)
            elif messType == 3:
                window.writeln(str(dec_message))
                messLog = echo_log[str(sequence) + str(initPos)]
                if messLog[0] == 1:
                    if sequence <= sequenceNumber and initPos == sensor.pos:
                        window.writeln("Echo wave " +
                                       str(sequence) + " is decided.")
                        if operation == 0:
                            window.writeln("Payload " + str(payload))
                        elif operation == 1:
                            window.writeln("Size network is " +
                                           str(payload + messLog[1] + 1))
                        elif operation == 2:
                            window.writeln("The sum of values is " +
                                           str(payload + messLog[1] +
                                               sensor.val))
                        elif operation == 3:
                            if messLog[1] > payload:
                                messLog[1] = payload
                            window.writeln("The mini\
                                            mum value of the netwerk is " +
                                           str(messLog[1]))
                        elif operation == 4:
                            if messLog[1] < payload:
                                messLog[1] = payload
                            window.writeln("The maximum value of\
                                            the netwerk is " +
                                           str(messLog[1]))
                        elif operation == 5:
                            window.writeln("Numbers of sensors with\
                                            same value is " +
                                           str(payload + messLog[1] + 1))
                    else:
                        father_addr = messLog[2]
                        op_list = [1, 2, 5]
                        if operation in op_list:
                            send_echo_reply(peer, sequence, initPos,
                                            father_addr, operation,
                                            messLog[1] + payload,
                                            2, capability)
                        elif operation == 3:
                            if messLog[1] > payload:
                                messLog[1] = payload
                            send_echo_reply(peer, sequence, initPos,
                                            father_addr, operation, messLog[1],
                                            2, capability)
                        elif operation == 4:
                            if messLog[1] < payload:
                                messLog[1] = payload
                            send_echo_reply(peer, sequence, initPos,
                                            father_addr, operation, messLog[1],
                                            2, capability)
                    del messLog
                else:
                    messLog[0] -= 1
                    if operation == 1 or operation == 2 or operation == 5:
                        messLog[1] += payload
                    elif operation == 3 and messLog[1] > payload:
                        messLog[1] = payload
                    elif operation == 4 and messLog[1] < payload:
                        messLog[1] = payload

        line = window.getline()
        subParts = line.split(" ")

        if subParts[0] == "ping":
            neighbours = []
            getNeighbours(peer, mcast_addr)
        elif subParts[0] == "move":
            sensor.pos = random_position(grid_size)
            window.writeln('my new position is (%s, %s)' % sensor.pos)
            neighbours = []
            getNeighbours(peer, mcast_addr)
        elif subParts[0] == "list":
            if neighbours == []:
                window.writeln("You have no known neighbours")
            else:
                for neighbour in neighbours:
                    window.writeln("Ip: " + str(neighbour[0][0]))
                    window.writeln("Port: " + str(neighbour[0][1]))
                    window.writeln("")
        elif subParts[0] == "set":
            if int(subParts[1]) >= 20 and int(subParts[1]) <= 70
            and (int(subParts[1]) % 10) == 0:
                sensor.srange = int(subParts[1])
                neighbours = []
                getNeighbours(peer, mcast_addr)
            else:
                window.writeln("Range need to be between\
                                20 and 70(with steps of 10)")
        elif subParts[0] in operation_list:
            opcode = operation_list.index(subParts[0])
            echo_log[str(sequenceNumber) + str(sensor.pos)] = []
            echo_log[str(sequenceNumber) +
                     str(sensor.pos)].append(len(neighbours))
            if opcode == 3 or opcode == 4:
                echo_log[str(sequenceNumber) +
                         str(sensor.pos)].append(sensor.val)
            else:
                echo_log[str(sequenceNumber) +
                         str(sensor.pos)].append(0)
            sequenceNumber = initiateEcho(peer, neighbours,
                                          sequenceNumber, window,
                                          opcode, sensor.val)
        time.sleep(0.1)
        timeCounter += 1
        if timeCounter == ping_period:
            neighbours = []
            getNeighbours(peer, mcast_addr)
            timeCounter = 0


def getDistance(pos1, pos2):
    return np.sqrt(np.power(pos1[0] - pos2[0], 2) + np.power(pos1[1] - pos2[1],
                                                             2))


def getNeighbours(peer, mcast_addr):
    enc_message = message_encode(0, 0, sensor.pos, (0, 0), 0, sensor.srange, 0)
    peer.sendto(enc_message, mcast_addr)


def initiateEcho(peer, neighbours, sequenceNumber,
                 window, operation, sensor_val=0):
    payload = 0
    if operation == 3 or operation == 4:
        payload = sensor.val
    if neighbours == []:
        window.writeln("You have no neighbours to send the echo to")
    else:
        for neighbour in neighbours:
            message = message_encode(2, sequenceNumber, sensor.pos, (0, 0),
                                     operation, sensor_val, payload)
            peer.sendto(message, neighbour[0])
        sequenceNumber += 1
    return sequenceNumber


def forward_echo(peer, neighbours, init_seq, init_pos,
                 operation, father_addr, payload, sensor_val=0):
    for neighbour in neighbours:
        if neighbour[0] != father_addr:
            message = message_encode(2, init_seq, init_pos, (0, 0),
                                     operation, sensor_val, payload)
            peer.sendto(message, neighbour[0])


def send_echo_reply(peer, init_seq, init_pos, father_addr,
                    operation, payload, ident, sensor_val=0):
    if operation == 0:
        message = message_encode(3, init_seq, init_pos, (0, 0), 0, 0, 0)
        peer.sendto(message, father_addr)
    elif operation == 1:
        if ident != 2:
            payload = ident
        else:
            payload += 1
        message = message_encode(3, init_seq, init_pos,
                                 (0, 0), operation, 0, payload)
        peer.sendto(message, father_addr)
    elif operation == 2:
        if ident > 0:
            payload += sensor.val
        message = message_encode(3, init_seq, init_pos,
                                 (0, 0), operation, 0, payload)
        peer.sendto(message, father_addr)
    elif operation == 3:
        if ident > 0 and payload > sensor.val:
            payload = sensor.val
        message = message_encode(3, init_seq, init_pos,
                                 (0, 0), operation, 0, payload)
        peer.sendto(message, father_addr)
    elif operation == 4:
        if ident > 0 and payload < sensor.val:
            payload = sensor.val
        message = message_encode(3, init_seq, init_pos,
                                 (0, 0), operation, 0, payload)
        peer.sendto(message, father_addr)
    elif operation == 5:
        if sensor.val == sensor_val and ident > 0:
            payload += 1
        message = message_encode(3, init_seq, init_pos,
                                 (0, 0), operation, sensor_val, payload)
        peer.sendto(message, father_addr)


class sensor:
    pos = ""
    val = ""
    srange = ""

    def __init__(self, pos, val, srange):
        self.pos = pos
        self.val = val
        self.srange = srange

# -- program entry point --
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--group', help='multicast group', default='224.1.1.1')
    p.add_argument('--port', help='multicast port', default=50100, type=int)
    p.add_argument('--pos', help='x,y sensor position', default=None)
    p.add_argument('--grid', help='size of grid', default=100, type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--value', help='sensor value', default=-1, type=int)
    p.add_argument('--period', help='period between autopings (0=off)',
                   default=50, type=int)
    args = p.parse_args(sys.argv[1:])
    if args.pos:
        pos = tuple(int(n) for n in args.pos.split(',')[:2])
    else:
        pos = random_position(args.grid)
    if args.value >= 0:
        value = args.value
    else:
        value = randint(0, 100)
    mcast_addr = (args.group, args.port)
    sensor = sensor(pos, value, args.range)
    main(mcast_addr, pos, args.range, value, args.grid, args.period)

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
    window.writeln('my position is (%s, %s)' % sensor_pos)
    window.writeln('my sensor value is %s' % sensor_val)

    getNeighbours(peer, mcast_addr, sensor_pos, sensor_range)

    neighbours = []
    timeCounter = 0
    REFRESHNEIGHBOUR = 50
    # -- This is the event loop. --
    while window.update():
        [rlist, wlist, xlist] = select.select([mcast, peer], [], [], 0)

        # add neighbors to list
        for neighbor_socket in rlist:
            data, address = neighbor_socket.recvfrom(512)
            dec_message = message_decode(data)
            print dec_message
            if dec_message[0] == 0:
                pos_init = dec_message[2]
                distance = getDistance(pos_init, sensor_pos)
                if distance == 0:
                    continue
                elif distance < dec_message[5]:
                    enc_message = message_encode(1, 0, pos_init, sensor_pos)
                    peer.sendto(enc_message, address)
            elif dec_message[0] == 1:
                neighbours.append([address, dec_message[3]])
        line = window.getline()
        subParts = line.split(" ")
        if subParts[0] == "ping":
            neighbours = []
            getNeighbours(peer, mcast_addr, sensor_pos, sensor_range)
        elif subParts[0] == "move":
            sensor_pos = random_position(grid_size)
            window.writeln('my new position is (%s, %s)' % sensor_pos)
            neighbours = []
            getNeighbours(peer, mcast_addr, sensor_pos, sensor_range)
        elif subParts[0] == "list":
            if neighbours == []:
                window.writeln("You have no known neighbours")
            else:
                for neighbour in neighbours:
                    window.writeln("Ip: " + str(neighbour[0][0]))
                    window.writeln("Port: " + str(neighbour[0][1]))
                    window.writeln("")
        elif subParts[0] == "set":
            if int(subParts[1]) >= 20 and int(subParts[1]) <= 70 and (int(subParts[1]) % 10) == 0:
                sensor_range = int(subParts[1])
                neighbours = []
                getNeighbours(peer, mcast_addr, sensor_pos, sensor_range)
            else:
                window.writeln("Range need to be between 20 and 70(with steps of 10)") 
        elif subParts[0] == "echo":
            initiateEcho(peer, neighbours, sensor_pos, sensor_range)

        time.sleep(0.1)
        timeCounter += 1
        if timeCounter == REFRESHNEIGHBOUR:
            neighbours = []
            getNeighbours(peer, mcast_addr, sensor_pos, sensor_range)
            timeCounter = 0

def initiateEcho(peer, neighbours, sensor_pos, sensor_range):
    for neighbour in neighbours:
        message = message_encode(2, 0, sensor_pos, neighbour[1], 0, 0, 0)
        peer.sendto(message, neighbour[0])

def getDistance(pos1, pos2):
    return np.sqrt(np.power(pos1[0] - pos2[0], 2) + np.power(pos1[1] - pos2[1], 2))

def getNeighbours(peer, mcast_addr, sPos, sRange):
    enc_message = message_encode(0, 0, sPos, (0,0), 0, sRange, 0)
    peer.sendto(enc_message, mcast_addr)
        

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
                   default=5, type=int)
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
    main(mcast_addr, pos, args.range, value, args.grid, args.period)

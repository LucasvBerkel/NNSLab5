# Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
# NAME: Julian Main, Lucas van Berkel
# STUDENT ID: ..., 10747958

import subprocess
import time
import matplotlib.pyplot as plt


def get_file_length(file_name):
    counter = 0
    while True:
        try:
            with open(file_name) as f:
                for line in f:
                    counter = counter + 1
        except:
            pass
        break
    return counter


def main(nodes, r, steps):

    # Store processes.
    processes = []

    for node in range(nodes):

        # Open a process.
        processes.append(subprocess.Popen(['python', 'pipesensor.py',
                                           '--range', str(r)],
                                          stdout=subprocess.PIPE,
                                          stdin=subprocess.PIPE))
        # Send our sensor range.
        # Read the output of pipe-example.py
        while True:
            # print get_file_length(str(r) + "_max.txt")
            time.sleep(0.1)
            if get_file_length(str(r) + "_max.txt") > node:
                break
        print "Received something from node %d" % (node)

    for p in processes:
        p.terminate()


def plot_range_connected(nodes, steps, stepsize):
    """
    plots the relation between sensor range and chance of all nodes in network
    being connected
    """

    sensor_range_list = range(0, 60, stepsize)  # the x-axis for the plot
    all_nodes_connected = []  # the y-axis for the plot

    # calculate networksize, min, max for 0-100 sensor_range
    for sensor_range in range(0, 60, stepsize):
        main(nodes, sensor_range, steps)

    # check if all nodes connected for each sensor range
    for sensor_range in range(0, 60, stepsize):
        size_list = get_file_as_list(sensor_range, "size")
        network_size = float(size_list[-1].split(" ")[-1])
        if network_size == float(nodes):
            all_nodes_connected.append(1)
        else:
            all_nodes_connected.append(0)

    plt.plot(sensor_range_list, all_nodes_connected)
    plt.xlabel("sensor range")
    plt.ylabel("all nodes connected")
    plt.show()


def plot_nodes_connected(steps, sensor_range, stepsize):
    """
    plots the relation between amount of nodes and chance of all nodes in
    network being connected
    """

    node_range_list = range(0, 60, stepsize)  # the x-axis for the plot
    all_nodes_connected = []  # the y-axis for the plot

    # calculate networksize, min, max for 0-100 nodes
    for nodes in range(0, 60, stepsize):
        main(nodes, sensor_range, steps)

    # check if all nodes connected for each amount of nodes
    for nodes in range(0, 60, stepsize):
        size_list = get_file_as_list(sensor_range, "size")
        network_size = float(size_list[-1].split(" ")[-1])
        if network_size == float(nodes):
            all_nodes_connected.append(1)
        else:
            all_nodes_connected.append(0)

    plt.plot(node_range_list, all_nodes_connected)
    plt.xlabel("number of nodes")
    plt.ylabel("all nodes connected")
    plt.show()


def get_file_as_list(sensor_range, file_type):
    """"
    reads file line by line and returns list with each line as element
    sensor_range: prefix of file to read
    file_type: min, max, size
    """
    file_name = str(sensor_range) + "_" + file_type + ".txt"
    # line[0:-1] to remove newline character
    return [line[0:-1] for line in open(file_name)]


if __name__ == '__main__':
    import argparse
    import sys
    p = argparse.ArgumentParser()
    p.add_argument('--nodes', help='number of nodes to spawn', required=True,
                   type=int)
    p.add_argument('--range', help='sensor range', default=50, type=int)
    p.add_argument('--steps', help='output graph info every step',
                   action="store_true")
    args = p.parse_args(sys.argv[1:])
    plot_range_connected(args.nodes, args.steps, 20)
    plot_nodes_connected(args.steps, 50, 20)
#    main(args.nodes, args.range, args.steps)

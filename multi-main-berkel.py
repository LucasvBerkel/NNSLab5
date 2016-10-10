# Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
# NAME:
# STUDENT ID:

import subprocess
import time

def get_file_length(file_name):
    return sum(1 for line in open(file_name))

def main(nodes, r, steps):

    # Store processes.
    processes = []

    for node in range(nodes):

        # Open a process.
        processes.append(subprocess.Popen(['python', 'pipesensor.py'],
                                          stdout=subprocess.PIPE,
                                          stdin=subprocess.PIPE))
        # Send our sensor range.
        # Read the output of pipe-example.py
        while get_file_length("max.txt") != (node+1):
            print get_file_length("max.txt")
            time.sleep(0.1)

        print "Received something from node %d" % (node)

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
    main(args.nodes, args.range, args.steps)

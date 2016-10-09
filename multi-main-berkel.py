# Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
# NAME:
# STUDENT ID:

import subprocess


def main(nodes, r, steps):

    # Store processes.
    processes = []

    processes.append(subprocess.Popen(['python', 'pipesensor.py'],
                                      stdout=subprocess.PIPE,
                                      stdin=subprocess.PIPE))

    processes[0].stdin.flush()

    for node in range(nodes):
        print("in loop")
        # Open a process.
        processes.append(subprocess.Popen(['python', 'pipesensor.py'],
                                          stdout=subprocess.PIPE,
                                          stdin=subprocess.PIPE))
        # Send our sensor range.
#        p.stdin.write("%s\n" % r)
        processes[node + 1].stdin.flush()
        # Read the output of pipe-example.py
        string = ""
        while True:
            # Read a single character.

            char = processes[node + 1].stdout.read(1)
            # If the character is a newline, we have our data!
            if char == "\n":
                break

            # Append the character to the string.
            string += char

        print "Received something from node %d: %s" % (node, string)

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

#!/usr/bin/env python2

import argparse, re
from uuid import uuid4
from math import pow, sqrt

RE_G0 = re.compile(r'G00 X(?P<x>\d+\.\d+) Y(?P<y>\d+\.\d+)')

parser = argparse.ArgumentParser(description='gcodeblocksort')
parser.add_argument('input', metavar='FILE',)
args = parser.parse_args()

nodes = {}
blocks = {}

with open(args.input) as f:
    block = []
    rapids = 1
    header = []
    footer = []
    p = ''
    x, y = 0, 0

    # read header
    for l in f:
        l = l.strip()
        header.append(l)
        if l.startswith('G00'):
            break

    # read in blocks
    for l in f:
        l = l.strip()
        if l and l != p:
            block.append(l)
            if l.startswith('G00'):
                rapids += 1
                m = RE_G0.match(l)
                if m:
                    x = float(m.group('x'))
                    y = float(m.group('y'))

            if rapids == 2:
                name = uuid4()
                nodes[name] = (x, y)
                blocks[name] = block
                block = []
                rapids = 0
            p = l
        if l.startswith('M5'):
            footer.append(l)
            break

    # read footer
    for l in f:
        l = l.strip()
        footer.append(l)


path = []
length = 0.0
x, y = 0, 0

while 1:
    best = float('inf')
    for candidate in nodes:
        if candidate not in path:
            (i, j) = nodes[candidate]
            distance = abs(sqrt(pow(abs(i - x), 2) + pow(abs(j - y), 2)))
            #print '%s is %f away' % (candidate, distance)
            if distance < best:
                #print '%s is better than %f' % (candidate, best)
                winner = candidate
                best = distance
    #print '%s won' % winner
    path.append(winner)
    if len(nodes) == len(path):
        break

for l in header:
    print l

for node in path:
    print '(Node Block %s)' % node
    for l in blocks[node]:
        print l

for l in footer:
    print l

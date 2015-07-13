#!/usr/bin/env python2

import argparse, re, logging
from uuid import uuid4
from math import pow, sqrt

RE_G0 = re.compile(r'G00 X(?P<x>\d+\.\d+) Y(?P<y>\d+\.\d+)')

parser = argparse.ArgumentParser(description='gcodeblocksort')
parser.add_argument('input', metavar='FILE',)
parser.add_argument('--debug', action='store_true')
args = parser.parse_args()

logger = logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', name="gcodeblocksort")
logger = logging.getLogger("ssp")
if args.debug:
    logger.setLevel(logging.DEBUG)

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
    logger.debug('Finding next path step')
    best = float('inf')
    for candidate in nodes:
        logger.debug('  Examining candidate %s' % candidate)
        if candidate not in path:
            logger.debug('    Candidate is not already in path')
            (i, j) = nodes[candidate]
            distance = abs(sqrt(pow(abs(i - x), 2) + pow(abs(j - y), 2)))
            logger.debug('    %s is %f away' % (candidate, distance))
            if distance < best:
                logger.debug('    New best! (distance %f is better than %f)' % (distance, best))
                winner = candidate
                best = distance
    logger.debug('    %s won' % winner)
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

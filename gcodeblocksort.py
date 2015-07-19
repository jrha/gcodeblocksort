#!/usr/bin/env python2

import argparse, re, logging
from uuid import uuid4
from math import pow, sqrt

MODES = {
    'plain' : {
        #'header' : re.compile(r'^%$'),
        'block' : re.compile(r'^G00 X(?P<x>\d+\.\d+) Y(?P<y>\d+\.\d+)'),
        'start' : re.compile(r'^G00 X(?P<x>\d+\.\d+) Y(?P<y>\d+\.\d+)$'),
        'footer' : re.compile(r'^M5$'),
    },
    'inkscape' : {
        #'header' : re.compile(r'^(Header)$'),
        'block' : re.compile(r'^\(Start cutting path id: (?P<name>.+)\)$'),
        'start' : re.compile(r'^G00 X(?P<x>\d+\.\d+) Y(?P<y>\d+\.\d+)$'),
        'footer' : re.compile(r'^\(Footer\)$'),
    },
}

parser = argparse.ArgumentParser(description='gcodeblocksort')
parser.add_argument('input', metavar='FILE',)
parser.add_argument('--debug', action='store_true')
parser.add_argument('--mode', choices=MODES, default='inkscape')
args = parser.parse_args()

logger = logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', name="gcodeblocksort")
logger = logging.getLogger("ssp")
if args.debug:
    logger.setLevel(logging.DEBUG)

logger.debug('Using %s mode' % args.mode)

nodes = {}

with open(args.input) as f:
    previous_line = ''
    block = []
    x, y = 0, 0

    sections = {
        'header' : [],
        'blocks' : {},
        'footer' : [],
    }
    section = 'header'

    for line in f:
        line = line.rstrip()
        if line and line != previous_line:
            is_block = MODES[args.mode]['block'].match(line)
            if is_block:
                if section == 'blocks':
                    # Start of new block, flush current block
                    sections['blocks'][name] = block
                else:
                    section = 'blocks'
                # Clear current block
                block = []
                name ="%s_%s" % (is_block.group('name'), uuid4())
                sections['blocks'][name] = []
                logger.debug('Found block %s' % name)

            is_footer = MODES[args.mode]['footer'].match(line)
            if is_footer:
                logger.debug('Found footer')
                section = 'footer'

            if section != 'blocks':
                sections[section].append(line)
            else:
                block.append(line)
            previous_line = line

    logger.debug('Reached end of file')

    # Find starting locations for each block
    logger.debug('Searching for starting locations')
    for block in sections['blocks']:
        for line in sections['blocks'][block]:
            start = MODES[args.mode]['start'].match(line)
            if start:
                x = float(start.group('x'))
                y = float(start.group('y'))
                nodes[block] = (x, y)
                logger.debug('Found starting point of %f,%f for block %s' % (x, y, block))
                break
        if not start:
            logger.error('Unable to find starting point for block %s' % block)


path = []
length = 0.0
x, y = 0, 0

while len(path) < len(nodes):
    logger.debug('Finding next path step')
    best = float('inf')
    for candidate in nodes:
        logger.debug('  Examining candidate %s' % candidate)
        if candidate not in path:
            logger.debug('    Candidate is not already in path')
            (i, j) = nodes[candidate]
            distance = sqrt(pow(abs(i - x), 2) + pow(abs(j - y), 2))
            logger.debug('    %s is %f away' % (candidate, distance))
            if distance < best:
                logger.debug('    New best! (distance %f is better than %f)' % (distance, best))
                winner = candidate
                best = distance
    logger.debug('    %s won' % winner)
    path.append(winner)
    (x, y) = nodes[winner]

logger.debug('-------- Printing Header --------')
for l in sections['header']:
    print l
print

logger.debug('-------- Printing Path --------')
for node in path:
    print '(Node %s)' % node
    for l in sections['blocks'][node]:
        print l
    print
print

logger.debug('-------- Printing Footer--------')
for l in sections['footer']:
    print l

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""@package CBR
Copyright (C) 2015 University of Virginia. All rights reserved.

file      cbr.py
author    Shawn Chen <sc7cq@virginia.edu>
version   1.0
date      Nov. 1, 2015

LICENSE

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2 of the License, or（at your option）
any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details at http://www.gnu.org/copyleft/gpl.html

brief     parses log files and computes the cumulative bytes ratio (CBR)
usage     python cbr.py <logfile> <csvfile-to-write>
"""


from __future__ import division
import re
import sys
import pytz
from dateutil.parser import parse
from datetime import datetime

# RTT is 55 ms
rtt = 0.001
#rtt = 0.055

def parseMLDM(line):
    """Parses the product size and elapsed time received by MLDM.

    Parses the product size and elapsed receiving time consumed
    for the product (which is received by MLDM) in the given line
    of log file.

    Args:
        line: A line of the raw log file.

    Returns:
        (-1, -1, -1): If no valid size or time is found.
        (prodindex, prodsize, rxtime): A tuple of product index, product size
                                       and receiving time.
    """
    match = re.search(r'.*mldm.*Received', line)
    if match:
        split_line = line.split()
        # the last column is product index
        prodindex = int(split_line[-1])
        # col 6 is size in bytes
        size = int(split_line[6])
        # col 0 is the arrival time, col 7 is the insertion time.
        arrival_time = parse(split_line[0]).astimezone(pytz.utc)
        arrival_time = arrival_time.replace(tzinfo=None)
        insert_time  = datetime.strptime(split_line[7], "%Y%m%d%H%M%S.%f")
        rxtime = (arrival_time - insert_time).total_seconds()
        return (prodindex, size, rxtime)
    else:
        return (-1, -1, -1)


def parseBackstop(line):
    """Parses the product size and elapsed time received by the backstop.

    Parses the product size and elapsed receiving time consumed for the
    product (which is received by the backstop) in the given line of log file.

    Args:
        line: A line of the raw log file.

    Returns:
        (-1, -1, -1): If no valid size or time is found.
        (prodindex, prodsize, rxtime): A tuple of product index, product size
                                       and receiving time.
    """
    match = re.search(r'.*down7.*Inserted', line)
    if match:
        split_line = line.split()
        # the last column is product index
        prodindex = int(split_line[-1])
        # col 5 is size
        size = int(split_line[5])
        # col 0 is the arrival time, col 6 is the insertion time.
        arrival_time = parse(split_line[0]).astimezone(pytz.utc).replace(tzinfo=None)
        insert_time = datetime.strptime(split_line[6], "%Y%m%d%H%M%S.%f")
        rxtime = (arrival_time - insert_time).total_seconds()
        return (prodindex, size, rxtime)
    else:
        return (-1, -1, -1)


def extractLog(filename):
    """Extracts the key information from the log file.

    Args:
        filename: Filename of the log file.

    Returns:
        (complete_set, complete_dict, vset): extracted groups.
    """
    complete_set  = set()
    complete_dict = {}
    with open(filename, 'r') as logfile:
        for i, line in enumerate(logfile):
            (mprodid, msize, mrxtime) = parseMLDM(line)
            (bprodid, bsize, brxtime) = parseBackstop(line)
            if mprodid >= 0:
                complete_set |= {mprodid}
                if not complete_dict.has_key(mprodid):
                    complete_dict[mprodid] = (msize, mrxtime)
            elif bprodid >= 0:
                complete_set |= {bprodid}
                if not complete_dict.has_key(bprodid):
                    complete_dict[bprodid] = (bsize, brxtime)
    logfile.close()
    return (sorted(complete_set), complete_dict)


def calcCBR(index, complete_dict):
    """Calculates cumulative bytes ratio (CBR) for a product.

    Args:
        index: prodindex of a product
        complete_dict: Dict of complete products.

    Returns:
        cbr: cumulative bytes ratio
        half_full_cbr: CBR that reflects the buffer is half full
    """
    # vc_rate is the circuit rate in bps
    vc_rate    = 40000000
    ideal_time = float(complete_dict[index][0] / vc_rate) + 0.5 * rtt
    half_full_time = float(complete_dict[index][0] / vc_rate) + 0.5 * rtt + 60
    true_time  = complete_dict[index][1]
    if ideal_time and true_time:
        cbr = float(ideal_time / true_time) * 100
        half_full_cbr = float(ideal_time / half_full_time) * 100
    else:
        cbr = -1
        half_full_cbr = -1
    return (cbr, half_full_cbr)


def main(logfile, csvfile):
    """Reads the raw log file and parses it.

    Reads the raw ldmd log file, parses each line and computes throughput
    and VSR over an aggregate size.

    Args:
        metadata: Filename of the metadata.
        logfile: Filename of the log file.
        csvfile : Filename of the new file to contain output results.
    """
    (rx_set, rx_dict) = extractLog(logfile)
    w = open(csvfile, 'w+')
    tmp_str = 'Prodindex, CBR (%), half-full-CBR (%), is-half-full' + '\n'
    w.write(tmp_str)
    for i in rx_set:
        (cbr, half_full_cbr) = calcCBR(i, rx_dict)
        if cbr < half_full_cbr:
            tmp_str = str(i) + ',' + str(cbr) + ',' + str(half_full_cbr) + \
            ',' + str(1) + '\n'
        else:
            tmp_str = str(i) + ',' + str(cbr) + ',' + str(half_full_cbr) + \
            ',' + str(0) + '\n'
        w.write(tmp_str)
    w.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

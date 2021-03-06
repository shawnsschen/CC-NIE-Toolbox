#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""@package ldm_parser
Copyright (C) 2015 University of Virginia. All rights reserved.

file      ldm6_par.py
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

brief     parses log files generated by LDM7 receivers on a specified
          aggregate size basis.
usage     python ldm_parser.py <metadata> <logfile> <csvfile-to-write>
"""


from __future__ import division
import csv
import sys
import pytz
from dateutil.parser import parse
from datetime import datetime


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
    split_line = line.split()
    if split_line[3].isdigit():
        # the last column is product index
        prodindex = int(split_line[-1])
        # col 6 is size in bytes
        size = int(split_line[3])
        # col 0 is the arrival time, col 7 is the insertion time.
        arrival_time = parse(split_line[0]).astimezone(pytz.utc)
        arrival_time = arrival_time.replace(tzinfo=None)
        insert_time  = datetime.strptime(split_line[4], "%Y%m%d%H%M%S.%f")
        rxtime = (arrival_time - insert_time).total_seconds()
        return (prodindex, size, rxtime)
    else:
        return (-1, -1, -1)


def aggregate(filename, aggregate_size):
    """Does aggregating on the given input csv.

    Does size aggregating over a csv file that contains sizes of products in
    the first column and returns the aggregate results.

    Args:
        filename: Filename of the csv file.
        aggregate_size: The size of each aggregate group.

    Returns:
        (groups, sizes): A list of aggregated groups.
    """
    groups   = []
    group    = []
    sizes    = []
    sum_size = 0
    with open(filename, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=' ')
        for i, row in enumerate(csvreader):
            group.append(i)
            sum_size += int(row[0])
            if sum_size >= aggregate_size:
                groups.append(group)
                sizes.append(sum_size)
                group    = []
                sum_size = 0
        if group and sum_size:
            groups.append(group)
            sizes.append(sum_size)
    csvfile.close()
    return (groups, sizes)


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
            if mprodid >= 0:
                complete_set |= {mprodid}
                if not complete_dict.has_key(mprodid):
                    complete_dict[mprodid] = (msize, mrxtime)
    logfile.close()
    return (complete_set, complete_dict)


def calcThroughput(tx_group, complete_set, complete_dict):
    """Calculates throughput for an aggregate.

    Args:
        tx_group: Aggregate group.
        complete_set: Set of complete products.
        complete_dict: Dict of complete products.

    Returns:
        (thru, complete_size): calculated throughputs.
    """
    complete_size = 0
    complete_time = 0
    thru          = 0
    for i in tx_group & complete_set:
        complete_size += complete_dict[i][0]
        complete_time += complete_dict[i][1]
    if complete_time:
        thru = float(complete_size / complete_time) * 8
    else:
        thru = -1
    return (thru, complete_size)


def main(metadata, logfile, csvfile):
    """Reads the raw log file and parses it.

    Reads the raw ldmd log file, parses each line and computes throughput
    and VSR over an aggregate size.

    Args:
        metadata: Filename of the metadata.
        logfile: Filename of the log file.
        csvfile : Filename of the new file to contain output results.
    """
    w = open(csvfile, 'w+')
    aggregate_size = 200 * 1024 * 1024
    (tx_groups, tx_sizes) = aggregate(metadata, aggregate_size)
    (rx_success_set, rx_success_dict) = extractLog(logfile)
    tmp_str = 'Sent first prodindex, Sent last prodindex, Sender aggregate ' \
              'size (B), Successfully received aggregate size (B), ' \
              'Throughput (bps)' + '\n'
    w.write(tmp_str)
    for group, size in zip(tx_groups, tx_sizes):
        (thru, rx_group_size) = calcThroughput(set(group), rx_success_set,
                                               rx_success_dict)
        tmp_str = str(min(group)) + ',' + str(max(group)) + ',' \
                + str(size) + ',' + str(rx_group_size) + ',' \
                + str(thru) + '\n'
        w.write(tmp_str)
    w.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

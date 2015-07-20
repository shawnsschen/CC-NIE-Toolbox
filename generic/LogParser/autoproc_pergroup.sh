#!/bin/bash
##
# Copyright (C) 2015 University of Virginia. All rights reserved.
#
# @file      autoproc_pergroup.sh
# @author    Shawn Chen <sc7cq@virginia.edu>
# @version   1.0
# @date      July 20, 2015
#
# @section   LICENSE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or（at your option）
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details at http://www.gnu.org/copyleft/gpl.html
#
# @brief     Automatically parses the raw log file and generates csv.
# @usage     ./autoproc_pergroup.sh <basename-of-logfile> <experiment number> \
#            <hostname>


metadata=$1
filebase=$2
exptno=$3
host=$4
exp="Expt"
dash="-"
log=".log"
csv=".csv"
run="-run"

# parses all the raw log files one by one
for i in {1..10}
do
    echo "---------- processing log$i ----------"
    python perGroupParser.py $metadata $filebase$i$log $exp$exptno$dash$host$run$i$csv
done

# clean up
mkdir csv
mv *.csv csv

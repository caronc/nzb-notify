#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Notify post-processing script for SABnzbd
#
# Copyright (C) 2014-2016 Chris Caron <lead2gold@gmail.com>
#
# This file adds support for SABnzbd v1.1.0 or higher
#
# NZBGet-Notify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NZBGet-Notify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NZBGet-Notify. If not, see <http://www.gnu.org/licenses/>.
import subprocess
import sys
import os

from os import getpid
from os import kill
from os.path import abspath
from os.path import dirname
from os.path import join
from os.path import isfile

from time import sleep
from datetime import datetime
from datetime import timedelta

import logging
import logging.handlers

logger = logging.getLogger("sabnzbd-notify - %s" % getpid())
logging.raiseExceptions = 0
logger.setLevel(logging.INFO)
h1 = logging.StreamHandler(sys.stdout)
h1.setFormatter(logging. \
    Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
#add h1 to logger
logger.addHandler(h1)

# Path to notify script
NOTIFY_SCRIPT = join(abspath(dirname(__name__)), 'Notify.py')

# Just some timeout value
NOTIFY_MAX_WAIT_TIME_SEC = 300

# A mapping of possible notifications to their respected image.  This
# is only referenced by notifications that support this feature.
SABNZBD_NOTIFICATION_MAP = {
    # Startup/Shutdown
    'startup': ('Startup/Shutdown', '/path/to/image.png'),
    # Added NZB
    'download': ('Added NZB', '/path/to/image.png'),
    # Post-processing started
    'pp': ('Post-Processing Started', '/path/to/image.png'),
    # Job finished
    'complete': ('Job Finished', '/path/to/image.png'),
    # Job failed
    'failed': ('Job Failed', '/path/to/image.png'),
    # Warning
    'warning': ('Warning', '/path/to/image.png'),
    # Error
    'error': ('Error', '/path/to/image.png'),
    # Disk full
    'disk_full': ('Disk Full', '/path/to/image.png'),
    # Queue finished
    'queue_done': ('Queue Finished', '/path/to/image.png'),
    # User logged in
    'new_login': ('User Logged In', '/path/to/image.png'),
    # Other Messages
    'other': ('Other Messages', '/path/to/image.png'),
}


def syntax():
    """
    A simple script to print the syntax to the end user
    """
    return 'Syntax: sabnzbd-notify.py <Type> <Title> <Message> '+\
        'url1[,url2[,urlN]]' +\
        os.linesep + '* The <Type> can be one of the following:' +\
        os.linesep + os.linesep.join(['\t%s: %s' % (k, v[0]) \
                        for (k,v) in SABNZBD_NOTIFICATION_MAP.items()]) +\
        os.linesep + "* The <Title> and <Message> are self explanitory. "+\
        "If the <Title> is however left" + os.linesep +"\tblank, then the "+\
        "description of the <Type> is used instead." + os.linesep +\
        "* All remaining arguments are treated as URLs. You can also " +\
        "delimit multiple" + os.linesep + "\tURLs in a single " +\
        "string/argument with the use of a comma (,)."
    

if __name__ == "__main__":
    # Simple parsing of the command line
    if len(sys.argv) <= 4:
        logger.error('Not enough arguments specified.')
        print(syntax())
        exit(1)

    # Make sure our Notify.py script is available to us
    if not (os.path.isfile(NOTIFY_SCRIPT) and \
            os.access(NOTIFY_SCRIPT, os.X_OK)):
        logger.error('The engine %s was not found!' % NOTIFY_SCRIPT)
        exit(1)

    # Parse our arguments to make sure they're valid
    notify_type = sys.argv[1].strip().lower()
    if notify_type not in SABNZBD_NOTIFICATION_MAP.keys():
        logger.error('Invalid <Type> specified (argument 1)')
        print(syntax())
        exit(1)

    # Take on specified title
    notify_title = sys.argv[2].strip()
    if not notify_title:
        notify_title = SABNZBD_NOTIFICATION_MAP[notify_type][0]

    # Store body (empty or not)
    notify_body = sys.argv[3].strip()

    # The URLs are complex and very depending on what we're notifying
    # so we'll let Notify.py take care of them at this point.
    notify_urls =  ','.join([ v.strip() for v in sys.argv[4:]])

    cmd = [
        NOTIFY_SCRIPT,
        '-t', notify_title,
        '-b', notify_body,
        '-i', SABNZBD_NOTIFICATION_MAP[notify_type][1],
        '-s', notify_urls,
    ]

    # Execute our Process
    p1 = subprocess.Popen(cmd)

    ## Calculate Wait Time
    max_wait_time = datetime.utcnow() + \
                    timedelta(seconds=NOTIFY_MAX_WAIT_TIME_SEC)
    while p1.poll() == None:
        if datetime.utcnow() >= max_wait_time:
            logger.error("Process aborted (took too long)")
            try:
                kill(p1.pid, SIGKILL)
            except:
                pass
        ## CPU Throttle
        sleep(0.8)

    if p1.poll() == None:
        ## Safety
        try:
            kill(p1.pid, SIGKILL)
        except:
            pass
    ## Ensure execution leaves memory
    p1.wait()

    if p1.returncode not in (0, 93):
        # 93 is a return value recognized by NZBGet as 'good'
        # all systems okay; we want to translate this back to
        # standard shell scripting responses if we get anything
        # outside of what is identified above
        exit(1)
    exit(0)

#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Notifification wrapper for SABnzbd
#
# Copyright (C) 2014-2016 Chris Caron <lead2gold@gmail.com>
#
# This file adds support for SABnzbd v1.1.0 or higher
#
# NZB-Notify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NZB-Notify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NZB-Notify. If not, see <http://www.gnu.org/licenses/>.
import subprocess
import sys
import os

from os import getpid
from os import kill
from os.path import abspath
from os.path import dirname
from os.path import join

from time import sleep
from datetime import datetime
from datetime import timedelta

import logging
import logging.handlers

# Logging Support
logger = logging.getLogger("sabnzbd-notify - %s" % getpid())
logging.raiseExceptions = 0
logger.setLevel(logging.INFO)
h1 = logging.StreamHandler(sys.stdout)
h1.setFormatter(logging. \
    Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(h1)

# Path to notify script
NOTIFY_SCRIPT = join(abspath(dirname(__file__)), 'Notify.py')

# Just some timeout value
NOTIFY_MAX_WAIT_TIME_SEC = 300

# This will be what I'll need you users to toggle if you thing you've
# found a bug you need me to solve.  Send your logs to lead2gold@gmail.com
# or i'll really have no idea what's going on.
DEBUG_MODE = False

# A mapping of possible notifications to their respected image.  This
# is only referenced by notifications that support this feature.
SABNZBD_NOTIFICATION_MAP = {
    # Startup/Shutdown
    'startup': (
        'Startup/Shutdown',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # Added NZB
    'download': (
        'Added NZB',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # Post-processing started
    'pp': (
        'Post-Processing Started',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # Job finished
    'complete': (
        'Job Finished',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # Job failed
    'failed': (
        'Job Failed',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # Warning
    'warning': (
        'Warning',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # Error
    'error': (
        'Error',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # Disk full
    'disk_full': (
        'Disk Full',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # Queue finished
    'queue_done': (
        'Queue Finished',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # User logged in
    'new_login': (
        'User Logged In',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
    # Other Messages
    'other': (
        'Other Messages',
        'https://sabnzbd.org/images/icons/apple-touch-icon-76x76-precomposed.png',
    ),
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


def notify(ntype, title, body, urls, debug=None):
    """
    A callable function so SABnzbd can import this file and just
    call the notifications through here if they wish.
    """
    if debug is None:
        debug = DEBUG_MODE

    if sys.platform[0:3] == 'win':
        # Windows systems require the executable 'python'
        # up front
        cmd = [
            'python',
            NOTIFY_SCRIPT,
            '-t', title,
            '-b', body,
            '-u', SABNZBD_NOTIFICATION_MAP[ntype][1],
            '-s', urls,
        ]
    else:
        # Other systems determine the environment from
        # the executable's first line #!
        cmd = [
            NOTIFY_SCRIPT,
            '-t', title,
            '-b', body,
            '-u', SABNZBD_NOTIFICATION_MAP[ntype][1],
            '-s', urls,
        ]

    if debug:
        # Debug Mode Enabled
        cmd.append('-D')

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
        return False
    return True

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

    # Perform Notification
    exit(int(not notify(
        ntype=notify_type,
        title=notify_title,
        body=notify_body,
        urls=notify_urls,
    )))

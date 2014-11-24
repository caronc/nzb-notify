#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Notify post-processing script for NZBGet
#
# Copyright (C) 2014 Chris Caron <lead2gold@gmail.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with subliminal.  If not, see <http://www.gnu.org/licenses/>.
#

###########################################################################
### NZBGET POST-PROCESSING SCRIPT

# NZBGet Notifications.
#
# The script will send a Notification to the systems of choice identified
# with the status of a download.
#
# Info about this Notify NZB Script:
# Author: Chris Caron (lead2gold@gmail.com).
# Date: Sun, Nov 23th, 2014.
# License: GPLv3 (http://www.gnu.org/licenses/gpl.html).
# Script Version: 0.1.0.
#
# Growl implimentation is a wrapper for "netgrowl";
# a python library to search and download subtitles, written
# by Rui Carmo (http://the.taoofmac.com/space/projects/netgrowl).
#

###########################################################################
### OPTIONS

# Servers.
#
# Specify the server(s) you wish to notify. If there is more than
# one, simply use a comma and/or space to delimit the addresses. If the
# server uses a non-standard port, use colon (:PORT) at the end of
# the servers that this applies to. Some servers require a login and
# password to work correctly, the username can also be specified in the
# url as well. The following values are valid:
#  - service://user@host:port
#  - service://password@host:port
#  - service://user:password@host:port
#  - service://host:port
#  - service://host
#
# The following services are currently supported:
#  - growl:// -> A Growl Server
#  - xbmc:// -> An XBMC Server

# NOTE: If no port is specified, then the default port for the service
# identifed is always used instead.
# NOTE: If no user and/or password is specified, then it is assumed there isn't one.
# NOTE: Growl requires you to register the notifications your application
# sends (and set whether or not they're enabled on the GUI) before being able
# to actually send something to your Mac, so make sure you have "Allow
# application registration" enabled on Growl's preference pane. Additionally,
# you should make sure that you set a password.
#
# Specify the URL that identifies all of the servers you wish to notify.
#Servers=

# Send Notification on Failure (yes, no).
#
# Instruct the script to send a growl notification in the event the download
# failed.
#OnFailure=yes

# Send Notification on Success (yes, no).
#
# Instruct the script to send a growl notification in the event the download
# was successful.
#OnSuccess=yes

# Enable debugging mode (yes, no).
#
# Logging will be much more verbose, but if you are experiencing issues,
# developers and support staff will only be able to help you much easier
# if they have this extra bit of detail in your logging output.
#Debug=no

### NZBGET POST-PROCESSING SCRIPT
###########################################################################
import sys
from os.path import join
from os.path import dirname
sys.path.insert(0, join(dirname(__file__), 'Notify'))

from nzbget import SCRIPT_MODE
from nzbget import PostProcessScript

from NotifyGrowl import NotifyGrowl
from NotifyXBMC import NotifyXBMC

GROWL_APPLICATION = 'NZBGet'
GROWL_NOTIFICATION = 'Post-Process NZBGet Notification'
NOTIFY_GROWL_SCHEMA = 'growl'
NOTIFY_XBMC_SCHEMA = 'xbmc'
NOTIFY_XBMCS_SCHEMA = 'xbmcs'
SCHEMA_MAP = {
    # Growl Server
    NOTIFY_GROWL_SCHEMA: NotifyGrowl,
    # XBMC Server
    NOTIFY_XBMC_SCHEMA: NotifyXBMC,
    # Secure XBMC Server
    NOTIFY_XBMCS_SCHEMA: NotifyXBMC,
}

class NotifyScript(PostProcessScript):
    """Inheriting PostProcessScript grants you access to of the API defined
       throughout this wiki
    """
    def notify(self, servers, body, title):
        """
        processes list of servers specified
        """
        if isinstance(servers, basestring):
            # servers can be a list of URLs, or it can be
            # a string which will be parsed into this list
            # we wanted.
            servers = self.parse_list(self.get('Servers', ''))

        for _server in servers:
            server = self.parse_url(_server, default_schema='unknown')
            if not server:
                # Failed to parse te server
                self.logger.error('Could not parse URL: %s' % server)
                continue

            self.logger.vdebug('Server parsed to: %s' % str(server))

            # Some basic validation
            if server['schema'] not in SCHEMA_MAP:
                self.logger.error(
                    '%s is not a supported server type.' % server['schema'].upper(),
                )
                continue

            # #######################################################################
            # GROWL Server Support
            # #######################################################################
            if server['schema'] == NOTIFY_GROWL_SCHEMA:
                nobj = NotifyGrowl(
                    # Base
                    host=server['host'],
                    port=server['port'],
                    username=server['user'],
                    password=server['password'],

                    # Notify Specific
                    application_id=GROWL_APPLICATION,
                    notification_title=GROWL_NOTIFICATION,

                    # Logger Details
                    logger=self.logger,
                )

            # #######################################################################
            # XBMC Server Support
            # #######################################################################
            elif server['schema'] in \
                    (NOTIFY_XBMC_SCHEMA, NOTIFY_XBMCS_SCHEMA):

                # Secure Flag
                secure = (server['schema'] == NOTIFY_XBMCS_SCHEMA)

                nobj = NotifyXBMC(
                    # Base
                    host=server['host'],
                    port=server['port'],
                    username=server['user'],
                    password=server['password'],

                    # Notify Specific
                    secure=secure,

                    # Logger Details
                    logger=self.logger,
                )

            else:
                # General support
                nobj = SCHEMA_MAP[server['schema']](
                    # Base
                    host=server['host'],
                    port=server['port'],
                    password=server['password'],

                    # Logger Details
                    logger=self.logger,
                )

            if not nobj.notify(body=body, title=title):
                self.logger.error('Could not notify: %s' % server['url'])
                continue
            self.logger.debug('Notified %s successfully' % server['url'])


    def postprocess_main(self, *args, **kwargs):
        """Write all your code here
        """

        if not self.validate(keys=(
            'Servers',
            'OnFailure',
            'OnSuccess',
        )):
            return False

        servers = self.parse_list(self.get('Servers', ''))
        on_failure = self.parse_bool(self.get('OnFailure'))
        on_success = self.parse_bool(self.get('OnSuccess'))

        # Contents
        title = ''
        body = self.get('NZBFILE')

        if self.health_check():
            if not on_success:
                self.logger.debug('Success notifications supressed.')
                return None
            title = 'Download Successful'
        else:
            if not on_failure:
                self.logger.debug('Failure notifications supressed.')
                return None
            title = 'Download Failed'

        # Preform Notifications
        return self.notify(servers, title=title, body=body)

    def main(self, *args, **kwargs):
        """CLI
        """

        # Environment
        servers = self.get('Servers', None)
        title = self.get('Title', 'Test Notify Title')
        body = self.get('Body', 'Test Notify Body')

        if not servers:
            self.logger.debug('No servers were specified --servers (-s)')
            return False

        # Preform Notifications
        return self.notify(servers, title=title, body=body)

# Call your script as follows:
if __name__ == "__main__":
    from optparse import OptionParser

    # Support running from the command line
    parser = OptionParser()
    parser.add_option(
        "-s",
        "--servers",
        dest="servers",
        help="Specify 1 or more servers in their URL format ie: " + \
            "growl://mypass@localhost"
            "the command line.",
        metavar="URL(s)",
    )
    parser.add_option(
        "-t",
        "--title",
        dest="title",
        help="Specify the title of the notification message.",
        metavar="TITLE",
    )
    parser.add_option(
        "-b",
        "--body",
        dest="body",
        help="Specify the body of the notification message.",
        metavar="BODY",
    )
    parser.add_option(
        "-L",
        "--logfile",
        dest="logfile",
        help="Send output to the specified logfile instead of stdout.",
        metavar="FILE",
    )
    parser.add_option(
        "-D",
        "--debug",
        action="store_true",
        dest="debug",
        help="Debug Mode",
    )
    options, _args = parser.parse_args()

    logger = options.logfile
    if not logger:
        # True = stdout
        logger = True
    debug = options.debug

    script_mode = None
    _servers = options.servers
    _body = options.body
    _title = options.title
    if _servers:
        # By specifying a scandir, we know for sure the user is
        # running this as a standalone script,

        # Setting Script Mode to NONE forces main() to execute
        # which is where the code for the cli() is defined
        script_mode = SCRIPT_MODE.NONE

    # Initialize Script
    script = NotifyScript(
        logger=logger,
        debug=debug,
        script_mode=script_mode,
    )

    # Initialize entries if any were specified
    if _servers:
        script.set('Servers', _servers)

    if _title:
        script.set('Title', _title)

    if _body:
        script.set('Body', _body)

    # call run() and exit() using it's returned value
    exit(script.run())

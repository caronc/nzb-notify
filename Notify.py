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

###########################################################################
### OPTIONS

# Servers.
#
# Specify the server(s) you wish to notify. If there is more than
# one, simply use a comma and/or space to delimit the addresses. If the
# server uses a non-standard port, use colon (:PORT) at the end of
# the servers that this applies to. Some servers require a login and
# password to work correctly, the user can also be specified in the
# url as well. The following values are valid:
#  - service://user@host:port
#  - service://password@host:port
#  - service://user:password@host:port
#  - service://host:port
#  - service://host
#
# The following services are currently supported:
#  - growl:// -> A Growl Server
#  - prowl:// -> A Prowl Server
#  - xbmc:// -> An XBMC Server
#  - kodi:// -> An KODI Server (XBMC Server)
#  - pbul:// -> A PushBullet Notification
#  - pover:// -> A Pushover Notification
#  - json:// -> A simple json query
#  - jsons:// -> A simple secure json query

# NOTE: If no port is specified, then the default port for the service
# identifed is always used instead.
# NOTE: If no user and/or password is specified, then it is assumed there isn't one.
# NOTE: Growl requires you to register the notifications your application
# sends (and set whether or not they're enabled on the GUI) before being able
# to actually send something to your Mac, so make sure you have "Allow
# application registration" enabled on Growl's preference pane. Additionally,
# you should make sure that you set a password.
# NOTE: PushBullet requires a access token it uses to comuncate with the
# remote server.  This is specified inline with the service request like
# so:
#  - pbul://accesstoken
#
# NOTE: PushBullet can support emails, devices and channels, you can also
# do this by specifying them on the path; as an example (mix and match
# as you feel). If no path is specified, then it is assumed you want to
# notify all deies.:
#  - pbul://accesstoken/#channel/#channel2/device/email@email.com
#
# NOTE: Pushover notifications require a user and a token to work
# correctly. The following syntax will handle this for you:
# - pover://user@token
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
import re
from os.path import join
from os.path import dirname
from urllib import unquote
sys.path.insert(0, join(dirname(__file__), 'Notify'))

from nzbget import SCRIPT_MODE
from nzbget import PostProcessScript

from NotifyGrowl import NotifyGrowl
from NotifyJSON import NotifyJSON
from NotifyProwl import NotifyProwl
from NotifyToasty import NotifyToasty
from NotifyPushBullet import NotifyPushBullet
from NotifyPushover import NotifyPushover
from NotifyXBMC import NotifyXBMC

GROWL_APPLICATION = 'NZBGet'
GROWL_NOTIFICATION = 'Post-Process NZBGet Notification'
NOTIFY_GROWL_SCHEMA = 'growl'
NOTIFY_PROWL_SCHEMA = 'prowl'
NOTIFY_XBMC_SCHEMA = 'xbmc'
NOTIFY_KODI_SCHEMA = 'kodi'
NOTIFY_XBMCS_SCHEMA = 'xbmcs'
NOTIFY_KODIS_SCHEMA = 'kodis'
NOTIFY_TOASTY_SCHEMA = 'toasty'
NOTIFY_PUSHBULLET_SCHEMA = 'pbul'
NOTIFY_PUSHOVER_SCHEMA = 'pover'
NOTIFY_JSON_SCHEMA = 'json'
NOTIFY_JSONS_SCHEMA = 'jsons'

SCHEMA_MAP = {
    # KODI Server
    NOTIFY_KODI_SCHEMA: NotifyXBMC,
    # Secure KODI Server
    NOTIFY_KODIS_SCHEMA: NotifyXBMC,
    # Growl Server
    NOTIFY_GROWL_SCHEMA: NotifyGrowl,
    # Prowl Server
    NOTIFY_PROWL_SCHEMA: NotifyProwl,
    # Toasty Server
    NOTIFY_TOASTY_SCHEMA: NotifyToasty,
    # XBMC Server
    NOTIFY_XBMC_SCHEMA: NotifyXBMC,
    # Secure XBMC Server
    NOTIFY_XBMCS_SCHEMA: NotifyXBMC,
    # PushBullet Server
    NOTIFY_PUSHBULLET_SCHEMA: NotifyPushBullet,
    # Pushover Server
    NOTIFY_PUSHOVER_SCHEMA: NotifyPushover,
    # Simple JSON HTTP Server
    NOTIFY_JSON_SCHEMA: NotifyJSON,
    # Simple Secure JSON HTTP Server
    NOTIFY_JSONS_SCHEMA: NotifyJSON,
}

# Used to break a path list into parts
PATHSPLIT_LIST_DELIM = re.compile(r'[ \t\r\n,\\/]+')

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
                    # Notify Specific
                    application_id=GROWL_APPLICATION,
                    notification_title=GROWL_NOTIFICATION,

                    # Logger Details
                    logger=self.logger,

                    # Base
                    **server)

            # #######################################################################
            # PROWL Server Support
            # #######################################################################
            elif server['schema'] == NOTIFY_PROWL_SCHEMA:

                # optionally find the provider key
                try:
                    providerkey = filter(bool, PATHSPLIT_LIST_DELIM.split(
                        unquote(server['fullpath']),
                    ))[0]

                    if not providerkey:
                        providerkey = None

                except (AttributeError, IndexError):
                    providerkey = None


                nobj = NotifyProwl(
                    # Notify Specific
                    apikey=server['host'],
                    providerkey=providerkey,

                    # Logger Details
                    logger=self.logger,

                    # Base
                    **server)

            # #######################################################################
            # PushBullet Server Support
            # #######################################################################
            elif server['schema'] == NOTIFY_PUSHBULLET_SCHEMA:
                try:
                    recipients = unquote(server['fullpath'])
                except AttributeError:
                    recipients = ''

                nobj = NotifyPushBullet(
                    # Notify Specific
                    accesstoken=server['host'],
                    recipients=recipients,

                    # Logger Details
                    logger=self.logger,

                    # Base
                    **server)

            # #######################################################################
            # Pushover Server Support
            # #######################################################################
            elif server['schema'] == NOTIFY_PUSHOVER_SCHEMA:
                try:
                    devices = unquote(server['fullpath'])
                except AttributeError:
                    devices = ''

                nobj = NotifyPushover(
                    # Notify Specific
                    token=server['host'],
                    devices=devices,

                    # Logger Details
                    logger=self.logger,

                    # Base
                    **server)

            # #######################################################################
            # Toasty Server Support
            # #######################################################################
            elif server['schema'] == NOTIFY_TOASTY_SCHEMA:
                try:
                    devices = unquote(server['fullpath'])
                except AttributeError:
                    devices = ''

                nobj = NotifyToasty(
                    # Notify Specific
                    devices='%s/%s' % (server['host'], devices),

                    # Logger Details
                    logger=self.logger,

                    # Base
                    **server)

            # #######################################################################
            # GENERAL / COMMON Server Support
            # #######################################################################
            else:
                secure = (server['schema'][-1] == 's')
                nobj = SCHEMA_MAP[server['schema']](
                    # General
                    secure=secure,

                    # Logger Details
                    logger=self.logger,

                    # Base
                    **server)

            nobj.notify(body=body, title=title)

        # Always return true
        return True


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
            "growl://mypass@localhost",
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

#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Notify post-processing script for NZBGet
#
# Copyright (C) 2014 Chris Caron <lead2gold@gmail.com>
#
# This file is part of NZBGet-Notify.
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

###########################################################################
### NZBGET QUEUE/POST-PROCESSING SCRIPT

# NZBGet Notifications.
#
# The script will send a Notification to the systems of choice identified
# with the status of a download.
#
# Info about this Notify NZB Script:
# Author: Chris Caron (lead2gold@gmail.com).
# Date: Tue, Dec 2nd, 2014.
# License: GPLv2 (http://www.gnu.org/licenses/gpl.html).
# Script Version: 0.1.2.
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
#
# The following services are currently supported:
#  - boxcar:// -> A Boxcar Notification
#  - boxcars:// -> A secure Boxcar Notification
#  - faast:// -> A Faast Notification
#  - growl:// -> A Growl Notification
#  - json:// -> A simple json query
#  - jsons:// -> A secure, simple json query
#  - kodi:// -> An KODI Notification
#  - nma:// -> Notify My Android Notification
#  - palot:// -> A Pushalot Notification
#  - pbul:// -> A PushBullet Notification
#  - prowl:// -> A Prowl Server
#  - pover:// -> A Pushover Notification
#  - toasty:// -> A (Super) Toasty Notification
#  - xbmc:// -> An XBMC Notification (protocol v2)
#  - xml:// -> A simple xml (SOAP) Notification
#  - xmls:// -> A secure, simple xml (SOAP) Notification
#
#
# NOTE: If no port is specified, then the default port for the service
# identifed is always used instead.
#
# NOTE: If no user and/or password is specified, then it is assumed there
# isn't one.
#
# NOTE: Boxcar requires an api key and host in order to use it. Boxcar can
# optionally support tags, aliases and device tokens which can be specified
# on the path:
#  - boxcars://host
#  - boxcars://user:host
#  - boxcars://user@pass:host
#  - boxcars://host/@tag
#  - boxcars://host/@tag1/@tag2/@tagN
#  - boxcars://host/devicetoken
#  - boxcars://host/devicetoken1/devicetoken2/devicetokenN
#  - boxcars://host/alias
#  - boxcars://host/alias1/alias2/alias1
#  - boxcars://host/alias/@tag/devicetoken
#
#
# NOTE: Faast Notifications require an authorization token:
#  - faast://authorizationtoken
#
#
# NOTE: Growl requires you to register the notifications your application
# sends (and set whether or not they're enabled on the GUI) before being able
# to actually send something to your Mac, so make sure you have "Allow
# application registration" enabled on Growl's preference pane. Additionally,
# you should make sure that you set a password.
#
# NOTE: Notify My Android requires an API Key it uses to comuncate with the
# remote server.  This is specified inline with the service request like so:
#  - nma://apikey
#
#
# NOTE: Pushalot requires an authorization token it uses to comuncate with the
# remote server.  This is specified inline with the service request like so:
#  - palot://authorizationtoken
#
#
# NOTE: PushBullet notifications require a access token, They can support
# emails, devices and channels, you can also do this by specifying them on the
# path; as an example (mix and match as you feel). If no path is specified,
# then it is assumed you want to notify all devices:
#  - pbul://accesstoken
#  - pbul://accesstoken/#channel
#  - pbul://accesstoken/device
#  - pbul://accesstoken/email@domain.net
#  - pbul://accesstoken/#channel/#channel2/device/email@email.com
#
#
# NOTE: Pushover notifications require a user and a token to work
# correctly. You can optionally specify devices associated with the
# account if you wish to target them specifically. Otherwise it is assumed
# you wish to notify all devices if none are specified:
#  - pover://user@token
#  - pover://user@token/device/
#  - pover://user@token/device1/device2/devicen
#
#
# NOTE: (Super) Toasty notifications requires at the very minimum at least
# one device to notify, you can additionally specify more then one too
# if you want:
#  - toasty://user@device
#  - toasty://user@device1/device2/deviceN
#Servers=

# Send Notification on Failure (yes, no).
#
# Instruct the script to send a notification in the event the download
# failed.
#OnFailure=yes

# Send Notification on Success (yes, no).
#
# Instruct the script to send a notification in the event the download
# was successful.
#OnSuccess=yes

# Create Notification on Queued Content (yes, no).
#
# Instruct the script to send a notification in the event an item is
# added to the download queue.
#OnQueue=yes

# Send a notification image when supported (yes, no).
#
# Instruct the script to include a supported image with the notification
# if the protocol supports it.
#IncludeImage=yes

# Enable debugging mode (yes, no).
#
# Logging will be much more verbose, but if you are experiencing issues,
# developers and support staff will only be able to help you much easier
# if they have this extra bit of detail in your logging output.
#Debug=no

### NZBGET QUEUE/POST-PROCESSING SCRIPT
###########################################################################
import sys
import re
from os.path import join
from os.path import dirname
from urllib import unquote
sys.path.insert(0, join(dirname(__file__), 'Notify'))

from nzbget import SCRIPT_MODE
from nzbget import PostProcessScript
from nzbget import QueueScript
from nzbget import QueueEvent

# Inherit Push Notification Scripts
from pnotify import *

NOTIFY_BOXCAR_SCHEMA = 'boxcar'
NOTIFY_BOXCARS_SCHEMA = 'boxcars'
NOTIFY_FAAST_SCHEMA = 'faast'
NOTIFY_GROWL_SCHEMA = 'growl'
NOTIFY_PROWL_SCHEMA = 'prowl'
NOTIFY_JSON_SCHEMA = 'json'
NOTIFY_JSONS_SCHEMA = 'jsons'
NOTIFY_KODI_SCHEMA = 'kodi'
NOTIFY_KODIS_SCHEMA = 'kodis'
NOTIFY_PUSHALOT_SCHEMA = 'palot'
NOTIFY_PUSHBULLET_SCHEMA = 'pbul'
NOTIFY_PUSHOVER_SCHEMA = 'pover'
NOTIFY_TOASTY_SCHEMA = 'toasty'
NOTIFY_NMA_SCHEMA = 'nma'
NOTIFY_XBMC_SCHEMA = 'xbmc'
NOTIFY_XBMCS_SCHEMA = 'xbmcs'
NOTIFY_XML_SCHEMA = 'xml'
NOTIFY_XMLS_SCHEMA = 'xmls'

SCHEMA_MAP = {
    # BOXCAR Notification
    NOTIFY_BOXCAR_SCHEMA: NotifyBoxcar,
    # Secure BOXCAR Notification
    NOTIFY_BOXCARS_SCHEMA: NotifyBoxcar,
    # FAAST Notification
    NOTIFY_FAAST_SCHEMA: NotifyFaast,
    # KODI Notification
    NOTIFY_KODI_SCHEMA: NotifyXBMC,
    # Secure KODI Notification
    NOTIFY_KODIS_SCHEMA: NotifyXBMC,
    # Growl Notification
    NOTIFY_GROWL_SCHEMA: NotifyGrowl,
    # Prowl Notification
    NOTIFY_PROWL_SCHEMA: NotifyProwl,
    # Toasty Notification
    NOTIFY_TOASTY_SCHEMA: NotifyToasty,
    # Notify My Android Notification
    NOTIFY_NMA_SCHEMA: NotifyMyAndroid,
    # XBMC Notification
    NOTIFY_XBMC_SCHEMA: NotifyXBMC,
    # Secure XBMC Notification
    NOTIFY_XBMCS_SCHEMA: NotifyXBMC,
    # Pushalot Notification
    NOTIFY_PUSHALOT_SCHEMA: NotifyPushalot,
    # PushBullet Notification
    NOTIFY_PUSHBULLET_SCHEMA: NotifyPushBullet,
    # Pushover Notification
    NOTIFY_PUSHOVER_SCHEMA: NotifyPushover,
    # Simple JSON HTTP Notification
    NOTIFY_JSON_SCHEMA: NotifyJSON,
    # Secure Simple JSON HTTP Notification
    NOTIFY_JSONS_SCHEMA: NotifyJSON,
    # Simple XML HTTP Notification
    NOTIFY_XML_SCHEMA: NotifyXML,
    # Secure Simple XML HTTP Notification
    NOTIFY_XMLS_SCHEMA: NotifyXML,
}

# Used to break a path list into parts
PATHSPLIT_LIST_DELIM = re.compile(r'[ \t\r\n,\\/]+')

class NotifyScript(PostProcessScript, QueueScript):
    """Inheriting PostProcessScript grants you access to of the API defined
       throughout this wiki
    """
    def notify(self, servers, body, title, notify_type):
        """
        processes list of servers specified
        """

        # Include Image Flag
        include_image = self.parse_bool(self.get('IncludeImage'), False)

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

            notify_args = server.copy().items() + {
                # Logger Details
                'logger': self.logger,
                # Base
                'include_image': include_image,
                'secure': (server['schema'][-1] == 's'),
            }.items()

            # #######################################################################
            # Boxcar Notification Support
            # #######################################################################
            if server['schema'] in (NOTIFY_BOXCAR_SCHEMA, NOTIFY_BOXCARS_SCHEMA):
                try:
                    recipients = unquote(server['fullpath'])
                except AttributeError:
                    recipients = ''

                notify_args = notify_args + {
                    'recipients': recipients,
                }.items()

            # #######################################################################
            # Faast Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_FAAST_SCHEMA:
                notify_args = notify_args + {
                    'authtoken': server['host'],
                }.items()

            # #######################################################################
            # GROWL Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_GROWL_SCHEMA:
                notify_args = notify_args + {
                }.items()

            # #######################################################################
            # Notify My Android Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_NMA_SCHEMA:

                notify_args = notify_args + {
                    'apikey': server['host'],
                }.items()

            # #######################################################################
            # PROWL Notification Support
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

                notify_args = notify_args + {
                    'apikey': server['host'],
                    'providerkey': providerkey,
                }.items()

            # #######################################################################
            # Pushalot Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_PUSHALOT_SCHEMA:
                notify_args = notify_args + {
                    'authtoken': server['host'],
                }.items()

            # #######################################################################
            # PushBullet Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_PUSHBULLET_SCHEMA:
                try:
                    recipients = unquote(server['fullpath'])
                except AttributeError:
                    recipients = ''

                notify_args = notify_args + {
                    'accesstoken': server['host'],
                    'recipients': recipients,
                }.items()

            # #######################################################################
            # Pushover Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_PUSHOVER_SCHEMA:
                try:
                    devices = unquote(server['fullpath'])
                except AttributeError:
                    devices = ''

                notify_args = notify_args + {
                    'token': server['host'],
                    'devices': devices,
                }.items()

            # #######################################################################
            # Toasty Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_TOASTY_SCHEMA:
                try:
                    devices = unquote(server['fullpath'])
                except AttributeError:
                    devices = ''

                notify_args = notify_args + {
                    'devices': '%s/%s' % (server['host'], devices),
                }.items()

            try:
                nobj = SCHEMA_MAP[server['schema']](**dict(notify_args))
            except TypeError:
                # Validation Failure
                continue


            nobj.notify(body=body, title=title, notify_type=notify_type)

        # Always return true
        return True

    def queue_main(self, *args, **kwargs):
        """Queue Script
        """

        if not self.validate(keys=(
            'Servers',
            'IncludeImage',
            'OnQueue',
        )):
            return False

        if self.event != QueueEvent.NZB_ADDED:
            return None

        servers = self.parse_list(self.get('Servers', ''))
        on_failure = self.parse_bool(self.get('OnFailure'))
        on_success = self.parse_bool(self.get('OnSuccess'))
        notify_type = NotifyType.INFO

        if self.health_check():
            if not on_success:
                self.logger.debug('Success notifications supressed.')
                return None
            title = 'Queued Successfully'
        else:
            if not on_failure:
                self.logger.debug('Failure notifications supressed.')
                return None
            title = 'Queue Failed'

        return self.notify(
            servers,
            title=title,
            body=self.nzbname,
            notify_type=notify_type,
        )

    def postprocess_main(self, *args, **kwargs):
        """Post Processing Script
        """

        if not self.validate(keys=(
            'Servers',
            'IncludeImage',
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
            notify_type = NotifyType.SUCCESS
            title = 'Download Successful'
        else:
            if not on_failure:
                self.logger.debug('Failure notifications supressed.')
                return None
            notify_type = NotifyType.FAILURE
            title = 'Download Failed'

        # Preform Notifications
        return self.notify(
            servers,
            title=title,
            body=body,
            notify_type=notify_type,
        )

    def main(self, *args, **kwargs):
        """CLI
        """

        # Environment
        servers = self.get('Servers', None)
        title = self.get('Title', 'Test Notify Title')
        body = self.get('Body', 'Test Notify Body')
        notify_type = NotifyType.INFO

        if not servers:
            self.logger.debug('No servers were specified --servers (-s)')
            return False

        # Preform Notifications
        return self.notify(
            servers,
            title=title,
            body=body,
            notify_type=notify_type,
        )

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
        "-i",
        "--include_image",
        action="store_true",
        dest="include_image",
        help="Include image in message if the protocol supports it.",
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
    _include_image = options.include_image

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

    if _include_image:
        script.set('IncludeImage', _include_image)

    # call run() and exit() using it's returned value
    exit(script.run())

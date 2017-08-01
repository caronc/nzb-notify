#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Notififications Core
#
# Copyright (C) 2014-2017 Chris Caron <lead2gold@gmail.com>
#
# This file is part of NZB-Notify.
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

###########################################################################
### NZBGET QUEUE/POST-PROCESSING SCRIPT
### QUEUE EVENTS: NZB_ADDED

# NZBGet Notifications.
#
# The script will send a Notification to the systems of choice identified
# with the status of a download.
#
# Info about this Notify NZB Script:
# Author: Chris Caron (lead2gold@gmail.com).
# Date: Wed, Jul 7th, 2017.
# License: GPLv2 (http://www.gnu.org/licenses/gpl.html).
# Script Version: 0.6.1
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
#  - kodi:// -> A KODI Notification
#  - mailto:// -> An email Notification
#  - mailtos:// -> A secure email Notification
#  - nma:// -> Notify My Android Notification
#  - palot:// -> A Pushalot Notification
#  - pbul:// -> A PushBullet Notification
#  - prowl:// -> A Prowl Server
#  - pover:// -> A Pushover Notification
#  - toasty:// -> A (Super) Toasty Notification
#  - xbmc:// -> An XBMC Notification (protocol v2)
#  - slack:// -> An Slack Notification
#  - tgram:// -> An Telegram Notification
#  - xml:// -> A simple xml (SOAP) Notification
#  - xmls:// -> A secure, simple xml (SOAP) Notification
#  - mmost:// -> A (Unsecure) MatterMost Notification
#  - mmosts:// -> A Secure MatterMost Notification
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
# NOTE: Growl requires this script to register the notifications it
# sends before being able to actually send something.
# Make sure you are configured to allow application registration. The
# syntax looks as follows:
#  - growl://growlserver
#  - growl://password@growlserver
#
# Growl assumes you're using the v2 (or greater) protocol; if
# you need to use the version 1.4 protocol (for an older system)
# you can specify that switch as part of your url:
#  - growl://password@growlserver?version=1
#
#
# NOTE: Email notifications support a lot of options.
#
# The following would try to send an email to user@example.com
# and would attempt to detect the smtp server.
#  - mailtos://user@pass:port/example.com
#
# Emails are sent using html by default; but if you don't like this, you can turn it
# off like this:
#  - mailtos://user:pass@address.com?format=text
#
# There are many other options you can over-ride with an email too
#  - mailtos://user:pass@domain.com?smtp=mail.serverhost.com
#  - mailtos://user:pass@domain.com?smtp=example.com&from=from@address2.com&name=FooBar
#
# Some mail services are pretty mainstream (such as gmail.com, hotmail.com,
# etc). Specifying one of these hosts for the domain will result in the
# proper port, security, and SMTP mail server configuration automatically.
#
#
# NOTE: MattterMost notifications require you to generate a WebHook Key.
# By default it will use port 8065 unless otherwise specified.
#
# Once you've got this information; here is the structure of the message:
#  - mmost://domain.com/WebHookKey
#  - mmost://domain.com:8065/WebHookKey
#
# You can send a notification to a channel with the following:
#  - mmost://domain.com/WebHookKey?channel=test
#
# Or as a user:
#  - mmost://user@domain.com/WebHookKey
#
# If you're running an https setup, then just use mmosts://
#  - mmosts://domain.com/WebHookKey
#  - mmosts://domain.com:8065/WebHookKey
#  - mmosts://domain.com/WebHookKey?channel=test
#  - mmosts://user@domain.com/WebHookKey
#
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
# NOTE: Slack notifications require an incoming-webhook it can connect to.
# To use this plugin, you'll need to first access https://api.slack.com.
# Specifically https://my.slack.com/services/new/incoming-webhook/
# to create a new incoming-webhook for your account. You'll need to
# follow the wizard to pre-determine the channel(s) you want your
# message to broadcast to, and when you're complete, you will
# recieve a URL that looks something like this:
#  * https://hooks.slack.com/services/T1JJ3T3L2/A1BRTD4JD/TIiajkdnlazkcOXrIdevi7F
#
# You need to focus on the 3 Tokens at the end of the URL
#  * https://hooks.slack.com/services/TokenA/TokenB/TokenC
#
# Once you have a webhook (and you're tokens), here is how to use this part
# of the notification:
#  - slack://TokenA/TokenB/TokenC/#Channel
#  - slack://TokenA/TokenB/TokenC/#Channel1/#Channel2/#ChannelN
#  - slack://botname@TokenA/TokenB/TokenC/#Channel
#  - slack://botname@TokenA/TokenB/TokenC/#Channel1/#Channel2/#ChannelN
#
#
# NOTE: Telgram notifications work through a bot.
# You'll need to set one up an get the bot_token and at least
# one chat_id of where the bot you created is assigned to.
#
# Once you've got this information; here is the structure of the message:
#  - tgram://BotToken/ChatID
#  - tgram://BotToken/ChatID1/ChatID2/ChatIDN
#
# This works too if you want to place your ChatID in the user spot:
#  - tgram://ChatID@BotToken
#  - tgram://ChatID1@BotToken/ChatID2/ChatIDN
#
#
# NOTE: Join notifications pretty much work out of the box. Just visit
#       https://play.google.com/store/apps/details?id=com.joaomgcd.join and
#       download the app. Then visit https://joinjoaomgcd.appspot.com/ to
#       sign in (make sure you aren't blocking pop-ups) and acquire your
#       APIKey and DeviceID.  You'll need this to make up the Notify URL
#
# The URL looks something like this:
#  - join://APIKey/DeviceID
#  - join://APIKey/DeviceID1/DeviceID2/DeviceIDN
#  - join://APIKey/group.all
#  - join://APIKey/group.chrome/group.tablet/group.android
#  - join://APIKey/chrome/tablet/android
#  - join://APIKey/chrome/DeviceID1/tablet/DeviceID2/android
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
# NOTE: Prowl notifications require an api key to work correctly.
# you can optionally specify a provider key if you have one too.
#  - prowl://apikey
#  - prowl://apikey/providerkey
#
#
# NOTE: (Super) Toasty notifications requires at the very minimum at least
# one device to notify, you can additionally specify more then one too
# if you want:
#  - toasty://user@device
#  - toasty://user@device1/device2/deviceN
#Servers=

# Send Notification when Queued (yes, no).
#
# Send a notification when a new entry is queued into NZBGet for
# download.
#OnQueue=yes

# Send Notification on Failure (yes, no).
#
# Send a notification if the download failed.
#OnFailure=yes

# Send Notification on Success (yes, no).
#
# Send a notification if the download was successful.
#OnSuccess=yes

# Include Statistics (yes, no).
#
# Include statistics (if possible) in notification(s)
#IncludeStats=yes

# Include Files (yes, no).
#
# Include a file listing (if possible) of content retrieved.
# Note: File listings are excempted if the download failed.
#IncludeFiles=yes

# Include Logs (yes, no, OnFailure).
#
# Include the log entries in the notification
#IncludeLogs=OnFailure

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

# You can test your server configuration here.
#TestServers@Test Server Configuration

### NZBGET QUEUE/POST-PROCESSING SCRIPT
###########################################################################
import sys
import re
from os.path import join
from os.path import abspath
from os.path import dirname
from urllib import unquote

sys.path.insert(0, join(dirname(abspath(__file__)), 'Notify'))

from nzbget import SCRIPT_MODE
from nzbget import PostProcessScript
from nzbget import QueueScript
from nzbget import QueueEvent

# Inherit Push Notification Scripts
from pnotify import *
from pnotify.NotifyBase import IS_EMAIL_RE

NOTIFY_BOXCAR_SCHEMA = 'boxcar'
NOTIFY_BOXCARS_SCHEMA = 'boxcars'
NOTIFY_FAAST_SCHEMA = 'faast'
NOTIFY_GROWL_SCHEMA = 'growl'
NOTIFY_PROWL_SCHEMA = 'prowl'
NOTIFY_JSON_SCHEMA = 'json'
NOTIFY_JSONS_SCHEMA = 'jsons'
NOTIFY_KODI_SCHEMA = 'kodi'
NOTIFY_KODIS_SCHEMA = 'kodis'
NOTIFY_MATTERMOST_SCHEMA = 'mmost'
NOTIFY_MATTERMOSTS_SCHEMA = 'mmosts'
NOTIFY_PUSHALOT_SCHEMA = 'palot'
NOTIFY_PUSHBULLET_SCHEMA = 'pbul'
NOTIFY_PUSHOVER_SCHEMA = 'pover'
NOTIFY_TOASTY_SCHEMA = 'toasty'
NOTIFY_EMAIL_SCHEMA = 'mailto'
NOTIFY_EMAILS_SCHEMA = 'mailtos'
NOTIFY_NMA_SCHEMA = 'nma'
NOTIFY_XBMC_SCHEMA = 'xbmc'
NOTIFY_XBMCS_SCHEMA = 'xbmcs'
NOTIFY_XML_SCHEMA = 'xml'
NOTIFY_XMLS_SCHEMA = 'xmls'
NOTIFY_SLACK_SCHEMA = 'slack'
NOTIFY_JOIN_SCHEMA = 'join'
NOTIFY_TELEGRAM_SCHEMA = 'tgram'
NOTIFY_PUSHJET_SCHEMA = 'pjet'
NOTIFY_PUSHJETS_SCHEMA = 'pjets'

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
    # MatterMost (Unsecure) Notification
    NOTIFY_MATTERMOST_SCHEMA: NotifyMatterMost,
    # MatterMost (Secure) Notification
    NOTIFY_MATTERMOSTS_SCHEMA: NotifyMatterMost,
    # Growl Notification
    NOTIFY_GROWL_SCHEMA: NotifyGrowl,
    # Prowl Notification
    NOTIFY_PROWL_SCHEMA: NotifyProwl,
    # Toasty Notification
    NOTIFY_TOASTY_SCHEMA: NotifyToasty,
    # Email Notification
    NOTIFY_EMAIL_SCHEMA: NotifyEmail,
    # Secure Email Notification
    NOTIFY_EMAILS_SCHEMA: NotifyEmail,
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
    # Slack Notification
    NOTIFY_SLACK_SCHEMA: NotifySlack,
    # Join Notification
    NOTIFY_JOIN_SCHEMA: NotifyJoin,
    # Telegram Notification
    NOTIFY_TELEGRAM_SCHEMA: NotifyTelegram,
    # Pushjet Notification
    NOTIFY_PUSHJET_SCHEMA: NotifyPushjet,
    # Pushjet Notification (secure)
    NOTIFY_PUSHJETS_SCHEMA: NotifyPushjet,
}

class IncludeLogOption(object):
    YES = 'YES'
    NO = 'NO'
    ONFAILURE = 'ONFAILURE'

INCLUDE_LOG_OPTIONS = (
    IncludeLogOption.YES,
    IncludeLogOption.NO,
    IncludeLogOption.ONFAILURE,
)

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
        _url = self.parse_url(self.get('IncludeImage'))

        # Define some globals to use in this function
        image_path = None
        image_url = None

        if _url:
            # Toggle our include image flag right away to True
            include_image = True

            # Get some more details
            if not re.match('^(https?|file)$', _url['schema'] ,re.IGNORECASE):
                self.logger.error(
                    'An invalid image url protocol (%s://) was specified.' % \
                     _url['schema'],
                )
                return False

            if _url['schema'] == 'file':
                if not isile(_url['fullpath']):
                    self.logger.error(
                        'The specified file %s was not found.' % \
                        _url['fullpath'],
                    )
                    return False
                image_path = _url['fullpath']

            else:
                # We're dealing with a web request
                image_url = _url['url']

        else:
            # Dealing with the old way of doing things; just toggling a true/false
            # flag
            include_image = self.parse_bool(self.get('IncludeImage'), False)

        if isinstance(servers, basestring):
            # servers can be a list of URLs, or it can be
            # a string which will be parsed into this list
            # we wanted.
            servers = self.parse_list(self.get('Servers', ''))

        for _server in servers:

            # swap hash (#) tag values with their html version
            # This is useful for accepting channels (as arguments to pushbullet)
            _server = _server.replace('/#', '/%23')

            server = self.parse_url(_server, default_schema='unknown')
            if not server:
                # This is a dirty hack; but it's the only work around to
                # tgram:// messages since the bot_token has a colon in it.
                # It invalidates an normal URL.

                # This hack searches for this bogus URL and corrects it
                # so we can properly load it further down. The other
                # alternative is to ask users to actually change the colon
                # into a slash (which will work too), but it's more likely
                # to cause confusion... So this is the next best thing
                tgram = re.match(
                    r'(?P<protocol>%s://)(bot)?(?P<prefix>([a-z0-9_-]+)(:[a-z0-9_-]+)?@)?(?P<btoken_a>[0-9]+):+(?P<remaining>.*)$' % \
                    NOTIFY_TELEGRAM_SCHEMA,
                    _server, re.IGNORECASE,
                )

                if tgram:
                    if tgram.group('prefix'):
                        server = self.parse_url('%s%s%s/%s' % (
                                tgram.group('protocol'),
                                tgram.group('prefix'),
                                tgram.group('btoken_a'),
                                tgram.group('remaining'),
                            ),
                            default_schema='unknown',
                        )
                    else:
                        server = self.parse_url('%s%s/%s' % (
                                tgram.group('protocol'),
                                tgram.group('btoken_a'),
                                tgram.group('remaining'),
                            ),
                            default_schema='unknown',
                        )
            if not server:
                # Failed to parse te server
                self.logger.error('Could not parse URL: %s' % server)
                continue

            self.logger.debug('Server parsed to: %s' % str(server))

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
                # Support SSL Certificate 'verify' keyword
                # Default to being enabled (True)
                'verify': self.parse_bool(server['qsd'].get('verify', True)),
                # Overrides
                'override_image_url': image_url,
                'override_image_path': image_path,
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
            # Email Notification Support
            # #######################################################################
            elif server['schema'] in (NOTIFY_EMAIL_SCHEMA, NOTIFY_EMAILS_SCHEMA):

                # Default Format is HTML
                notify_format = NotifyFormat.HTML

                to_addr = ''
                from_addr = ''
                smtp_host = ''
                if 'format' in server['qsd'] and len(server['qsd']['format']):
                    # Extract email format (Text/Html)
                    try:
                        format = unquote(server['qsd']['format']).lower()
                        if len(format) > 0 and format[0] == 't':
                            notify_format = NotifyFormat.TEXT
                    except AttributeError:
                        pass

                # get 'To' email address
                try:
                    to_addr = filter(bool, PATHSPLIT_LIST_DELIM.split(
                          unquote(server['host'].lstrip('/')),
                    ))[0]
                except (AttributeError, IndexError):
                    # No problem, we have other ways of getting
                    # the To address
                    pass

                if not IS_EMAIL_RE.match(to_addr):
                    if server['user']:
                        # Try to be clever and build a potential
                        # email address based on what we've been provided
                        to_addr = '%s@%s' % (
                            re.split('[\s@]+', server['user'])[0],
                            re.split('[\s@]+', to_addr)[-1],
                        )
                        if not IS_EMAIL_RE.match(to_addr):
                            self.logger.error(
                                '%s does not contain a recipient email.' % \
                                unquote(server['url'].lstrip('/')),
                            )
                            continue

                # Attempt to detect 'from' email address
                from_addr = to_addr
                try:
                    if 'from' in server['qsd'] and len(server['qsd']['from']):
                        from_addr = server['qsd']['from']
                        if not IS_EMAIL_RE.match(server['qsd']['from']):
                            # Lets be clever and attempt to make the from
                            # address email
                            from_addr = '%s@%s' % (
                            re.split('[\s@]+', from_addr)[0],
                            re.split('[\s@]+', to_addr)[-1],
                        )
                        if not IS_EMAIL_RE.match(from_addr):
                            self.logger.error(
                                '%s does not contain a from address.' % \
                                unquote(server['url'].lstrip('/')),
                            )
                            continue

                except AttributeError:
                    pass

                try:
                    if 'name' in server['qsd'] and len(server['qsd']['name']):
                        # Extract from name to assocaite with from address
                        notify_args = notify_args + {
                            'name': unquote(server['qsd']['name']),
                        }.items()
                except AttributeError:
                    pass

                try:
                    if 'timeout' in server['qsd'] and len(server['qsd']['timeout']):
                        # Extract the timeout to assocaite with smtp server
                        notify_args = notify_args + {
                            'timeout': unquote(server['qsd']['timeout']),
                        }.items()
                except AttributeError:
                    pass

                try:
                    if 'user' in server['qsd'] and len(server['qsd']['user']):
                        # Extract from username to assocaite with smtp server
                        notify_args = notify_args + {
                            'user': unquote(server['qsd']['user']),
                        }.items()
                except AttributeError:
                    pass

                try:
                    if 'pass' in server['qsd'] and len(server['qsd']['pass']):
                        # Extract from password to assocaite with smtp server
                        notify_args = notify_args + {
                            'password': unquote(server['qsd']['pass']),
                        }.items()
                except AttributeError:
                    pass

                # Store SMTP Host if specified
                try:
                    # Extract from password to assocaite with smtp server
                    if 'smtp' in server['qsd'] and len(server['qsd']['smtp']):
                        smtp_host = unquote(server['qsd']['smtp'])
                except AttributeError:
                    pass

                notify_args = notify_args + {
                    'to': to_addr,
                    'from': from_addr,
                    'smtp_host': smtp_host,
                    'notify_format': notify_format,
                }.items()

            # #######################################################################
            # Notify My Android Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_NMA_SCHEMA:

                notify_format = NotifyFormat.HTML

                if 'format' in server['qsd'] and len(server['qsd']['format']):
                    # Extract email format (Text/Html)
                    try:
                        format = unquote(server['qsd']['format']).lower()
                        if len(format) > 0 and format[0] == 't':
                            notify_format = NotifyFormat.TEXT
                    except AttributeError:
                        pass

                notify_args = notify_args + {
                    'apikey': server['host'],
                }.items()

            # #######################################################################
            # Join Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_JOIN_SCHEMA:

                # Limit results to just the first 2 line otherwise
                # there is just to much content to display
                body = re.split('[\r\n]+', body)
                body[0] = body[0].strip('#').strip()
                body = '\r\n'.join(body[0:2])

                try:
                    devices = ' '.join(
                        filter(bool, PATHSPLIT_LIST_DELIM.split(
                        unquote(server['fullpath']).lstrip('/'),
                    )))

                except (AttributeError, IndexError):
                    # Force some bad values that will get caught
                    # in parsing later
                    devices = None

                notify_args = notify_args + {
                    'apikey': server['host'],
                    'devices': devices,
                }.items()

            # #######################################################################
            # MatterMost Notification Support
            # #######################################################################
            elif server['schema'] in (
                NOTIFY_MATTERMOST_SCHEMA,
                NOTIFY_MATTERMOSTS_SCHEMA):

                try:
                    authtoken = filter(bool, PATHSPLIT_LIST_DELIM.split(
                        unquote(server['fullpath']).lstrip('/'),
                    ))[0]

                except (AttributeError, IndexError):
                    # Force some bad values that will get caught
                    # in parsing later
                    authtoken = None

                channel = None
                if 'channel' in server['qsd'] and len(server['qsd']['channel']):
                    # Allow the user to specify the channel to post to
                    try:
                        channel = unquote(server['qsd']['channel']).strip()

                    except (AttributeError, TypeError, ValueError):
                        self.logger.warning(
                            'An invalid MatterMost channel of "%s" ' % server['qsd']['channel'] +\
                            'was specified and will be ignored.'
                        )
                        pass

                notify_args = notify_args + {
                    'authtoken': authtoken,
                    'channel': channel,
                }.items()

            # #######################################################################
            # GROWL Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_GROWL_SCHEMA:

                version = None
                if 'version' in server['qsd'] and len(server['qsd']['version']):
                    # Allow the user to specify the version of the protocol to
                    # use
                    try:
                        version = int(unquote(server['qsd']['version']).strip().split('.')[0])
                    except (AttributeError, IndexError, TypeError, ValueError):
                        self.logger.warning(
                            'An invalid Growl version of "%s" ' % server['qsd']['version'] +\
                            'was specified and will be ignored.'
                        )
                        pass

                # Because of the URL formatting; the password is actually where
                # the username field is; for this reason, we just preform
                # this small hack to make it conform correctly; the following
                # strips out the existing password entry (if exists) so that it
                # can be swapped with the new one we specify
                notify_args = dict(notify_args)
                notify_args['user'] = None
                notify_args['password'] = server.get('user', None)
                if version:
                    notify_args['version'] = version
                notify_args = notify_args.items()

                # Limit results to just the first 2 line otherwise
                # there is just to much content to display
                body = re.split('[\r\n]+', body)
                body[0] = body[0].strip('#').strip()
                body = '\r\n'.join(body[0:2])

            # #######################################################################
            # Telegram Notification Support
            # Note: since the bot_token has a colon in it; it messes a bit with our
            #       url parsing.  Instead of being the hostname in this url, it
            #       becomes the host/port combination.
            # tgram://bot:token/chat_id1/chat_id2/chat_id3/?format=text
            # tgram://bot:token/chat_id1/chat_id2/chat_id3/
            # #######################################################################
            elif server['schema'] == NOTIFY_TELEGRAM_SCHEMA:

                # The first token is stored in the hostnamee
                bot_token_a = server['host']

                # Now fetch the remaining tokens
                try:
                    bot_token_b = filter(bool, PATHSPLIT_LIST_DELIM.split(
                        unquote(server['fullpath']).lstrip('/'),
                    ))[0]

                    bot_token = '%s:%s' % (bot_token_a, bot_token_b)

                except (AttributeError, IndexError):
                    # Force a bad value that will get caught in parsing later
                    bot_token = None

                try:
                    chat_ids = ','.join(
                        filter(bool, PATHSPLIT_LIST_DELIM.split(
                        unquote(server['fullpath']).lstrip('/'),
                    ))[1:])

                except (AttributeError, IndexError):
                    # Force some bad values that will get caught
                    # in parsing later
                    chat_ids = None

                notify_args = notify_args + {
                    'bot_token': bot_token,
                    'chat_ids': chat_ids,
                }.items()

            # #######################################################################
            # Slack Notification Support
            # #######################################################################
            elif server['schema'] == NOTIFY_SLACK_SCHEMA:

                # The first token is stored in the hostnamee
                token_a = server['host']

                # Now fetch the remaining tokens
                try:
                    token_b, token_c = filter(bool, PATHSPLIT_LIST_DELIM.split(
                        unquote(server['fullpath']).lstrip('/'),
                    ))[0:2]

                except (AttributeError, IndexError):
                    # Force some bad values that will get caught
                    # in parsing later
                    token_b = None
                    token_c = None

                try:
                    channels = '#'.join(
                        filter(bool, PATHSPLIT_LIST_DELIM.split(
                        unquote(server['fullpath']).lstrip('/'),
                    ))[2:])

                except (AttributeError, IndexError):
                    # Force some bad values that will get caught
                    # in parsing later
                    channels = None

                notify_args = notify_args + {
                    'token_a': token_a,
                    'token_b': token_b,
                    'token_c': token_c,
                    'channels': channels,
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

            # #######################################################################
            # XBMC Notification Support
            # #######################################################################
            elif server['schema'] in (
                NOTIFY_XBMC_SCHEMA, NOTIFY_XBMCS_SCHEMA,
                NOTIFY_KODI_SCHEMA, NOTIFY_KODIS_SCHEMA,
                                   ):
                # Limit results to just the first 2 line otherwise
                # there is just to much content to display
                body = re.split('[\r\n]+', body)
                body[0] = body[0].strip('#').strip()
                body = '\r\n'.join(body[0:2])
            try:
                #self.logger.debug('Initializing %s with:\r\n%s' % (
                #    SCHEMA_MAP[server['schema']].__name__,
                #    '\r\n'.join([ '%s=\'%s\'' % (k, v) \
                #               for (k, v) in notify_args ]),
                #))
                nobj = SCHEMA_MAP[server['schema']](**dict(notify_args))
            except TypeError, e:
                # Validation Failure
                self.logger.error(
                    'Could not initialize %s instance.' % server['schema'],
                )
                self.logger.debug('Initialization Exception: %s' % str(e))
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

        on_queue = self.parse_bool(self.get('OnQueue'))
        if not on_queue:
            return None

        if self.event != QueueEvent.NZB_ADDED:
            return None

        servers = self.parse_list(self.get('Servers', ''))
        notify_type = NotifyType.INFO

        # Contents
        title = ''

        if self.health_check():
            title = 'New File Queued for Download'
        else:
            # Do nothing; there is nothing queued now
            return None

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
            'IncludeFiles',
            'IncludeStats',
            'IncludeLogs',
            'OnFailure',
            'OnSuccess',
        )):
            return False

        servers = self.parse_list(self.get('Servers', ''))
        on_failure = self.parse_bool(self.get('OnFailure'))
        on_success = self.parse_bool(self.get('OnSuccess'))

        include_stats = self.parse_bool(self.get('IncludeStats'))
        include_files = self.parse_bool(self.get('IncludeFiles'))
        include_logs = self.get('IncludeLogs', 'NO').upper()

        health_okay = self.health_check()

        if include_logs not in INCLUDE_LOG_OPTIONS:
            # Default to being off
            include_logs = IncludeLogOption.NO

        # Contents
        title = ''
        body = '## %s ##' % self.nzbname
        body += NOTIFY_NEWLINE + 'Status: %s' % str(self.status)

        if health_okay:
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

        def hhmmss(seconds):
            """
            takes an integer and returns hh:mm:ss
            """
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return "%02d:%02d:%02d" % (round(h), round(m), round(s))

        # Get Statistics
        if include_stats:
            stats = self.get_statistics()
            if stats:
                # Build Printable List From Statistics
                statistics_core = [
                    ' * Download Size: %.2f MB' % stats['download_size_mb'],
                    ' * Download Time: %s' % \
                            hhmmss(stats['download_time_sec']),
                    ' * Transfer Speed: %.2f %s ' % (
                            stats['download_avg'],
                            stats['download_avg_unit'],
                    ),
                ]

                statistics_par = [
                    ' * Analyse Time: %s' % \
                                    hhmmss(stats['par_prepare_time_sec']),
                    ' * Repair Time: %s' % \
                                    hhmmss(stats['par_repair_time_sec']),
                ]

                statistics_overall = [
                    ' * Total Archive Preparation Time: %s' % \
                            hhmmss(stats['par_total_time_sec']),
                    ' * Unarchiving Time: %s' % \
                            hhmmss(stats['unpack_time_sec']),
                    ' * Total Post-Process Time: %s' % \
                            hhmmss(stats['postprocess_time']),
                    ' * Total Time: %s' % \
                            hhmmss(stats['total_time_sec']),
                ]

                body += NOTIFY_NEWLINE + NOTIFY_NEWLINE + \
                        '### Statistics ###' + \
                    NOTIFY_NEWLINE + NOTIFY_NEWLINE.join(statistics_core) + \
                    NOTIFY_NEWLINE + NOTIFY_NEWLINE.join(statistics_par) + \
                    NOTIFY_NEWLINE + NOTIFY_NEWLINE.join(statistics_overall)

        # Retrieve File listings (if possible)
        files = self.get_files(
            followlinks=True, fullstats=True,
            min_depth=None, max_depth=None,
        )

        if include_files and health_okay:
            # Build printable file list from results
            files_downloaded = []
            for _file, meta in files.items():
                unit = 'B'
                val = float(meta['filesize'])
                if val >= 1024.0:
                    val = val/1024.0
                    unit = 'KB'
                if val >= 1024.0:
                    val = val/1024.0
                    unit = 'MB'
                if val >= 1024.0:
                    val = val/1024.0
                    unit = 'GB'
                if val >= 1024.0:
                    val = val/1024.0
                    unit = 'TB'

                files_downloaded.append(
                    ' * ' + _file[len(self.directory)+1:] + ' (%.2f %s)' % (
                        val, unit
                ))

            if files_downloaded:
                body += NOTIFY_NEWLINE + NOTIFY_NEWLINE + '### File(s) ###' + \
                    NOTIFY_NEWLINE + \
                        NOTIFY_NEWLINE.join(sorted(files_downloaded))

        if include_logs == IncludeLogOption.YES or \
           (include_logs == IncludeLogOption.ONFAILURE \
            and not health_okay):

            # Fetch logs
            logs = self.get_logs(25)
            if logs:
                body += NOTIFY_NEWLINE + NOTIFY_NEWLINE + '### Logs ###' + \
                    ('%s * ' % NOTIFY_NEWLINE) + ('%s * ' % NOTIFY_NEWLINE).join(logs)

        # Preform Notifications
        return self.notify(
            servers,
            title=title,
            body=body,
            notify_type=notify_type,
        )

    def action_testservers(self, *args, **kwargs):
        """
        Execute the TestServers Test Action
        """

        if not self.validate(keys=(
            'Servers',
            'IncludeImage',
            'IncludeFiles',
            'IncludeStats',
            'IncludeLogs',
            'OnFailure',
            'OnSuccess',
        )):
            return False

        servers = self.parse_list(self.get('Servers', ''))
        on_failure = self.parse_bool(self.get('OnFailure'))
        on_success = self.parse_bool(self.get('OnSuccess'))

        include_stats = self.parse_bool(self.get('IncludeStats'))
        include_files = self.parse_bool(self.get('IncludeFiles'))
        include_logs = self.get('IncludeLogs', 'NO').upper()

        # Prepare our Test Response
        notify_type = NotifyType.INFO
        title='NZBGet-Notify Configuration Test'
        body='## NZBGet-Notify Configuration Test ##\r\n'
        body += '- **OnFailure**: %s\r\n' % (
            'Yes' if on_failure else 'No')
        body += '- **OnSuccess**: %s\r\n' % (
            'Yes' if on_success else 'No')
        body += '- **Include Statistics**: %s\r\n' % (
            'Yes' if include_stats else 'No')
        body += '- **Include File Listings**: %s\r\n' % (
            'Yes' if include_files else 'No')
        body += '- **Include Log Details**: %s\r\n' % (
            'Yes' if include_logs else 'No')

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
        "-u",
        "--image_url",
        dest="image_url",
        help="Provide url to image; should be either http://, " + \
            "https://, or file://. This option implies that " + \
            "--include_image (-i) is set automatically.",
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
    _image_url = options.image_url

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
    if not script.get('Servers') and _servers:
        script.set('Servers', _servers)

    if not script.get('Title') and _title:
        script.set('Title', _title)

    if not script.get('Body') and _body:
        script.set('Body', _body)

    if not script.get('IncludeImage') and _include_image:
        script.set('IncludeImage', _include_image)

    if _image_url:
        # if the _image_url is set, then we want to use it.
        # but before we do; check that it is valid first
        _url = script.parse_url(_image_url)
        if _url is None:
            # An invalid URL was specified
            script.logger.error('An invalid image url was specified.')
            exit(1)

        # Store IncludeImage path
        script.set('IncludeImage', _image_url)


    if not script.script_mode and not script.get('Servers'):
        # Provide some CLI help when VideoPaths has been
        # detected as not being identified
        parser.print_help()
        exit(1)

    # call run() and exit() using it's returned value
    exit(script.run())

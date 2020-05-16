#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Notififications Core
#
# Copyright (C) 2014-2019 Chris Caron <lead2gold@gmail.com>
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
# Date: Fri, Jul 19th, 2019.
# License: GPLv2 (http://www.gnu.org/licenses/gpl.html).
# Script Version: 0.9.3.
#
# Home: https://github.com/caronc/nzb-notify
# Wiki: https://github.com/caronc/nzb-notify/wiki

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
#  - discord:// -> A Discord Notification
#  - d7sms:// -> A D7 Networks SMS Notification
#  - emby:// -> A Emby Notification
#  - faast:// -> A Faast Notification
#  - flock:// -> A Flock Notification
#  - gitter:// -> A Gitter Notification
#  - gnome:// -> A Gnome Notification
#  - growl:// -> A Growl Notification
#  - gotify:// -> A Gotify Notification
#  - ifttt:// -> A IFTTT (If This Than That) Notification
#  - join:// -> A Join Notification
#  - json:// -> A simple json query
#  - jsons:// -> A secure, simple json query
#  - kde:// -> A KDE Notification
#  - kodi:// -> A KODI Notification
#  - kodis:// -> A Secure KODI Notification
#  - mailgun:// -> An Mailgun Notification
#  - matrix:// -> A Matrix Notification
#  - matrixs:// -> A Secure Matrix Notification
#  - mailto:// -> An email Notification
#  - mailtos:// -> A secure email Notification
#  - mattermost:// -> A Mattermost Notification
#  - msteams:// -> A Microsoft Teams Notification
#  - nexmo:// -> A Nexmo Notification
#  - prowl:// -> A Prowl Server
#  - pbul:// -> A PushBullet Notification
#  - pover:// -> A Pushover Notification
#  - pjet:// -> A Pushjet Notification
#  - pushed:// -> A Pushed Notification
#  - rocket:// -> A Rocket.Chat Notification
#  - rockets:// -> A Secure Rocket.Chat Notification
#  - ryver:// -> A Ryver Notification
#  - slack:// -> A Slack Notification
#  - sns:// -> Amazon Web Service (AWS) - Simple Notificaation Service (SNS)
#  - tgram:// -> A Telegram Notification
#  - twilio:// -> A Twilio Notification
#  - twitter:// -> A Twitter Direct Message (DM) Notification
#  - twist:// -> A Twist Notification
#  - xml:// -> A simple xml (SOAP) Notification
#  - xmls:// -> A secure, simple xml (SOAP) Notification
#  - mmost:// -> A (Unsecure) MatterMost Notification
#  - mmosts:// -> A Secure MatterMost Notification
#  - xbmc:// -> An XBMC Notification (protocol v2)
#  - xmpp:// -> An XMPP Notification
#  - wxteams:// -> An Cisco Webex Teams Notification
#  - windows:// -> A Microsoft Windows Notification
#  - zulip:// -> An Zulip Chat Notification
#
# Note: For details on how to use each notification checkout this link:
# https://github.com/caronc/apprise/wiki
#
# Note: You may specify as many servers as you wish so long as they're
# separated by a comma and/or space.
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
import logging
import re
import six
from os.path import join
from os.path import dirname
from os.path import isfile

# pip install nzbget
from nzbget import SCRIPT_MODE
from nzbget import PostProcessScript
from nzbget import QueueScript
from nzbget import QueueEvent

# pip install apprise
from apprise import Apprise
from apprise import NotifyType
from apprise import NotifyFormat
from apprise import AppriseAsset

# Used for character detection
from chardet import detect as chardet_detect

# HTML New Line Delimiter
NOTIFY_NEWLINE = '\r\n'


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


def decode(str_data, encoding=None):
    """
    Returns the unicode string of the data passed in
    otherwise it throws a ValueError() exception. This function makes
    use of the chardet library

    If encoding == None then it is attempted to be detected by chardet
    If encoding is a string, then only that encoding is used
    """
    if six.PY3:
        # nothing to do for Python 3
        return str_data

    if isinstance(str_data, unicode):
        return str_data

    default_encoding = 'utf-8'
    if encoding is None:
        decoded = chardet_detect(str_data)
        if decoded:
            encoding = decoded.get('encoding', default_encoding)
        else:
            encoding = default_encoding

    try:
        str_data = str_data.decode(
            encoding,
            errors='ignore',
        )
        return str_data

    except UnicodeError:
        raise ValueError(
            '%s contains invalid characters' % (
                str_data,
        ))
    except KeyError:
        raise ValueError(
            '%s encoding could not be detected ' % (
                str_data,
        ))
    return None


class NotifyScript(PostProcessScript, QueueScript):
    """Inheriting PostProcessScript grants you access to of the API defined
       throughout this wiki
    """

    def notify(self, servers, body, title, notify_type=NotifyType.INFO,
               body_format=NotifyFormat.MARKDOWN):
        """
        processes list of servers specified
        """

        # Decode our data
        body = decode(body)
        title = decode(title)

        # Apprise Asset Object
        asset = AppriseAsset()
        asset.app_id = 'NZB-Notify'
        asset.app_desc = 'NZB Notification'
        asset.app_url = 'https://github.com/caronc/nzb-notify'

        asset.image_path_mask = join(
            dirname(__file__),
            'Notify', 'apprise-theme', '{THEME}',
            'apprise-{TYPE}-{XY}.png')

        # Image URL Mask
        asset.image_url_mask = \
            'https://raw.githubusercontent.com/caronc/nzb-notify/master/' \
            'Notify/apprise-theme/{THEME}/' \
            'apprise-{TYPE}-{XY}{EXTENSION}'

        # Application Logo
        asset.image_url_logo = \
            'https://raw.githubusercontent.com/caronc/nzb-notify/master/' \
            'Notify/apprise-theme/{THEME}/' \
            'apprise-logo.png'

        # Include Image Flag
        _url = self.parse_url(self.get('IncludeImage'))

        # Define some globals to use in this function
        image_path = None
        image_url = None

        if _url:
            # Toggle our include image flag right away to True
            include_image = True

            # Get some more details
            if not re.match('^(https?|file)$', _url['schema'], re.IGNORECASE):
                self.logger.error(
                    'An invalid image url protocol (%s://) was specified.' %
                    _url['schema'],
                )
                return False

            if _url['schema'] == 'file':
                if not isfile(_url['fullpath']):
                    self.logger.error(
                        'The specified file %s was not found.' %
                        _url['fullpath'],
                    )
                    return False
                image_path = _url['fullpath']

            else:
                # We're dealing with a web request
                image_url = _url['url']

        else:
            # Dealing with the old way of doing things; just toggling a
            # true/false flag
            include_image = self.parse_bool(self.get('IncludeImage'), False)

        if isinstance(servers, six.string_types):
            # servers can be a list of URLs, or it can be
            # a string which will be parsed into this list
            # we wanted.
            servers = self.parse_list(self.get('Servers', ''))

        # Create our apprise object
        a = Apprise(asset=asset)

        for server in servers:

            # Add our URL
            if not a.add(server):
                # Validation Failure
                self.logger.error(
                    'Could not initialize %s instance.' % server,
                )
                continue

        # Notify our servers
        a.notify(body=body, title=title, notify_type=notify_type,
                 body_format=body_format)

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
                    ('%s * ' % NOTIFY_NEWLINE) + \
                    ('%s * ' % NOTIFY_NEWLINE).join(logs)

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
        title = 'NZBGet-Notify Configuration Test'
        body = '## NZBGet-Notify Configuration Test ##\r\n'
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

        if not servers:
            self.logger.info('No servers were specified --servers (-s)')
            return False

        # Preform Notifications
        return self.notify(
            servers,
            title=title,
            body=body,
            body_format=NotifyFormat.TEXT,
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
        help="Specify 1 or more servers in their URL format ie: " +
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

    # Attach Apprise logging to output by connecting to its namespace
    logging.getLogger('apprise.plugins.NotifyBase').\
            addHandler(script.logger.handlers[0])
    logging.getLogger('apprise.plugins.NotifyBase').\
            setLevel(script.logger.getEffectiveLevel())

    # call run() and exit() using it's returned value
    exit(script.run())

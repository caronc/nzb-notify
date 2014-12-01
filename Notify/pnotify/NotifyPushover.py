# -*- encoding: utf-8 -*-
#
# Pushover Notify Wrapper
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

from urllib import quote
import requests
import re

from NotifyBase import NotifyBase
from NotifyBase import NotifyFormat
from NotifyBase import HTTP_ERROR_MAP

# Flag used as a placeholder to sending to all devices
PUSHOVER_SEND_TO_ALL = 'ALL_DEVICES'

# Pushover uses the http protocol with JSON requests
PUSHOVER_URL = 'https://api.pushover.net/1/messages.json'

# Used to validate API Key
VALIDATE_TOKEN = re.compile(r'[A-Za-z0-9]{30}')

# Used to detect a User and/or Group
VALIDATE_USERGROUP = re.compile(r'[A-Za-z0-9]{30}')

# Used to detect a User and/or Group
VALIDATE_DEVICE = re.compile(r'[A-Za-z0-9_]{1,25}')

# Priorities
class PushoverPriority(object):
    VERY_LOW = -2
    MODERATE = -1
    NORMAL = 0
    HIGH = 1
    EMERGENCY = 2

PUSHOVER_PRIORITIES = (
    PushoverPriority.VERY_LOW,
    PushoverPriority.MODERATE,
    PushoverPriority.NORMAL,
    PushoverPriority.HIGH,
    PushoverPriority.EMERGENCY,
)

# Used to break path apart into list of devices
DEVICE_LIST_DELIM = re.compile(r'[ \t\r\n,\\/]+')

# Used to detect a device
IS_DEVICE_RE = re.compile(r'[A-Za-z0-9_]{1,25}')

# Extend HTTP Error Messages
PUSHOVER_HTTP_ERROR_MAP = dict(HTTP_ERROR_MAP.items() + {
    401: 'Unauthorized - Invalid Token.',
}.items())

class NotifyPushover(NotifyBase):
    """
    A wrapper for Pushover Notifications
    """
    def __init__(self, token, devices=None,
                 priority=PushoverPriority.NORMAL,
                 **kwargs):
        """
        Initialize Pushover Object
        """
        super(NotifyPushover, self).__init__(
            title_maxlen=250, body_maxlen=512,
            notify_format=NotifyFormat.TEXT,
            **kwargs)

        if not VALIDATE_TOKEN.match(token.strip()):
            self.logger.warning(
                'They API Token specified (%s) is invalid.' % token,
            )
            raise TypeError(
                'They API Token specified (%s) is invalid.' % token,
            )

        # The token associated with the account
        self.token = token.strip()

        if isinstance(devices, basestring):
            self.devices = filter(bool, DEVICE_LIST_DELIM.split(
                devices,
            ))
        elif isinstance(devices, (tuple, list)):
            self.devices = devices
        else:
            self.devices = list()

        if len(self.devices) == 0:
            self.devices = (PUSHOVER_SEND_TO_ALL, )

        # The Priority of the message
        if priority not in PUSHOVER_PRIORITIES:
            self.priority = PushoverPriority.NORMAL
        else:
            self.priority = priority

        if not self.user:
            self.logger.warning('No user was specified.')
            raise TypeError('No user was specified.')

        if not self.token:
            self.logger.warning('No token was specified.')
            raise TypeError('No token was specified.')

        if not VALIDATE_USERGROUP.match(self.user):
            self.logger.warning(
                'The user/group specified (%s) is invalid.' % self.user,
            )
            raise TypeError(
                'The user/group specified (%s) is invalid.' % self.user,
            )

    def _notify(self, title, body, **kwargs):
        """
        Perform Pushover Notification
        """

        headers = {
            'User-Agent': self.app_id,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        auth = (self.token, '')

        # error tracking (used for function return)
        has_error = False

        # Create a copy of the devices list
        devices = list(self.devices)
        while len(devices):
            device = devices.pop(0)

            # prepare JSON Object
            payload = {
                'token': self.token,
                'user': self.user,
                'priority': str(self.priority),
                'title': quote(title),
                'message': quote(body),
            }

            if device != PUSHOVER_SEND_TO_ALL:
                if not VALIDATE_DEVICE.match(device):
                    self.logger.warning(
                        'The device specified (%s) is invalid.' % device,
                    )
                    has_error = True
                    continue

                payload['device'] = device

            self.logger.debug('Pushover POST URL: %s' % PUSHOVER_URL)
            try:
                r = requests.post(
                    PUSHOVER_URL,
                    data=payload,
                    headers=headers,
                    auth=auth,
                )
                if r.status_code != 200:
                    # We had a problem
                    try:
                        self.logger.warning(
                            'Failed to send Pushover:%s ' % device +\
                            'notification: %s (error=%s).' % (
                                PUSHOVER_HTTP_ERROR_MAP[r.status_code],
                                r.status_code,
                        ))

                    except IndexError:
                        self.logger.warning(
                            'Failed to send Pushover:%s ' % device +\
                            'notification (error=%s).' % (
                                r.status_code,
                        ))

                    #self.logger.debug('Response Details: %s' % r.raw.read())
                    # Return; we're done
                    has_error = True

            except requests.ConnectionError as e:
                self.logger.warning(
                    'A Connection error occured sending Pushover:%s ' % (
                        device) + 'notification.'
                )
                self.logger.debug('Socket Exception: %s' % str(e))
                has_error = True

            if len(devices):
                # Prevent thrashing requests
                self.throttle()

        return has_error

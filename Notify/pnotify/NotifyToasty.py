# -*- encoding: utf-8 -*-
#
# (Super) Toasty Notify Wrapper
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

# Toasty uses the http protocol with JSON requests
TOASTY_URL = 'http://api.supertoasty.com/notify/'

# Used to break apart list of potential devices by their delimiter
# into a usable list.
DEVICES_LIST_DELIM = re.compile(r'[ \t\r\n,\\/]+')

class NotifyToasty(NotifyBase):
    """
    A wrapper for Toasty Notifications
    """
    def __init__(self, devices, **kwargs):
        """
        Initialize Toasty Object
        """
        super(NotifyToasty, self).__init__(
            title_maxlen=250, body_maxlen=32768,
            notify_format=NotifyFormat.TEXT,
            **kwargs)

        if isinstance(devices, basestring):
            self.devices = filter(bool, DEVICES_LIST_DELIM.split(
                devices,
            ))
        elif isinstance(devices, (tuple, list)):
            self.devices = devices
        else:
            raise TypeError('You must specify at least 1 device.')

        if not self.user:
            raise TypeError('You must specify a username.')

    def _notify(self, title, body, **kwargs):
        """
        Perform Toasty Notification
        """

        headers = {
            'User-Agent': self.app_id,
            'Content-Type': 'multipart/form-data',
        }

        # error tracking (used for function return)
        has_error = False

        # Create a copy of the devices list
        devices = list(self.devices)
        while len(devices):
            device = devices.pop(0)

            # prepare JSON Object
            payload = {
                'sender': quote(self.user),
                'title': quote(title),
                'text': quote(body),
            }

            # URL to transmit content via
            url = '%s%s' % (TOASTY_URL, device)

            try:
                self.logger.debug('Toasty POST URL: %s' % url)
                r = requests.post(
                    url,
                    data='&'.join([ '%s=%s' % (k,v) \
                                   for (k,v) in payload.items() ]),
                    headers=headers,
                )
                if r.status_code != 200:
                    # We had a problem
                    try:
                        self.logger.warning(
                            'Failed to send Toasty:%s ' % device +\
                            'notification: %s (error=%s).' % (
                                HTTP_ERROR_MAP[r.status_code],
                                r.status_code,
                        ))

                    except IndexError:
                        self.logger.warning(
                            'Failed to send Toasty:%s ' % device +\
                            'notification (error=%s).' % (
                                r.status_code,
                        ))

                    #self.logger.debug('Response Details: %s' % r.raw.read())
                    # Return; we're done
                    has_error = True

            except requests.ConnectionError as e:
                self.logger.warning(
                    'A Connection error occured sending Toasty:%s ' % (
                        device) + 'notification.'
                )
                self.logger.debug('Socket Exception: %s' % str(e))
                has_error = True

            if len(devices):
                # Prevent thrashing requests
                self.throttle()

        return has_error

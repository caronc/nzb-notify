# -*- encoding: utf-8 -*-
#
# (Super) Toasty Notify Wrapper
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

from NotifyBase import NotifyBase

from urllib import quote
import requests
import re

# Toasty uses the http protocol with JSON requests
TOASTY_URL = 'http://api.supertoasty.com/notify/'

# Used to break apart list of potential devices by their delimiter
# into a usable list.
DEVICES_LIST_DELIM = re.compile(r'[ \t\r\n,\\/]+')

class NotifyToasty(NotifyBase):
    """
    A wrapper for Toasty Notifications
    """
    def __init__(self, devices, logger=True, **kwargs):
        super(NotifyToasty, self).__init__(logger=logger, **kwargs)

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

    def notify(self, title, body, **kwargs):
        """
        Perform Toasty Notification
        """

        headers = {
            'User-Agent': "NZBGet-Notify",
            'Content-Type': 'multipart/form-data',
        }

        for device in self.devices:
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
                    self.logger.error(
                        'Failed to send Toasty:%s ' % device + \
                        'notification (error=%s)' % (
                            r.status_code,
                    ))
                    self.logger.debug(
                        'Toasty Server returned error %s' % str(r.raw))
                else:
                    self.logger.info(
                        'Sent Toasty:%s notification successfully' % (
                            device,
                    ))

            except requests.ConnectionError as e:
                self.logger.error(
                    'A Connection error occured sending Toasty ' + \
                    'notification.'
                )
                self.logger.debug('Socket Exception: %s' % str(e))

        return True

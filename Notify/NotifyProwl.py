# -*- encoding: utf-8 -*-
#
# Prowl Notify Wrapper
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
from json import dumps as to_json

import requests

# Prowl uses the http protocol with JSON requests
PROWL_URL = 'https://api.prowlapp.com/publicapi/add'

# Priorities
class ProwlPriority(object):
    VERY_LOW = -2
    MODERATE = -1
    NORMAL = 0
    HIGH = 1
    EMERGENCY = 2

PROWL_PRIORITIES = (
    ProwlPriority.VERY_LOW,
    ProwlPriority.MODERATE,
    ProwlPriority.NORMAL,
    ProwlPriority.HIGH,
    ProwlPriority.EMERGENCY,
)

PROWL_ERROR_MAP = {
    400: 'Bad Request; Unsupported Parameters',
    401: 'Verification Failed',
    406: 'IP address has exceeded API limit',
    409: 'Request not aproved.',
    500: 'Internal server error.',
}

class NotifyProwl(NotifyBase):
    """
    A wrapper for Prowl Notifications
    """
    def __init__(self, apikey, providerkey=None,
                 priority=ProwlPriority.NORMAL,
                 logger=True, **kwargs):

        super(NotifyProwl, self).__init__(
            host='localhost', logger=logger, **kwargs)

        if priority not in PROWL_PRIORITIES:
            self.priority = ProwlPriority.NORMAL
        else:
            self.priority = priority

        self.apikey = apikey
        self.providerkey = providerkey

    def notify(self, title, body, **kwargs):
        """
        Perform Prowl Notification
        """

        headers = {
            'User-Agent': "NZBGet-Notify",
            'Content-Type': 'application/json',
        }
        auth = (self.apikey, '')

        # prepare JSON Object
        payload = {
            'apikey': self.apikey,
            'description': body,
            'application': 'NZBGet-Notify',
            'event': title,
            'priority': self.priority,
        }

        if self.providerkey:
            payload['providerkey'] = self.providerkey

        try:
            r = requests.post(
                PROWL_URL,
                data=to_json(payload),
                headers=headers,
                auth=auth,
            )
            if r.status_code != 200:
                try:
                    error_msg = PROWL_ERROR_MAP[r.status_code]
                except IndexError:
                    error_msg = 'Failed to send Prowl notification'

                self.logger.error('%s (error=%s)' % (
                        error_msg,
                        r.status_code,
                ))
                self.logger.debug(
                    'Prowl Server returned error %s' % str(r.raw))
            else:
                self.logger.info('Sent Prowl successfully')

        except requests.ConnectionError as e:
            self.logger.error(
                'Failed to send Prowl alert to'
            )
            self.logger.debug('Socket Exception: %s' % str(e))

        return True

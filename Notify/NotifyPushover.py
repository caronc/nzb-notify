# -*- encoding: utf-8 -*-
#
# Pushover Notify Wrapper
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
from NotifyBase import HTTP_ERROR_MAP
from json import dumps as to_json
import requests

# Pushover uses the http protocol with JSON requests
PUSHOVER_URL = 'https://api.pushover.net/1/messages.json'

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

class NotifyPushover(NotifyBase):
    """
    A wrapper for Pushover Notifications
    """
    def __init__(self, token, priority=PushoverPriority.NORMAL,
                 logger=True, **kwargs):
        super(NotifyPushover, self).__init__(logger=logger, **kwargs)

        # The token associated with the account
        self.token = token

        # The Priority of the message
        if priority not in PUSHOVER_PRIORITIES:
            self.priority = PushoverPriority.NORMAL
        else:
            self.priority = priority

        if not self.user:
            raise TypeError('No user was specified.')

        if not self.token:
            raise TypeError('No token was specified.')

    def notify(self, title, body, **kwargs):
        """
        Perform Pushover Notification
        """

        headers = {
            'User-Agent': "NZBGet-Notify",
            'Content-Type': 'application/json',
        }
        auth = (self.token, '')

        # prepare JSON Object
        payload = {
            'token': self.token,
            'user': self.user,
            'title': title,
            'message': body,
        }

        try:
            self.logger.debug('Pushover POST URL: %s' % PUSHOVER_URL)
            r = requests.post(
                PUSHOVER_URL,
                data=to_json(payload),
                headers=headers,
                auth=auth,
            )
            if r.status_code != 200:
                try:
                    error_msg = HTTP_ERROR_MAP[r.status_code]
                except IndexError:
                    error_msg = 'Failed to send Pushover notification'

                self.logger.error('%s (error=%s)' % (
                        error_msg,
                        r.status_code,
                ))
                self.logger.debug(
                    'Pushover Server returned error %s' % str(r.raw))
            else:
                self.logger.info('Sent Pushover notification successfully')

        except requests.ConnectionError as e:
            self.logger.error(
                'A Connection error occured sending Pushover ' + \
                'notification.'
            )
            self.logger.debug('Socket Exception: %s' % str(e))

        return True

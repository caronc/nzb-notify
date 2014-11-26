# -*- encoding: utf-8 -*-
#
# PushBullet Notify Wrapper
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
import re

# Flag used as a placeholder to sending to all devices
PUSHBULLET_SEND_TO_ALL = 'ALL_DEVICES'

# PushBullet uses the http protocol with JSON requests
PUSHBULLET_URL = 'https://api.pushbullet.com/api/pushes'

# Regular expression retrieved from:
# http://www.regular-expressions.info/email.html
IS_EMAIL_RE = re.compile(
    r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)" +\
    r"*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*" +\
    r"[a-z0-9])?",
    re.IGNORECASE,
)

# Used to break apart list of potential recipients by their delimiter
# into a usable list.
RECIPIENTS_LIST_DELIM = re.compile(r'[ \t\r\n,\\/]+')

class NotifyPushBullet(NotifyBase):
    """
    A wrapper for PushBullet Notifications
    """
    def __init__(self, accesstoken, recipients=None,
                 logger=True, **kwargs):

        super(NotifyPushBullet, self).__init__(
            host=accesstoken, logger=logger, **kwargs)

        self.accesstoken = accesstoken
        if isinstance(recipients, basestring):
            self.recipients = filter(bool, RECIPIENTS_LIST_DELIM.split(
                recipients,
            ))
        elif isinstance(recipients, (tuple, list)):
            self.recipients = recipients
        else:
            self.recipients = list()

        if len(self.recipients) == 0:
            self.recipients = (PUSHBULLET_SEND_TO_ALL, )

    def notify(self, title, body, **kwargs):
        """
        Perform PushBullet Notification
        """

        headers = {'content-type': 'application/json'}
        auth = (self.accesstoken, '')

        for recipient in self.recipients:
            # prepare JSON Object
            payload = {
                'type': 'note',
                'title': title,
                'body': body,
            }

            if recipient is PUSHBULLET_SEND_TO_ALL:
                # Send to all
                pass

            if IS_EMAIL_RE.match(recipient):
                payload['email'] = recipient
                self.logger.debug(
                    "Recipient '%s' is an email address" % \
                    recipient,
                )

            elif recipient[0] == '#':
                payload['channel_tag'] = recipient[1:]
                self.logger.debug(
                    "Recipient '%s' is a channel" % \
                    recipient,
                )

            else:
                payload['device_iden'] = recipient
                self.logger.debug(
                    "Recipient '%s' is a device" % \
                    recipient,
                )

            try:
                r = requests.post(
                    PUSHBULLET_URL,
                    data=to_json(payload),
                    headers=headers,
                    auth=auth,
                )
                if r.status_code != 200:
                    self.logger.error(
                        'Failed to send PushBullet:%s ' % recipient + \
                        'notification (error=%s)' % (
                            r.status_code,
                    ))
                    self.logger.debug(
                        'PushBullet Server returned error %s' % str(r.raw))
                else:
                    self.logger.info(
                        'Sent PushBullet:%s successfully' % recipient,
                    )

            except requests.ConnectionError as e:
                self.logger.error(
                    'Failed to send PushBullet alert to'
                )
                self.logger.debug('Socket Exception: %s' % str(e))

        return True

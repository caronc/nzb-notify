# -*- encoding: utf-8 -*-
#
# JSON Notify Wrapper
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

class NotifyJSON(NotifyBase):
    """
    A wrapper for JSON Notifications
    """
    def __init__(self, **kwargs):
        super(NotifyJSON, self).__init__(**kwargs)

        if self.secure:
            self.schema = 'https'
        else:
            self.schema = 'http'

        self.fullpath = kwargs.get('fullpath')
        if not isinstance(self.fullpath, basestring):
            self.fullpath = '/'

        return

    def notify(self, title, body, **kwargs):
        """
        Perform JSON Notification
        """

        # prepare JSON Object
        payload = {
            'title': title,
            'message': body,
        }

        headers = {
            'User-Agent': "NZBGet-Notify",
            'Content-Type': 'application/json',
        }

        auth = None
        if self.user:
            auth = (self.user, self.password)

        url = '%s://%s' % (self.schema, self.host)
        if isinstance(self.port, int):
            url += ':%d' % self.port

        url += self.fullpath

        try:
            self.logger.debug('JSON POST URL: %s' % url)
            r = requests.post(
                url,
                data=to_json(payload),
                headers=headers,
                auth=auth,
            )
            if r.status_code != 200:
                self.logger.error(
                    'JSON Server failed to acknowledge notification at ' + \
                    '%s (error=%s)' % (
                        self.host,
                        r.status_code,
                ))
                self.logger.debug(
                    'JSON Server returned error %s' % str(r.raw))
                return False

        except requests.ConnectionError as e:
            self.logger.error(
                'A Connection error occured sending JSON ' + \
                'notification to %s.' % (
                    self.host,
            ))
            self.logger.debug('Socket Exception: %s' % str(e))
            return False

        return True

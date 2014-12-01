# -*- encoding: utf-8 -*-
#
# XBMC Notify Wrapper
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

from json import dumps
import requests

from NotifyBase import NotifyBase
from NotifyBase import NotifyFormat
from NotifyBase import NotifyImageSize
from NotifyBase import HTTP_ERROR_MAP

# Image Support (128x128)
XBMC_IMAGE_XY = NotifyImageSize.XY_128

# XBMC uses the http protocol with JSON requests
XBMC_PORT = 8080

class NotifyXBMC(NotifyBase):
    """
    A wrapper for XBMC/KODI Notifications
    """
    def __init__(self, **kwargs):
        """
        Initialize XBMC/KODI Object
        """
        super(NotifyXBMC, self).__init__(
            title_maxlen=250, body_maxlen=32768,
            image_size=XBMC_IMAGE_XY,
            notify_format=NotifyFormat.TEXT,
            **kwargs)

        if self.secure:
            self.schema = 'https'
        else:
            self.schema = 'http'

        if not self.port:
            self.port = XBMC_PORT

        return

    def _payload_20(self, title, body, notify_type, **kwargs):
        """
        Builds payload for XBMC JSON v2.0

        Returns (headers, payload)
        """

        headers = {
            'User-Agent': self.app_id,
            'Content-Type': 'application/json'
        }

        # prepare JSON Object
        payload = {
            'jsonrpc': '2.0',
            'method': 'GUI.ShowNotification',
            'params': {
                'title': title,
                'message': body,
                # displaytime is defined in microseconds
                'displaytime': 12000,
            },
            'id': 1,
        }

        if self.include_image:
            image_url = self.image_url(
                notify_type,
            )
            if image_url:
                payload['image'] = image_url

        return (headers, dumps(payload))


    def _notify(self, title, body, notify_type, **kwargs):
        """
        Perform XBMC Notification
        """

        # XBMC v2.0
        (headers, payload) = self._payload_20(
            title, body, notify_type, **kwargs)

        # TODO: XBMC v6.0 Support

        auth = None
        if self.user:
            auth = (self.user, self.password)

        url = '%s://%s' % (self.schema, self.host)
        if isinstance(self.port, int):
            url += ':%d' % self.port

        url += '/jsonrpc'

        self.logger.debug('XBMC/KODI POST URL: %s' % url)
        try:
            r = requests.post(
                url,
                data=payload,
                headers=headers,
                auth=auth,
            )
            if r.status_code != 200:
                # We had a problem
                try:
                    self.logger.warning(
                        'Failed to send XBMC/KODI notification:' +\
                        '%s (error=%s).' % (
                            HTTP_ERROR_MAP[r.status_code],
                            r.status_code,
                    ))
                except KeyError:
                    self.logger.warning(
                        'Failed to send XBMC/KODI notification ' +\
                        '(error=%s).' % (
                            r.status_code,
                    ))

                # Return; we're done
                return False
            else:
                self.logger.info('Sent XBMC/KODI notification.')

        except requests.ConnectionError as e:
            self.logger.warning(
                'A Connection error occured sending XBMC/KODI ' + \
                'notification.'
            )
            self.logger.debug('Socket Exception: %s' % str(e))

            # Return; we're done
            return False

        return True

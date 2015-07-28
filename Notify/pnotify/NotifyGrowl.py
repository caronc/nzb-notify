# -*- encoding: utf-8 -*-
#
# Growl Notify Wrapper
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

from NotifyBase import NotifyBase
from NotifyBase import NotifyFormat
from NotifyBase import NotifyImageSize
from gntp.notifier import GrowlNotifier
from gntp.errors import NetworkError as GrowlNetworkError
from gntp.errors import AuthError as GrowlAuthenticationError

# Default Growl Port
GROWL_UDP_PORT = 23053

# Image Support (128x128)
GROWL_IMAGE_XY = NotifyImageSize.XY_128

# Priorities
class GrowlPriority(object):
    VERY_LOW = -2
    MODERATE = -1
    NORMAL = 0
    HIGH = 1
    EMERGENCY = 2

GROWL_PRIORITIES = (
   GrowlPriority.VERY_LOW,
   GrowlPriority.MODERATE,
   GrowlPriority.NORMAL,
   GrowlPriority.HIGH,
   GrowlPriority.EMERGENCY,
)

class NotifyGrowl(NotifyBase):
    """
    A wrapper to Growl Notifications

    """
    def __init__(self, priority=GrowlPriority.NORMAL, **kwargs):
        """
        Initialize Growl Object
        """
        super(NotifyGrowl, self).__init__(
            title_maxlen=250, body_maxlen=32768,
            image_size=GROWL_IMAGE_XY,
            notify_format=NotifyFormat.TEXT,
            **kwargs)

        # A Global flag that tracks registration
        self.is_registered = False

        if not self.port:
            self.port = GROWL_UDP_PORT

        # The Priority of the message
        if priority not in GROWL_PRIORITIES:
            self.priority = GrowlPriority.NORMAL
        else:
            self.priority = priority

        self.growl = GrowlNotifier(
            applicationName=self.app_id,
            notifications=["New Updates","New Messages"],
            defaultNotifications=["New Messages"],
            hostname=self.host,
            password=self.password,
            port=self.port,
        )

        try:
            self.growl.register()
            # Toggle our flag
            self.is_registered = True

        except GrowlNetworkError:
            self.logger.warning(
                'A network error occured sending Growl ' + \
                'notification to %s.' % (
                    self.host,
            ))
            return

        except GrowlAuthenticationError:
            self.logger.warning(
                'An authentication error occured sending Growl ' + \
                'notification to %s.' % (
                    self.host,
            ))
            return

        return

    def _notify(self, title, body, notify_type, **kwargs):
        """
        Perform Growl Notification
        """

        if not self.is_registered:
            # We can't do anything
            return None

        icon = None
        if self.include_image:
            icon = self.image_raw(notify_type)

        try:
            self.growl.notify(
                noteType="New Updates",
                title=title,
                description=body,
                icon=icon,
                sticky=False,
                priority=self.priority,
            )

        except GrowlNetworkError as e:
            # Since Growl servers listen for UDP broadcasts,
            # it's possible that you will never get to this part
            # of the code since there is no acknowledgement as to
            # whether it accepted what was sent to it or not.

            # however, if the host/server is unavailable, you will
            # get to this point of the code.
            self.logger.warning(
                'A Connection error occured sending Growl ' + \
                'notification to %s.' % (
                    self.host,
            ))
            self.logger.debug('Growl Exception: %s' % str(e))

            # Return; we're done
            return False

        return True

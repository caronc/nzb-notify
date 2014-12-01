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

from netgrowl.netgrowl import GrowlNotificationPacket
from netgrowl.netgrowl import GrowlRegistrationPacket
from netgrowl.netgrowl import GROWL_UDP_PORT
from NotifyBase import NotifyFormat

from socket import AF_INET
from socket import SOCK_DGRAM
from socket import socket
from socket import error as SocketError

class NotifyGrowl(NotifyBase):
    """
    A wrapper to Growl Notifications

    """
    def __init__(self, **kwargs):
        """
        Initialize Growl Object
        """
        super(NotifyGrowl, self).__init__(
            title_maxlen=250, body_maxlen=32768,
            notify_format=NotifyFormat.TEXT,
            **kwargs)

        if not self.port:
            self.port = GROWL_UDP_PORT

        # Initialize Growl Registration Packet
        self.reg_packet = GrowlRegistrationPacket(
            application=self.app_id,
            password=self.password,
        )
        return

    def _notify(self, title, body, **kwargs):
        """
        Perform Growl Notification
        """
        # Initialize Growl Notification Packet
        notify_packet = GrowlNotificationPacket(
            application=self.app_id,
            notification=self.app_desc,
            title=title,
            description=body,
        )

        # Socket Control
        addr = (self.host, self.port)
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            s.sendto(self.reg_packet.payload(), addr)
            s.sendto(notify_packet.payload(), addr)
            self.logger.info('Sent Growl notification to "%s".' % (
                self.host,
            ))

        except SocketError as e:
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
            self.logger.debug('Socket Exception: %s' % str(e))

            # Return; we're done
            return False

        finally:
            s.close()

        return True

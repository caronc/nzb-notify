# -*- encoding: utf-8 -*-
#
# Growl Notify Wrapper
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

from netgrowl.netgrowl import GrowlNotificationPacket
from netgrowl.netgrowl import GrowlRegistrationPacket
from netgrowl.netgrowl import GROWL_UDP_PORT

from socket import AF_INET
from socket import SOCK_DGRAM
from socket import socket
from socket import error as SocketError

class NotifyGrowl(NotifyBase):
    """
    A wrapper to Growl Notifications

    """
    def __init__(self, host, application_id, notification_title,
                 port=GROWL_UDP_PORT, password=None, logger=True,
                 **kwargs):

        super(NotifyGrowl, self).__init__(
            host=host, port=port, password=password,
            logger=logger, **kwargs)

        if not self.port:
            self.port = GROWL_UDP_PORT

        self.application_id = application_id
        self.notification_title = notification_title

        # Initialize Growl Registration Packet
        self.reg_packet = GrowlRegistrationPacket(
            application=self.application_id,
            password=self.password,
        )
        return

    def notify(self, title, body, **kwargs):
        """
        Perform Growl Notification
        """
        # Initialize Growl Notification Packet
        notify_packet = GrowlNotificationPacket(
            application=self.application_id,
            notification=self.notification_title,
            title=title,
            description=body,
        )

        # Socket Control
        addr = (self.host, self.port)
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            s.sendto(self.reg_packet.payload(), addr)
            s.sendto(notify_packet.payload(), addr)
            self.logger.debug('Sent Growl alert to %s:%d' % (
                self.host,
                self.port,
            ))

        except SocketError as e:
            # Since Growl servers listen for UDP broadcasts,
            # it's possible that you will never get to this part
            # of the code since there is no acknowledgement as to
            # whether it accepted what was sent to it or not.

            # however, if the host/server is unavailable, you will
            # get to this point of the code.
            self.logger.error(
                'Failed to send Growl alert to %s:%d' % (
                    self.host,
                    self.port,
                ))
            self.logger.debug('Socket Exception: %s' % str(e))
            return False

        finally:
            s.close()

        return True

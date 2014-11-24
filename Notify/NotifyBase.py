# -*- encoding: utf-8 -*-
#
# Base Notify Wrapper
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

# Use logging integration provided with pynzget to
# keep things simple
from logging import Logger
from nzbget.Logger import init_logger

class NotifyBase(object):
    """
    This is the base class for all notification services
    """

    def __init__(self, host, port=None, username=None, password=None,
                 logger=True, debug=False, **kwargs):
        """
        Initialize some general logging and common server arguments
        that will keep things consistent when working with the
        notifiers that will inherit this class
        """

        self.host = host
        self.port = None
        if port:
            try:
                self.port = port
            except (TypeError, ValueError):
                self.port = None

        self.username = username
        self.password = password

        # logger identifier
        self.logger_id = __name__
        self.logger = logger
        self.debug = debug

        if isinstance(self.logger, basestring):
            # Use Log File
            self.logger = init_logger(
                name=self.logger_id,
                logger=logger,
                debug=self.debug,
                nzbget_mode=False,
            )

        elif not isinstance(self.logger, Logger):
            # handle all other types
            if logger is None:
                # None means don't log anything
                self.logger = init_logger(
                    name=self.logger_id,
                    logger=None,
                    debug=self.debug,
                    nzbget_mode=True,
                )
            else:
                # Use STDOUT for now
                self.logger = init_logger(
                    name=self.logger_id,
                    logger=True,
                    debug=self.debug,
                    nzbget_mode=True,
                )
        else:
            self.logger_id = None

    def notify(self, title, body, **kwargs):
        """
        This should be over-rided by the class that
        inherits this one.
        """
        return True

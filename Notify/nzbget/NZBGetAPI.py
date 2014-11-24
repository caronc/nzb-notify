# -*- encoding: utf-8 -*-
#
# A simple wrapper to the api interface for NZBGet
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
"""
This class was intended to make writing NZBGet API easier to interact with.
"""

from base64 import standard_b64encode

try:
    # Python 2
    from xmlrpclib import ServerProxy
except ImportError:
    # Python 3
    from xmlrpc.client import ServerProxy

class NZBGetAPI(object):
    """Interacts with NZBGetAPI
    """
    def __init__(self, user, passwd, host="127.0.0.1", port=6789):
        """Initializes and controls interaction to nzbget through
        it's API.
        """
        self.user = user
        self.passwd = passwd
        self.host = host
        self.port = int(port)

        if self.host == "0.0.0.0":
            self.host = "127.0.0.1"

        self.xmlrpc_url = 'http://%s:%s@%s:%s/xmlrpc' % ( \
            self.user,
            self.passwd,
            self.host,
            self.port,
        )

    def add_nzb(self, filename):
        """Simply add's an NZB file to NZBGet
        """
        try:
            proxy = ServerProxy(self.xmlrpc_url)
        except:
            return False
        try:
            f = open(filename, "r")
        except:
            return False

        content = f.read()
        f.close()
        b64content = standard_b64encode(content)
        try:
            return proxy.append(filename, 'software', False, b64content)
        except:
            return False

# -*- encoding: utf-8 -*-
#
# Base Notify Wrapper
#
# Copyright (C) 2014-2016 Chris Caron <lead2gold@gmail.com>
#
# This file is part of NZB-Notify.
#
# NZB-Notify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NZB-Notify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NZB-Notify. If not, see <http://www.gnu.org/licenses/>.

from time import sleep
import re

import markdown

from logging import Logger
from Logger import init_logger

from os.path import join
from os.path import dirname
from os.path import abspath

# Define a general HTML Escaping
try:
    # use sax first because it's faster
    from xml.sax.saxutils import escape as sax_escape

    def _escape(text):
        """
        saxutil escape tool
        """
        return sax_escape(text, {"'": "&apos;", "\"": "&quot;"})

except ImportError:
    # if we can't, then fall back to cgi escape
    from cgi import escape as cgi_escape

    def _escape(text):
        """
        cgi escape tool
        """
        return cgi_escape(text, quote=True)


class NotifyType(object):
    INFO = 'info'
    SUCCESS = 'success'
    FAILURE = 'failure'
    WARNING = 'warning'

# Most Servers do not like more then 1 request per 5 seconds,
# so 5.5 gives us a safe play range...
NOTIFY_THROTTLE_SEC = 5.5

NOTIFY_TYPES = (
    NotifyType.INFO,
    NotifyType.SUCCESS,
    NotifyType.FAILURE,
    NotifyType.WARNING,
)

# A Simple Mapping of Colors; For every NOTIFY_TYPE identified,
# there should be a mapping to it's color here:
HTML_NOTIFY_MAP = {
    NotifyType.INFO: '#3AA3E3',
    NotifyType.SUCCESS: '#3AA337',
    NotifyType.FAILURE: '#A32037',
    NotifyType.WARNING: '#CACF29',
}


class NotifyImageSize(object):
    XY_72 = '72x72'
    XY_128 = '128x128'
    XY_256 = '256x256'

NOTIFY_IMAGE_SIZES = (
    NotifyImageSize.XY_72,
    NotifyImageSize.XY_128,
    NotifyImageSize.XY_256,
)

HTTP_ERROR_MAP = {
    400: 'Bad Request - Unsupported Parameters.',
    401: 'Verification Failed.',
    404: 'Unauthorized access.',
    404: 'Page not found.',
    405: 'Method not allowed.',
    500: 'Internal server error.',
    503: 'Servers are overloaded.',
}

# Application Identifier
NOTIFY_APPLICATION_ID = 'NZB-Notify'
NOTIFY_APPLICATION_DESC = 'Notify Plugin'

# Image Control
NOTIFY_IMAGE_URL = 'http://nzbget.lead2gold.org/notify/' +\
        'nzbget-notify-{TYPE}-{XY}.png'

NOTIFY_IMAGE_FILE = abspath(join(
    dirname(__file__),
    'var',
    'nzbget-notify-{TYPE}-{XY}.png',
))

# HTML New Line Delimiter
NOTIFY_NEWLINE = '\r\n'


class NotifyFormat(object):
    TEXT = 'text'
    HTML = 'html'

NOTIFY_FORMATS = (
    NotifyFormat.TEXT,
    NotifyFormat.HTML,
)

# Regular expression retrieved from:
# http://www.regular-expressions.info/email.html
IS_EMAIL_RE = re.compile(
    r"(?P<userid>[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)" +\
    r"*)@(?P<domain>(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*" +\
    r"[a-z0-9]))?",
    re.IGNORECASE,
)


class NotifyBase(object):
    """
    This is the base class for all notification services
    """

    def __init__(self, title_maxlen=100, body_maxlen=512,
                 notify_format=NotifyFormat.TEXT, image_size=None,
                 include_image=False,
                 override_image_path=None,
                 logger=True, secure=False, debug=False, **kwargs):
        """
        Initialize some general logging and common server arguments
        that will keep things consistent when working with the
        notifiers that will inherit this class
        """

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

        if notify_format.lower() not in NOTIFY_FORMATS:
            self.logger.error(
                'Invalid notification format %s' % notify_format,
            )
            raise TypeError(
                'Invalid notification format %s' % notify_format,
            )

        if image_size and image_size not in NOTIFY_IMAGE_SIZES:
            self.logger.error(
                'Invalid image size %s' % image_size,
            )
            raise TypeError(
                'Invalid image size %s' % image_size,
            )

        self.app_id = NOTIFY_APPLICATION_ID
        self.app_desc = NOTIFY_APPLICATION_DESC

        self.notify_format = notify_format.lower()
        self.title_maxlen = title_maxlen
        self.body_maxlen = body_maxlen
        self.image_size = image_size
        self.include_image = include_image
        self.secure = secure

        self.host = kwargs.get('host', '')
        self.port = kwargs.get('port')
        if self.port:
            try:
                self.port = int(self.port)
            except (TypeError, ValueError):
                self.port = None

        self.user = kwargs.get('user')
        self.password = kwargs.get('password')

        # Over-rides
        self.override_image_url = kwargs.get('override_image_url')
        self.override_image_path = kwargs.get('override_image_path')

    def throttle(self, throttle_time=NOTIFY_THROTTLE_SEC):
        """
        A common throttle control
        """
        self.logger.debug('Throttling...')
        sleep(throttle_time)
        return

    def image_url(self, notify_type):
        """
        Returns Image URL if possible
        """

        if self.override_image_url:
            # Over-ride
            return self.override_image_url

        if not self.image_size:
            return None

        if notify_type not in NOTIFY_TYPES:
            return None

        re_map = {
            '{TYPE}': notify_type,
            '{XY}': self.image_size,
        }

        # Iterate over above list and store content accordingly
        re_table = re.compile(
            r'(' + '|'.join(re_map.keys()) + r')',
            re.IGNORECASE,
        )

        return re_table.sub(lambda x: re_map[x.group()], NOTIFY_IMAGE_URL)

    def image_raw(self, notify_type):
        """
        Returns the raw image if it can
        """
        if not self.override_image_path:
            if not self.image_size:
                return None

            if notify_type not in NOTIFY_TYPES:
                return None

            re_map = {
                '{TYPE}': notify_type,
                '{XY}': self.image_size,
            }

            # Iterate over above list and store content accordingly
            re_table = re.compile(
                r'(' + '|'.join(re_map.keys()) + r')',
                re.IGNORECASE,
            )

            # Now we open and return the file
            _file = re_table.sub(lambda x: re_map[x.group()], NOTIFY_IMAGE_FILE)

        else:
            # Override Path Specified
            _file = self.override_image_path

        try:
            fd = open(_file, 'rb')
        except:
            return None

        try:
            return fd.read()

        except:
            return None

        finally:
            fd.close()

    def escape_html(self, html, convert_new_lines=False):
        """
        Takes html text as input and escapes it so that it won't
        conflict with any xml/html wrapping characters.
        """
        escaped = _escape(html).\
                   replace(u'\t', u'&emsp;').\
                   replace(u'  ', u' &nbsp;')

        if convert_new_lines:
            return escaped.replace(u'\n', u'<br />')

        return escaped

    def to_html(self, body):
        """
        Returns the specified title in an html format and factors
        in a titles defined max length
        """
        html = markdown.markdown(body)

        # TODO:
        # This function should return multiple messages if we exceed
        # the maximum number of characters. the second message should

        # The new message should factor in the title and add ' cont...'
        # to the end of it.  It should also include the added characters
        # put in place by the html characters. So there is a little bit
        # of math and manipulation that needs to go on here.
        # we always return a list
        return [html, ]

    def notify(self, title, body, notify_type=NotifyType.SUCCESS,
               **kwargs):
        """
        This should be over-rided by the class that
        inherits this one.
        """
        if notify_type and notify_type not in NOTIFY_TYPES:
            self.warning(
                'An invalid notification type (%s) was specified.' % (
                notify_type,
            ))

        if not isinstance(body, basestring):
            body = ''
        if not isinstance(title, basestring):
            title = ''

        if title:
            title = title[0:self.title_maxlen]

        if self.notify_format == NotifyFormat.HTML:
            bodies = self.to_html(body=body)

        elif self.notify_format == NotifyFormat.TEXT:
            # TODO: this should split the content into
            # multiple messages
            bodies = [body[0:self.body_maxlen], ]

        #else notify_type was None

        while len(bodies):
            b = bodies.pop(0)
            # Send Message(s)
            if not self._notify(
                    title=title, body=b,
                    notify_type=notify_type,
                    **kwargs):
                return False

            # If we got here, we sent part of the notification
            # if there are any left, we should throttle so we
            # don't overload the server with requests (they
            # might not be happy with us otherwise)
            if len(bodies):
                self.throttle()

        return True

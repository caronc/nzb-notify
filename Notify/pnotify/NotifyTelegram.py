# -*- encoding: utf-8 -*-
#
# Telegram Notify Wrapper
#
# Copyright (C) 2016 Chris Caron <lead2gold@gmail.com>
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

# To use this plugin, you need to first access https://api.telegram.org
# You need to create a bot and acquire it's Token Identifier (bot_token)
#
# Basically you need to create a chat with a user called the 'BotFather'
# and type: /newbot
#
# Then follow through the wizard, it will provide you an api key
# that looks like this:123456789:alphanumeri_characters
#
# For each chat_id a bot joins will have a chat_id associated with it.
# You will need this value as well to send the notification.
#
# Log into the webpage version of the site if you like by accessing:
#    https://web.telegram.org
#
# You can't check out to see if your entry is working using:
#    https://api.telegram.org/botAPI_KEY/getMe
#
#    Pay attention to the word 'bot' that must be present infront of your
#    api key that the BotFather gave you.
#
#  For example, a url might look like this:
#    https://api.telegram.org/bot123456789:alphanumeri_characters/getMe
#
import requests
import re

from json import loads
from json import dumps

from NotifyBase import NotifyBase
from NotifyBase import NotifyFormat
from NotifyBase import HTTP_ERROR_MAP
from NotifyBase import HTML_NOTIFY_MAP
from NotifyBase import NotifyImageSize

# Telegram uses the http protocol with JSON requests
TELEGRAM_BOT_URL = 'https://api.telegram.org/bot'

# Token required as part of the API request
# allow the word 'bot' infront
VALIDATE_BOT_TOKEN = re.compile(
    r'(bot)?(?P<key>[0-9]+:[A-Za-z0-9_-]{32,34})',
    re.IGNORECASE,
)

# Chat ID is required 
IS_CHAT_ID_RE = re.compile(
    r'(@*(?P<idno>[0-9]{1,10})|(?P<name>[a-z_-][a-z0-9_-]*))',
    re.IGNORECASE,
)

# Used to break path apart into list of chat identifiers
CHAT_ID_LIST_DELIM = re.compile(r'[ \t\r\n,#\\/]+')

class NotifyTelegram(NotifyBase):
    """
    A wrapper for Telegram Notifications
    """
    def __init__(self, bot_token, chat_ids, **kwargs):
        """
        Initialize Telegram Object
        """
        super(NotifyTelegram, self).__init__(
            title_maxlen=250, body_maxlen=4096,
            notify_format=NotifyFormat.TEXT,
            **kwargs)

        result = VALIDATE_BOT_TOKEN.match(bot_token.strip())
        if not result:
            self.logger.warning(
                'The Bot Token specified (%s) is invalid.' % bot_token,
            )
            raise TypeError(
                'The Bot Token specified (%s) is invalid.' % bot_token,
            )

        # Store our API Key
        self.bot_token = result.group('key')

        if isinstance(chat_ids, basestring):
            self.chat_ids = filter(bool, CHAT_ID_LIST_DELIM.split(
                chat_ids,
            ))
        elif isinstance(chat_ids, (tuple, list)):
            self.chat_ids = list(chat_ids)

        else:
            self.chat_ids = list()

        if self.user:
            # Treat this as a channel too
            self.chat_ids.append(self.user)

        if len(self.chat_ids) == 0:
            self.logger.warning('No chat_id(s) were specified.')
            raise TypeError('No chat_id(s) were specified.')

    def _notify(self, title, body, notify_type, **kwargs):
        """
        Perform Telegram Notification
        """

        headers = {
            'User-Agent': self.app_id,
            'Content-Type': 'application/json',
        }

        # error tracking (used for function return)
        has_error = False

        url = '%s%s/%s' % (
            TELEGRAM_BOT_URL,
            self.bot_token,
            'sendMessage'
        )

        payload = {}

        if self.notify_format == NotifyFormat.HTML:
            payload['parse_mode'] = 'HTML'
            payload['text'] = '<b>%s</b>\r\n%s' % (title, body)

        else: # Text
            payload['parse_mode'] = 'Markdown'
            payload['text'] = '*%s*\r\n%s' % (title, body)

        # Create a copy of the chat_ids list
        chat_ids = list(self.chat_ids)
        while len(chat_ids):
            chat_id = chat_ids.pop(0)
            chat_id = IS_CHAT_ID_RE.match(chat_id)
            if not chat_id:
                self.logger.warning(
                    "The specified chat_id '%s' is invalid; skipping." % (
                        chat_id,
                    )
                )
                continue

            if chat_id.group('name') is not None:
                # Name
                payload['chat_id'] = '@%s' % chat_id.group('name')

            else:
                # ID
                payload['chat_id'] = chat_id.group('idno')

            self.logger.debug('Telegram POST URL: %s' % url)
            self.logger.debug('Telegram Payload: %s' % str(payload))

            try:
                r = requests.post(
                    url,
                    data=dumps(payload),
                    headers=headers,
                )
                if r.status_code != requests.codes.ok:
                    # We had a problem

                    try:
                        # Try to get the error message if we can:
                        error_msg = loads(r.text)['description']
                    except:
                        error_msg = None

                    try:
                        if error_msg:
                            self.logger.warning(
                                'Failed to send Telegram:%s ' % payload['chat_id'] +\
                                'notification: (%s) %s.' % (
                                    r.status_code, error_msg,
                            ))

                        else:
                            self.logger.warning(
                                'Failed to send Telegram:%s ' % payload['chat_id'] +\
                                'notification: %s (error=%s).' % (
                                    HTTP_ERROR_MAP[r.status_code],
                                    r.status_code,
                            ))

                    except IndexError:
                        self.logger.warning(
                            'Failed to send Telegram:%s ' % payload['chat_id'] +\
                            'notification (error=%s).' % (
                                r.status_code,
                        ))

                    #self.logger.debug('Response Details: %s' % r.raw.read())
                    # Return; we're done
                    has_error = True

            except requests.ConnectionError as e:
                self.logger.warning(
                    'A Connection error occured sending Telegram:%s ' % (
                        payload['chat_id']) + 'notification.'
                )
                self.logger.debug('Socket Exception: %s' % str(e))
                has_error = True

            if len(chat_ids):
                # Prevent thrashing requests
                self.throttle()

        return has_error

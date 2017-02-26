# -*- encoding: utf-8 -*-
#
# Some common utilities that may prove useful when processing downloads
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
import re
from os.path import expanduser

try:
    from xml.sax.saxutils import unescape
    SAX_UNESCAPE = True
except ImportError:
    SAX_UNESCAPE = False
    from HTMLParser import HTMLParser

# Pre-Escape content since we reference it so much
ESCAPED_PATH_SEPARATOR = re.escape('\\/')
ESCAPED_WIN_PATH_SEPARATOR = re.escape('\\')
ESCAPED_NUX_PATH_SEPARATOR = re.escape('/')

TIDY_WIN_PATH_RE = re.compile(
    '(^[%s]{2}|[^%s\s][%s]|[\s][%s]{2}])([%s]+)' % (
        ESCAPED_WIN_PATH_SEPARATOR,
        ESCAPED_WIN_PATH_SEPARATOR,
        ESCAPED_WIN_PATH_SEPARATOR,
        ESCAPED_WIN_PATH_SEPARATOR,
        ESCAPED_WIN_PATH_SEPARATOR,
))
TIDY_WIN_TRIM_RE = re.compile(
    '^(.+[^:][^%s])[\s%s]*$' %(
        ESCAPED_WIN_PATH_SEPARATOR,
        ESCAPED_WIN_PATH_SEPARATOR,
))

TIDY_NUX_PATH_RE = re.compile(
    '([%s])([%s]+)' % (
        ESCAPED_NUX_PATH_SEPARATOR,
        ESCAPED_NUX_PATH_SEPARATOR,
))
TIDY_NUX_TRIM_RE = re.compile(
    '([^%s])[\s%s]+$' % (
        ESCAPED_NUX_PATH_SEPARATOR,
        ESCAPED_NUX_PATH_SEPARATOR,
))

def os_path_split(path):
    """splits a path into a list by it's path delimiter

       hence: split_path('/etc/test/file') outputs:
                ['', 'etc', 'test', 'file']

       relative paths don't have the blank entry at the head
       of the string:
       hence: split_path('relative/file') outputs:
                ['relative', 'file']

       Paths can be reassembed as follows:
       assert '/'.join(split_path('/etc/test/file')) == \
               '/etc/test/file'

       assert '/'.join(split_path('relative/file')) == \
               'relative/file'
    """
    path = path.strip()
    if not path:
        return []

    p_list = re.split('[%s]+' % ESCAPED_PATH_SEPARATOR, path)
    try:
        # remove trailing slashes
        while not p_list[-1] and len(p_list) > 1:
            p_list.pop()
    except IndexError:
        # Nothing passed in
        return []
    return p_list

def tidy_path(path):
    """take a filename and or directory and attempts to tidy it up by removing
    trailing slashes and correcting any formatting issues.

    For example: ////absolute//path// becomes:
        /absolute/path

    """
    # Windows
    path = TIDY_WIN_PATH_RE.sub('\\1', path.strip())
    # Linux
    path = TIDY_NUX_PATH_RE.sub('\\1', path.strip())

    # Linux Based Trim
    path = TIDY_NUX_TRIM_RE.sub('\\1', path.strip())
    # Windows Based Trim
    path = expanduser(TIDY_WIN_TRIM_RE.sub('\\1', path.strip()))
    return path

def unescape_xml(content):
    """
    Escapes XML content into it's regular string value
    """

    if SAX_UNESCAPE:
        return unescape(content)
    return HTMLParser().unescape(content)

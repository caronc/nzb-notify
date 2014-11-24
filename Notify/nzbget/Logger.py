# -*- encoding: utf-8 -*-
#
# A scripting wrapper for NZBGet Post and Pre Processing
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
This class simplifies the setup of the logging to screen or file. It was
written to simplify the logging to and from an NZBGet Script
"""
import sys
import logging
import logging.handlers
from logging import Logger

from os import getpid

# Monkey Patch
logging.raiseExceptions = 0

# Logging Levels
DETAIL = 19
VERBOSE_DEBUG = 9
VERY_VERBOSE_DEBUG = 8

# Ensure Levels are Globally Added To logging module
logging.addLevelName(DETAIL, "DETAIL")
logging.addLevelName(VERBOSE_DEBUG, "VDEBUG")
logging.addLevelName(VERY_VERBOSE_DEBUG, "VVDEBUG")

def detail(self, message, *args, **kwargs):
    # logger takes its '*args' as 'args'.
    self._log(DETAIL, message, args, **kwargs)

def vdebug(self, message, *args, **kwargs):
    # logger takes its '*args' as 'args'.
    self._log(VERBOSE_DEBUG, message, args, **kwargs)

def vvdebug(self, message, *args, **kwargs):
    # logger takes its '*args' as 'args'.
    self._log(VERY_VERBOSE_DEBUG, message, args, **kwargs)

logging.Logger.detail = detail
logging.Logger.vdebug = vdebug
logging.Logger.vvdebug = vvdebug

def destroy_logger(name=None):
    """
       Destroys any log files assiated with name and/or logger
    """
    if name is None:
        name = __name__

    if isinstance(name, Logger):
        logger = name
    elif isinstance(name, basestring):
        logger = logging.getLogger(name)
    else:
        # not supported
        return

    logger = name
    if hasattr(logger, 'handlers'):
        # Destroy Logger
        for l in logger.handlers:
            logger.removeHandler(l)
            l.flush()
            try:
                l.close()
            except KeyError:
                # https://bugzilla.redhat.com/show_bug.cgi?id=573782
                # Bug 573782 - python logging's fileConfig causes
                # KeyError on shutdown
                pass

def init_logger(name=None, logger=True, debug=False, nzbget_mode=True,
                daily=False, bytecount=5242880, logcount=3, encoding=None):
    """
        Generate Logger

        name:         Defines a name to help identify each log entry
        logger:       - If set to 'None', then logging is disabled.
                      - If set to 'True', then content is sent to stdout
                        is used.
                      - If set to 'False', then content is sent to
                        stderr
                      - If set to a string, then the string is presumed
                        to be the filename where the logging should be
                        sent.
                      - If defined as a logger, then that is presumed
                        to be the log file to use.
        debug:        Enable extra debug log entries, if this is an interger
                      value, then that is the log level set
        nzbget_mode:  Log formatting does not include date/time, pid etc
                      because nzbget wraps all this for us.
        daily:        Rotate logs by day (instead of by size)
        encoding:     Can be set to something like 'bz2' to have all
                      content created compressed
    """

    if isinstance(logger, Logger):
        # Update handlers only
        for l in logger.handlers:
            if not nzbget_mode:
                l.setFormatter(logging. \
                    Formatter("%(asctime)s - " + str(getpid()) + \
                        " - %(levelname)s - %(message)s"))
            else:
                l.setFormatter(logging. \
                    Formatter("[%(levelname)s] %(message)s"))

        # Support NZBGET Detail Messages
        logging.addLevelName(DETAIL, 'DETAIL')

        if not nzbget_mode:
            logging.addLevelName(logging.DEBUG, 'DEBUG')
            if isinstance(debug, int):
                if debug <= VERBOSE_DEBUG:
                    logging.addLevelName(VERBOSE_DEBUG, 'VDEBUG')
                if debug <= VERY_VERBOSE_DEBUG:
                    logging.addLevelName(VERY_VERBOSE_DEBUG, 'VVDEBUG')

        else:
            # Level Name for [debug] has to be [info] or it simply won't print
            logging.addLevelName(logging.DEBUG, 'INFO] [DEBUG')
            if isinstance(debug, int):
                if debug <= VERBOSE_DEBUG:
                    logging.addLevelName(VERBOSE_DEBUG, 'INFO] [VDEBUG')
                if debug <= VERY_VERBOSE_DEBUG:
                    logging.addLevelName(VERY_VERBOSE_DEBUG, 'INFO] [VVDEBUG')

        return logger

    if name is None:
        # Namespace
        name = __name__

    # Perpare Logger
    _logger = logging.getLogger(name)

    # Ensure the logger isn't already initialized
    # to limit the number of handlers to 1, we sweep anything
    # that may or may not have already been created
    if isinstance(_logger, Logger):
        for l in _logger.handlers:
            _logger.removeHandler(l)
            l.flush()
            l.close()

    if logger is None:
        # Create a dummy log file without a handler
        _logger.setLevel(logging.CRITICAL)
        #logging.disable(logging.ERROR)
        # no logging handler nessisary
        return _logger

    elif isinstance(logger, basestring):
        # prepare rotating handler using the log file specified
        if not daily:
            h1 = logging.handlers.RotatingFileHandler(
                logger,
                maxBytes=bytecount,
                backupCount=logcount,
                encoding=encoding,
            )
        else:
            h1 = logging.handlers.TimedRotatingFileHandler(
                 logger,
                 when='midnight',
                 interval=1,
                 backupCount=logcount,
                 encoding=encoding,
            )

    elif logger:
        # stdout
        h1 = logging.StreamHandler(sys.stdout)
    else:
        # stderr
        h1 = logging.StreamHandler(sys.stderr)

    if debug is True:
        _logger.setLevel(logging.DEBUG)
        h1.setLevel(logging.DEBUG)

    elif debug in (False, None):
        # Default
        _logger.setLevel(DETAIL)
        h1.setLevel(DETAIL)
    else:
        try:
            debug = int(debug)
            _logger.setLevel(debug)
            h1.setLevel(debug)

        except (ValueError, TypeError):
            # Default
            _logger.setLevel(DETAIL)
            h1.setLevel(DETAIL)

    # Format logger
    if not nzbget_mode:
        h1.setFormatter(logging. \
                Formatter("%(asctime)s - " + str(getpid()) +
                    " - %(levelname)s - %(message)s"))
        logging.addLevelName(logging.DEBUG, 'DEBUG')
        if isinstance(debug, int):
            if debug <= VERBOSE_DEBUG:
                logging.addLevelName(VERBOSE_DEBUG, 'VDEBUG')
            if debug <= VERY_VERBOSE_DEBUG:
                logging.addLevelName(VERY_VERBOSE_DEBUG, 'VVDEBUG')

    else:
        h1.setFormatter(logging. \
                Formatter("[%(levelname)s] %(message)s"))
        # Level Name for [debug] has to be [info] or it simply won't print
        logging.addLevelName(logging.DEBUG, 'INFO] [DEBUG')
        if isinstance(debug, int):
            if debug <= VERBOSE_DEBUG:
                logging.addLevelName(VERBOSE_DEBUG, 'INFO] [VDEBUG')
            if debug <= VERY_VERBOSE_DEBUG:
                logging.addLevelName(VERY_VERBOSE_DEBUG, 'INFO] [VVDEBUG')

    # Add Handler
    _logger.addHandler(h1)

    return _logger

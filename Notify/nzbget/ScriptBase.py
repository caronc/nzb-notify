# -*- encoding: utf-8 -*-
#
# A base scripting class for NZBGet
#
# Copyright (C) 2014-2017 Chris Caron <lead2gold@gmail.com>
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
This script provides a base for all NZBGet Scripts and provides
functionality such as:
 * validate() - handle environment checking, correct versioning as well
                as if the expected configuration variables you specified
                are present.

 * push()     - pushes a variables to the NZBGet server


 * set()/get()- Hash table get/set attributes that can be set in one script
                and then later retrieved from another. get() can also
                be used to fetch content that was previously pushed using
                the push() tool. You no longer need to work with environment
                variables. If you enable the SQLite database, set content is
                put here as well so that it can be retrieved by another
                script.

 * unset()    - This allows you to unset values set by set() and get() as well
                as ones set by push().

 * nzb_set()  - Similar to the set() function identified above except it is
                used to build an nzb meta hash table which can be later pushed
                to the server using push_dnzb().

 * add_nzb()  - Using the built in API/RPC NZBGet supports, this allows you to
                specify a path to an NZBFile which you want to enqueue for
                downloading.

 * nzb_get()  - Retieves NZB Meta information previously stored.

 * nzb_unset()- Removes a variable previously set completely.

 * get_logs() - Using the built in API/RPC NZBGet supports, this retrieves and
                returns the latest logs.

 * get_files()- list all files in a specified directory as well as fetching
                their details such as filesize, modified date, etc in an
                easy to reference dictionary.  You can provide a ton of
                different filters to minimize the content returned. Filters
                can by a regular expression, file prefixes, and/or suffixes.

 * parse_nzbfile() - Parse an NZB-File and extract all of its meta
                     information from it. lxml must be installed on your
                     system for this to work correctly

 * parse_nzbcontent() - Parse meta information from the specified NZB Content
                     lxml must be installed on your system for this to work
                     correctly.

 * parse_url()  - Parse a URL and extract the protocol, user, pass,
                  remote directory and hostname from the string.

 * parse_list() - Takes a string (or more) as well as lists of strings as
                  input. It then cleans it up and produces an easy to
                  manage list by combining all of the results into 1.
                  Hence: parse_list('.mkv, .avi') returns:
                      [ '.mkv', '.avi' ]

 * parse_path_list() - Very smilar to parse_list() except that it is used
                  to handle directory paths while cleaning them up at the
                  same time.

 * parse_bool() - Handles all of NZBGet's configuration options such as
                  'on' and 'off' as well as 'yes' or 'no', or 'True' and
                  'False'.  It greatly simplifies the checking of these
                  variables passed in from NZBGet

 * push_guess() - You can push a guessit dictionary (or one of your own
                  that can help identify your release for other scripts
                  to use later after yours finishes

 * pull_guess() - Pull a previous guess pushed by another script.
                  why redo grunt work if it's already done for you?
                  if no previous guess content was pushed, then an
                  empty dictionary is returned.
 * push_dnzb()  - You can push all nzb meta information onbtained to the
                  NZBGet server as DNZB_ meta tags.

 * pull_dnzb()  - Pull all DNZB_ meta tags issued by the server and return
                  their values in a dictionary. if no DNZB_ (NZB Meta
                  information) was found, then an empty dictionary is returned
                  instead.

* is_unique_instance() - Allows you to ensure your instance of your script is
                  unique. This is useful for Scheduled scripts which can be
                  called and then run concurrently with NZBGet.

Ideally, you'll write your script using this class as your base wrapper
requiring you to only define a main() function and call run().
You no longer need to manage the different return codes NZBGet uses,
instead you can just return True, False and None from your main()
function and let the wrappers transform that to the proper return code.

Logging is automatically initialized and works right away.
When you define your logging, you can prepare in the following ways:
   logging=True
        All output will be redirected to stdout

   logging=False
        All output will be redirected to stderr
   logging=None
        No logging will take place
   logging=Logger()
        If you pass a Logger object (you already set up yourself), then
        logging will just reference that instance.
   logging=string
        The string you identify will be the log file content is written to
        with self rotating capabilties built in.  Man... life is so easy...

Additionally all exception handling is wrapped to make debugging easier.
"""

import re
from tempfile import gettempdir
from tempfile import mkstemp
from os import environ
from os import makedirs
from os import chdir
from os import unlink
from os import getcwd
from os import listdir
from os import access
from os import W_OK
from os import R_OK
from os import X_OK
from os import kill
from os import getpid
from os.path import isdir
from os.path import islink
from os.path import isfile
from os.path import join
from os.path import dirname
from os.path import abspath
from os.path import basename
from os.path import normpath
from os.path import splitext
from getpass import getuser
from logging import Logger
from datetime import datetime
from Utils import tidy_path
import ssl

import traceback
from sys import exc_info

from Logger import VERBOSE_DEBUG
from Logger import VERY_VERBOSE_DEBUG
from Logger import init_logger
from Logger import destroy_logger

from Utils import ESCAPED_WIN_PATH_SEPARATOR
from Utils import ESCAPED_NUX_PATH_SEPARATOR
from Utils import unescape_xml

import signal

# Initialize the default character set to use
DEFAULT_CHARSET = u'utf-8'

# NZB Processing Support if lxml is installed
LXML_TYPE = None
try:
    from lxml import etree
    from lxml.etree import XMLSyntaxError
    LXML_TYPE = u'lxml.etree'
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
        XMLSyntaxError = Exception
        LXML_TYPE = u'xml.etree.cElementTree'
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
            XMLSyntaxError = Exception
            LXML_TYPE = u'xml.etree.ElementTree'
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
                XMLSyntaxError = Exception
                LXML_TYPE = u'cElementTree'
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                    XMLSyntaxError = Exception
                    LXML_TYPE = u'elementtree.ElementTree'
                except ImportError:
                    # No panic, we just can't use nzbfile parsing
                    pass

# Database Support if sqllite is installed
try:
    from Database import Database
    from Database import Category
except ImportError:
    # No panic, we just can't use database
    pass

# File Stats
from stat import ST_ATIME
from stat import ST_CTIME
from stat import ST_MTIME
from stat import ST_SIZE

from os import stat

from urlparse import urlparse
from urlparse import parse_qsl
from urllib import quote
from urllib import unquote

from base64 import standard_b64encode
try:
    # Python 2
    from xmlrpclib import ServerProxy
    from xmlrpclib import SafeTransport
except ImportError:
    # Python 3
    from xmlrpc.client import ServerProxy

# Some booleans that are read to and from nzbget
NZBGET_BOOL_TRUE = u'yes'
NZBGET_BOOL_FALSE = u'no'

# The following directories will never be recursively looked
# into when using get_files()
SKIP_DIRECTORIES = (
    # OS X Meta Directories
    '.DS_Store',
    '.AppleDouble',
    '__MACOSX',
)


class EXIT_CODE(object):
    """List of exit codes for post processing
    """
    PARCHECK_CURRENT = 91
    # Request NZBGet to do par-check/repair for current nzb-file.
    # This code can be used by pp-scripts doing unpack on their own.
    PARCHECK_ALL = 92
    # Post-process successful
    SUCCESS = 93
    # Post-process failed
    FAILURE = 94
    # Process skipped. Use this code when your script determines that it is
    # neither a success or failure. Perhaps your just not processing anything
    # due to how content was parsed.
    NONE = 95

EXIT_CODES = (
    EXIT_CODE.PARCHECK_CURRENT,
    EXIT_CODE.PARCHECK_ALL,
    EXIT_CODE.SUCCESS,
    EXIT_CODE.FAILURE,
    EXIT_CODE.NONE,
)


class NZBGetDuplicateMode(object):
    """Defines Duplicate Mode. This is used when Adding NZB-Files directly
    """
    # This is default duplicate mode. Only nzb-files with higher scores
    # (when already downloaded) are considered.
    SCORE = u'SCORE'

    # All NZB-Files regardless of their scores are downloaded
    ALL = 'ALL'

    # Force download and disable all duplicate checks.
    FORCE = 'FORCE'


class NZBGetExitException(Exception):
    def __init__(self, code=EXIT_CODE.NONE):
        # Now for your custom code...
        self.code = code


class NZBGetSuccess(NZBGetExitException):
    def __init__(self):
        super(NZBGetExitException, self).\
            __init__(code=EXIT_CODE.SUCCESS)


class NZBGetFailure(NZBGetExitException):
    def __init__(self):
        super(NZBGetExitException, self).\
            __init__(code=EXIT_CODE.FAILURE)


class NZBGetParCheckCurrent(NZBGetExitException):
    def __init__(self):
        super(NZBGetExitException, self).\
            __init__(code=EXIT_CODE.PARCHECK_CURRENT)


class NZBGetParCheckAll(NZBGetExitException):
    def __init__(self):
        super(NZBGetExitException, self).\
            __init__(code=EXIT_CODE.PARCHECK_ALL)


class Health(tuple):
    """
    A class that returns health in in its 2 categories ie:
        ('SUCCESS', 'ALL')
    """

    # Define Main Categories
    SUCCESS = u'SUCCESS'
    WARNING = u'WARNING'
    FAILURE = u'FAILURE'
    DELETED = u'DELETED'

    # This gets set if the category was not correctly defined (or wasn't
    # defined at all)
    UNDEFINED = u'UNDEFINED'

    # Default Sub Category if one isn't matched
    DEFAULT_SUB = u'DEFAULT'

    # Define Category Map
    # has_archive: The original archive files are still present such as
    #              the .rar, .zip, .7z, .PAR2, .PAR3, files
    #
    # is_unpacked: The archive has been successfully extracted and content
    #           is present for parsing.
    HEALTH_MAP = {
        UNDEFINED: {
            # Assume debug mode because we aren't processing correct
            # values from environment
            DEFAULT_SUB: {u'has_archive': True, u'is_unpacked': True, },
        },
        SUCCESS: {
            DEFAULT_SUB: {u'has_archive': False, u'is_unpacked': True, },
            # Downloaded and par-checked or unpacked successfully. All
            # post-processing scripts were successful. The download is
            # completely OK.
            u'ALL': {},  # Use all defaults
            # The download was marked as good using mark(Mark.GOOD)
            u'GOOD': {},  # Use all defaults
            # Download was successful, download health is 100.0%. No par-check
            # was made (there are no par-files). No unpack was made (there are
            # no archive files or unpack was disabled for that download or
            # globally).
            u'HEALTH': {},  # Use all defaults
            # The hidden history item has status SUCCESS.
            u'HIDDEN': {},  # Use all defaults
            # Similar to SUCCESS/ALL but no post-processing scripts were
            # executed. Downloaded and par-checked successfully. No unpack was
            # made (there are no archive files or unpack was disabled for that
            # download or globally).
            u'PAR': {},  # Use all defaults
            # Similar to SUCCESS/ALL but no post-processing scripts were
            # executed. Downloaded and unpacked successfully. Par-check was
            # successful or was not necessary.
            u'UNPACK': {},  # Use all defaults
        },

        WARNING: {
            DEFAULT_SUB: {u'has_archive': True, u'is_unpacked': False, },
            # Par-check is required by is disabled in settings
            # (option ParCheck=Manual).
            u'DAMAGED': {},  # Use all defaults
            # Download health is below 100.0%. No par-check was made (there
            # are no par-files). No unpack was made (there are no archive
            # files or unpack was disabled for that download or globally).
            u'HEALTH': {},  # Use all defaults
            # The hidden history item has status FAILURE.
            u'HIDDEN': {},  # Use all defaults
            # Unpack has failed because the password was not provided or was
            # wrong. Only for rar5-archives.
            u'PASSWORD': {},  # Use all defaults
            # Par-check has detected damage and has downloaded additional
            # par-files but the repair is disabled in settings
            # (option ParRepair=no).
            u'REPAIRABLE': {},  # Use all defaults
            # The URL was fetched successfully but an error occurred during
            # scanning of the downloaded file. The downloaded file isn't a
            # proper nzb-file. This status usually means the web-server has
            # returned an error page (HTML page) instead of the nzb-file.
            u'SCAN': {},  # Use all defaults
            # Downloaded successfully. Par-check and unpack were either
            # successful or were not performed. At least one of the
            # post-processing scripts has failed.
            u'SCRIPT': {},  # Use all defaults
            # The URL was fetched successfully but downloaded file was not
            # nzb-file and was skipped by the scanner.
            u'SKIPPED': {},  # Use all defaults
            # Unpack has failed due to not enough space on the drive.
            u'SPACE': {},  # Use all defaults
        },

        FAILURE: {
            DEFAULT_SUB: {u'has_archive': True, u'is_unpacked': False, },
            # The download was marked as good using mark(Mark.BAD)
            u'BAD': {},  # Use all defaults
            # The download was aborted by history check.
            # Usual case is: download health is below critical health. No
            # par-check was made (there are no par-files). No unpack was made
            # (there are no archive files or unpack was disabled for that
            # download or globally).
            u'HEALTH': {},  # Use all defaults
            # An error has occurred when moving files from intermediate
            # directory into the final destination directory.
            u'MOVE': {},  # Use all defaults
            # The par-check has failed.
            u'PAR': {},  # Use all defaults
            # The unpack has failed and there are no par-files.
            u'UNPACK': {},  # Use all defaults
        },

        DELETED: {
            DEFAULT_SUB: {u'has_archive': False, u'is_unpacked': False, },
            # The download was deleted by duplicate check.
            u'DUPE': {},  # Use all defaults
            # Fetching of the URL has failed.
            u'FETCH': {},  # Use all defaults
            # The download was manually deleted by user.
            u'MANUAL': {},  # Use all defaults
        }
    }

    def __new__(self, health):
        """Allow initializations to set default values too
        """
        # We only work with the first (and potentially the second item)

        # Default Category
        category = Health.UNDEFINED

        # Default Sub Category
        subcategory = Health.DEFAULT_SUB

        if isinstance(health, basestring):
            health = re.split('[\s/\\\]+', health + '/')

        elif not isinstance(health, (tuple, list)):
            health = (category, subcategory)

        health = [h.upper() for h in filter(bool, health)]

        try:
            if health[0] in Health.HEALTH_MAP:
                category = health[0]

        except IndexError:
            # no problem, use default
            pass

        try:
            if health[1] in Health.HEALTH_MAP[category]:
                # no problem, use default
                subcategory = health[1]

        except IndexError:
            # no problem, use default
            pass

        return super(Health, self)\
                .__new__(self, tuple((category, subcategory)))

    def __init__(self, health):
        super(Health, self).__init__()

        # cat is a list or tuple at this point, we need to massage it
        # Get defaults
        self.category = self[0]
        self.subcategory = self[1]

        # Assign Defaults
        self.has_archive = Health.HEALTH_MAP\
                [self.category][Health.DEFAULT_SUB][u'has_archive']
        self.is_unpacked = Health.HEALTH_MAP\
                [self.category][Health.DEFAULT_SUB][u'is_unpacked']

        try:
            self.has_archive = Health.HEALTH_MAP\
                    [self.category][self.subcategory][u'has_archive']

        except KeyError:
            # No problem, we'll just use the defaults
            pass

        try:
            self.is_unpacked = Health.HEALTH_MAP\
                [self.category][self.subcategory][u'is_unpacked']

        except KeyError:
            # No problem, we'll just use the defaults
            pass

        # End of Health.__init__()
        return

    def __str__(self):
        """
        Return the status in a fashion the string format
        """
        return '/'.join(self)


class PRIORITY(object):
    """Although priority can be any integer value, the web-interface operates
    with six predefined priorities.
    """
    VERY_LOW = -100
    LOW = -50
    NORMAL = 0
    HIGH = 50
    VERY_HIGH = 100
    FORCE = 900

# A list of priorities makes it easier to validate them
# for each priority added above, make sure you also update this list.
PRIORITIES = (
    PRIORITY.VERY_LOW,
    PRIORITY.LOW,
    PRIORITY.NORMAL,
    PRIORITY.HIGH,
    PRIORITY.VERY_HIGH,
    PRIORITY.FORCE,
)

# Environment variables that identify specific configuration for scripts
SYS_ENVIRO_ID = u'NZBOP_'

# Script options
CFG_ENVIRO_ID = u'NZBPO_'

# Shared configuration options passed through NZBGet and push(); if these
# are found in the environment, they are saved to the `config` dictionary
SHR_ENVIRO_ID = u'NZBR_'

# Environment ID used when calling tests commands from NZBGet
"""
For example... the below would attempt to execute the function
action_ConnectionTest

If that didn't exist, it would attempt to execute action_connectiontest
and if that didn't exist, nothing would happen.

But the point is, it's very easy to simply add the below code and create
a function map to it. This is a new feature introduced after NZBGet v18
############################################################################
### OPTIONS                                                              ###

#
# To check connection parameters click the button.
# ConnectionTest@Send Test E-Mail
#
#
# ...

"""
TST_ENVIRO_ID = u'NZBCP_'

# The Key Environment Variable that is used to dermine the Test command
# to call (called from NZBGet's Configuration Screen)
TEST_COMMAND = u'%sCOMMAND' % TST_ENVIRO_ID

# Environment ID used when pushing common variables to the server
PUSH_ENVIRO_ID = u'NZBPR_'

# DNZB is an environment variable sometimes referenced by other scripts
SHR_ENVIRO_DNZB_ID = u'_DNZB_'

# GUESS is an environment variable sometimes referenced by other scripts
# it provides the guessed information for other scripts to save them
# from re-guessing all over again.
SHR_ENVIRO_GUESS_ID = u'_GUESS_'

# NZBGet Internal Message Passing Prefix
NZBGET_MSG_PREFIX = u'[NZB] '

# Precompile regular expressions for speed
SYS_OPTS_RE = re.compile('^%s([A-Z0-9_]+)$' % SYS_ENVIRO_ID)
CFG_OPTS_RE = re.compile('^%s([A-Z0-9_]+)$' % CFG_ENVIRO_ID)
SHR_OPTS_RE = re.compile('^%s([A-Z0-9_]+)$' % SHR_ENVIRO_ID)
TST_OPTS_RE = re.compile('^%s([A-Z0-9_]+)$' % TST_ENVIRO_ID)
DNZB_OPTS_RE = re.compile('^%s%s([A-Z0-9_]+)$' % (
    SHR_ENVIRO_ID,
    SHR_ENVIRO_DNZB_ID,
))

# Precompile Guess Fetching
SHR_GUESS_OPTS_RE = re.compile('^%s([A-Z0-9_]+)$' % SHR_ENVIRO_GUESS_ID)

# This is used as a mapping table so when we fetch content later
# at another time we can map them to the same format commonly
# used.
GUESS_KEY_MAP = {
    u'AUDIOCHANNELS': u'audioChannels', u'AUDIOCODEC': u'audioCodec',
    u'AUDIOPROFILE': u'audioProfile', u'BONUSNUMBER': u'bonusNumber',
    u'BONUSTITLE': u'bonusTitle', u'CONTAINER': u'container', u'DATE': u'date',
    u'EDITION': u'edition', u'EPISODENUMBER': u'episodeNumber',
    u'FILMNUMBER': u'filmNumber', u'FILMSERIES': u'filmSeries',
    u'FORMAT': u'format', u'LANGUAGE': u'language',
    u'RELEASEGROUP': u'releaseGroup',  u'SCREENSIZE': u'screenSize',
    u'SEASON': u'season', u'SERIES': u'series', u'SPECIAL': u'special',
    u'SUBTITLELANGUAGE': u'subtitleLanguage', u'TITLE': u'title',
    u'TYPE': u'type', u'VIDEOCODEC': u'videoCodec', u'VTYPE': u'vtype',
    u'WEBSITE': u'website', u'YEAR': u'year',
}

# keys should not be complicated... make it so they aren't
VALID_KEY_RE = re.compile('[^a-zA-Z0-9_.-]')

# delimiters used to separate values when content is passed in by string
# This is useful when turning a string into a list
STRING_DELIMITERS = r'[\[\]\;,\s]+'

# For separating paths
PATH_DELIMITERS = r'([%s]+[%s;\|,\s]+|[;\|,\s%s]+[%s]+)' % (
        ESCAPED_NUX_PATH_SEPARATOR,
        ESCAPED_NUX_PATH_SEPARATOR,
        ESCAPED_NUX_PATH_SEPARATOR,
        ESCAPED_NUX_PATH_SEPARATOR,
)

# SQLite Database
NZBGET_DATABASE_FILENAME = "nzbget/nzbget.db"

# URL Indexing Table for returns via parse_url()
VALID_URL_RE = re.compile(r'^[\s]*([^:\s]+):[/\\]*([^?]+)(\?(.+))?[\s]*$')
VALID_HOST_RE = re.compile(r'^[\s]*([^:/\s]+)')
VALID_QUERY_RE = re.compile(r'^(.*[/\\])([^/\\]*)$')


class SCRIPT_MODE(object):
    # After the download of nzb-file is completed NZBGet can call
    # post-processing scripts (pp-scripts). The scripts can perform further
    # processing of downloaded files such es delete unwanted files
    # (*.url, etc.), send an e-mail notification, transfer the files to other
    # application and do any other things.
    POSTPROCESSING = u'postprocess'

    # Scan scripts are called when a new file is found in the incoming nzb
    # directory (option `NzbDir`). If a file is being added via web-interface
    # or via RPC-API from a third-party app the file is saved into nzb
    # directory and then processed. NZBGet loads only files with nzb-extension
    # but it calls the scan scripts for every file found in the nzb directory.
    # This allows for example for scan scripts which unpack zip-files
    # containing nzb-files.

    # To activate a scan script or multiple scripts put them into `ScriptDir`,
    # then choose them in the option `ScanScript`.
    SCAN = u'scan'

    # Queue scripts are called after the download queue was changed. In the
    # current version the queue scripts are called only after an nzb-file was
    # added to queue. In the future they can be calledon other events too.

    # To activate a queue script or multiple scripts put them into `ScriptDir`,
    # then choose them in the option `QueueScript`.
    QUEUE = u'queue'

    # Scheduler scripts are called by scheduler tasks (setup by the user).

    # To activate a scheduler script or multiple scripts put them into
    # `ScriptDir`, then choose them in the option `TaskX.Script`.
    SCHEDULER = u'scheduler'

    # To activate a feed script or multiple scripts put them into
    # `ScriptDir`, then choose them in the option `FeedX.Script`.
    FEED = u'feed'

    # To activate a test call to the script, we look for NZBCP_
    # entries. These are populated through calls made available thorugh the
    # configuration portion of NZBGet. v1.8 introduced the ability to
    # test if your configuration is set up okay.
    CONFIG_ACTION = u'action'

    # None is detected if you aren't using one of the above types
    NONE = ''

# Depending on certain environment variables, a mode can be detected
# a mode can be used to. When using a MultiScript
SCRIPT_MODES = (
    # The order these are listed is very important,
    # it identifies the order when preforming sanity
    # checking
    SCRIPT_MODE.CONFIG_ACTION,
    SCRIPT_MODE.POSTPROCESSING,
    SCRIPT_MODE.SCAN,
    SCRIPT_MODE.QUEUE,
    SCRIPT_MODE.SCHEDULER,
    SCRIPT_MODE.FEED,

    # None should always be the last entry
    SCRIPT_MODE.NONE,
)


class ScriptBase(object):
    """The intent is this is the script you run from within your script
       after overloading the main() function of your class
    """

    def __init__(self, logger=True, debug=False, script_mode=None,
                 database_key=None, tempdir=None, *args, **kwargs):

        # logger identifier
        self.logger_id = __name__
        self.logger = logger
        self.debug = debug

        # Initialize the default character set
        self.charset = None

        # If a configuration test is being executed, this points to the
        # function itself.  Otherwise this is set to None.
        self._config_action = None

        # API by default is not configured; it is set up when a call to
        # an api function is made.
        self.api = None

        # Acquire our PID
        self.pid = getpid()

        # Extra debug modes used from command line; it gets to be
        # too noisy if you pass this into nzbget but if you really
        # insist, you can define a VDEBUG or a VVDEBUG as arguments
        # to your script.  This works best if you setup your script
        # and just set the debug variable above to 'VERBOSE_DEBUG',
        # or 'VERY_VERBOSE_DEBUG'

        # Verbose Debug Mode
        self.vdebug = kwargs.get(
            'vdebug', self.parse_bool(self.debug == VERBOSE_DEBUG),
        )

        # Very Verbose Debug Mode
        self.vvdebug = kwargs.get(
            'vvdebug', self.parse_bool(self.debug == VERY_VERBOSE_DEBUG),
        )

        # Script Mode
        self.script_mode = None
        if not hasattr(self, 'script_dict'):
            # Only define once
            self.script_dict = {}

        # For Database Handling
        self.database = None
        self.database_key = database_key

        # Fetch System Environment (passed from NZBGet)
        self.system = dict([(SYS_OPTS_RE.match(k).group(1), v.strip())
            for (k, v) in environ.items() if SYS_OPTS_RE.match(k)])

        # Fetch/Load Script Specific Configuration
        self.config = dict([(CFG_OPTS_RE.match(k).group(1), v.strip())
            for (k, v) in environ.items() if CFG_OPTS_RE.match(k)])

        # Fetch/Load Shared Configuration through push()
        self.shared = dict([(SHR_OPTS_RE.match(k).group(1), v.strip())
            for (k, v) in environ.items() if SHR_OPTS_RE.match(k)])

        # Fetch/Load Test/Command Specific Configuration; This is used
        # when issuing commands to a script from the configuration screen
        self.test = dict([(TST_OPTS_RE.match(k).group(1), v.strip()) \
            for (k, v) in environ.items() if TST_OPTS_RE.match(k)])

        # Preload nzbheaders based on any DNZB environment variables
        self.nzbheaders = self.pull_dnzb()

        # self.tempdir
        # path to temporary directory to work from
        if tempdir is None:
            self.tempdir = self.system.get('TEMPDIR')
        else:
            self.tempdir = tempdir

        # The pidfile is initialized if we call is_unique_instance()
        self.pidfile = None

        # We record the timestamp of our pid file after it's created
        # so that if it's missing, or has a different time stamp associated
        # with it, we can assume someone is mucking about; we will close
        self.pidfile_tstamp = None

        # version detection
        try:
            self.version = '%s.' % self.system.get('VERSION')
            self.version = int(self.version.split('.')[0])
        except (TypeError, ValueError):
            self.version = 11

        # Enabling DEBUG as a flag by specifying in the configuration
        # section of your script
        #Debug=no
        if self.debug is None:
            self.debug = self.parse_bool(
                self.config.get('DEBUG', False))

        # Enabling Character Set as a flag by specifying in the configuration
        # section of your script
        #CharSet=no
        if self.charset is None:
            self.charset = self.config.get('CHARSET', DEFAULT_CHARSET)

        # Verbose Debug
        if self.vdebug is None:
            self.vdebug = self.parse_bool(
                self.config.get('VDEBUG', False))
        if self.vdebug:
            self.debug = VERBOSE_DEBUG

        # Very Verbose Debug - Developers only!!
        if self.vvdebug is None:
            self.vvdebug = self.parse_bool(
                self.config.get('VVDEBUG', False))
        if self.vvdebug:
            self.debug = VERY_VERBOSE_DEBUG

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

        # Track the current working directory
        try:
            self.curdir = getcwd()
        except OSError:
            # This happens on some systems that simply don't
            # allow us access to this information
            self.curdir = './'

        # enforce temporary directory
        if not self.tempdir:
            self.tempdir = join(
                gettempdir(),
                'nzbget-%s' % getuser(),
            )
            # Force environment to be the same
            self.system['TEMPDIR'] = self.tempdir
            environ['%sTEMPDIR' % SYS_ENVIRO_ID] = self.tempdir

        if not isdir(self.tempdir):
            try:
                makedirs(self.tempdir, 0700)
            except:
                self.logger.warning(
                    'Temporary directory could not be ' + \
                    'created: %s' % self.system['TEMPDIR'],
                )

        if self.vvdebug:
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
            # Print Global System Varables to help debugging process
            #
            # Note: This is a very verbose process, so it is only performed
            #       if both the debug and vvdebug flags are set.
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
            for k, v in self.system.items():
                self.logger.vvdebug('%s%s=%s' % (SYS_ENVIRO_ID, k, v))

            for k, v in self.config.items():
                self.logger.vvdebug('%s%s=%s' % (CFG_ENVIRO_ID, k, v))

            for k, v in self.shared.items():
                self.logger.vvdebug('%s%s=%s' % (SHR_ENVIRO_ID, k, v))

            for k, v in self.test.items():
                self.logger.vvdebug('%s%s=%s' % (TST_ENVIRO_ID, k, v))

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Enforce system/global variables for script processing
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        self.config['DEBUG'] = self.debug

        # Set environment variable how NZBGet Would have done so
        if self.debug:
            environ['%sDEBUG' % SYS_ENVIRO_ID] = NZBGET_BOOL_TRUE
        else:
            environ['%sDEBUG' % SYS_ENVIRO_ID] = NZBGET_BOOL_FALSE

        if script_mode is not None:
            if script_mode in self.script_dict.keys() + [SCRIPT_MODE.NONE, ]:
                self.script_mode = script_mode
                if self.script_mode is SCRIPT_MODE.NONE:
                    self.logger.debug('Script mode forced off.')
                else:
                    self.logger.debug(
                        'Script mode forced to: %s' % self.script_mode,
                    )
            else:
                self.logger.warning(
                    'Could not force script mode to: %s' % script_mode,
                )

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Detect the mode we're running in
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        if self.script_mode is None:
            self.detect_mode()

        if self.script_mode == SCRIPT_MODE.NONE:
            # Reload logging without NZBGet mode configured
            self.logger = init_logger(
                name=self.logger_id,
                logger=self.logger,
                debug=self.debug,

                # NZBGet mode disabled
                nzbget_mode=False,
            )
        else:
            # An NZBGet Mode means we should work out of a writeable directory
            try:
                chdir(self.tempdir)
            except OSError:
                self.logger.warning(
                    'Temporary directory is not ' + 'accessible: %s' %
                    self.tempdir,
                )

        # Initialize the chosen script mode
        if hasattr(self, '%s_%s' % (self.script_mode, 'init')):
            getattr(
                self, '%s_%s' % (self.script_mode, 'init')
            )(*args, **kwargs)

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Signal Handling
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        try:
            if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
                # only handle if there isn't already a handler, e.g. for Pdb.
                signal.signal(signal.SIGINT, self.signal_quit)

            signal.signal(signal.SIGTERM, self.signal_quit)

        except ValueError:
            # This can occur if calling the script from within a thread
            # we just gracefully move on if this happens
            pass

    def is_unique_instance(self, pidfile=None, die_on_fail=True,
                           verbose=True):
        """
        Writes a PID file if one is not already present and returns
        True if the instance is unique.

        if the pidfile isn't specified, then it is automatically
        determined.

        if die_on_fail is set to True, then detected non-unique
        instances will cause the script to exit.

        verbose is a rather useless switch; but it helps control some of the
        redundant log messages since the script is called before the
        whole script exits, and if die_on_fail is set, you'll end up seeing
        these messages twice.  The final clean-up runs this script with
        the quiet flag set to True.
        """
        def _pid_running(pid):
            """ Returns False if the pid wasn't found running
            otherwise it returns True if it was found running.
            """
            try:
                kill(pid, 0)
            except OSError:
                return False
            return True

        if pidfile is not None:
            self.pidfile = pidfile

        if not self.pidfile:
            self.pidfile = join(self.tempdir, '.run', '%s-%s.pid' % (
                __name__, self.script_mode,
            ))

        if self.pidfile_tstamp is not None:
            # PID-File already created and running; test
            try:
                pidfile_tstamp = datetime\
                    .fromtimestamp(stat(self.pidfile)[ST_MTIME])

            except (IndexError, ValueError, OSError):
                if verbose:
                    self.logger.warning(
                        'Detected PID-File tampering (missing/bad).',
                    )

                # Reset class pidfile information and do not touch
                # PID-File as there is a chance it is no longer
                # ours
                self.pidfile_tstamp = None

                if die_on_fail:
                    raise NZBGetExitException
                return False

            if pidfile_tstamp != self.pidfile_tstamp:
                if verbose:
                    self.logger.warning(
                        'Detected PID-File tampering (changed timestamp).',
                    )

                # Reset class pidfile information and do not touch
                # PID-File as there is a chance it is no longer
                # ours
                self.pidfile_tstamp = None

                if die_on_fail:
                    raise NZBGetExitException
                return False

        if verbose:
            self.logger.debug('Testing for PID-File: %s (die_on_fail=%s)' % (
                self.pidfile,
                die_on_fail and "True" or "False",
            ))

        # PID Directory
        piddir = dirname(self.pidfile)

        # An NZBGet Mode means we should work out of a writeable directory
        if not isdir(piddir):
            try:
                makedirs(piddir, 0755)
                if verbose:
                    self.logger.info(
                        'Created PID-File directory: %s' % piddir
                    )
            except (IOError, OSError):
                if verbose:
                    self.logger.error(
                        'PID-File directory could not be ' + \
                        'created: %s' % piddir
                    )
                if die_on_fail:
                    raise NZBGetExitException
                return False

        if isfile(self.pidfile):
            try:
                pid = int(open(self.pidfile, 'r').read())
                if verbose:
                    self.logger.debug(
                        'PID-File identifies PID %d (our PID is %d):' % (
                        pid,
                        self.pid,
                    ))

            except (ValueError, TypeError):
                # Bad data
                if verbose:
                    self.logger.info(
                            'Removed (dead) PID-File: %s' % self.pidfile)
                try:
                    unlink(self.pidfile)
                    if verbose:
                        self.logger.info(
                            'Removed (dead) PID-File: %s' % self.pidfile)
                except:
                    unlink(self.pidfile)
                    if verbose:
                        self.logger.warning(
                            'Failed to removed (dead) PID-File: %s' % \
                            self.pidfile)

                    # It probably isn't ours
                    self.pidfile_tstamp = None

                    if die_on_fail:
                        raise NZBGetExitException

                    return False

            except (IOError, OSError):
                # Can't access content
                if verbose:
                    self.logger.warning(
                        'Can not access PID-File: %s' % self.pidfile)

                # It probably isn't ours
                self.pidfile_tstamp = None

                if die_on_fail:
                    raise NZBGetExitException
                return False

            if pid != self.pid:
                if _pid_running(pid):
                    if verbose:
                        self.logger.warning(
                           'Process is already running in ' +
                            'another instance (pid=%d)' % pid,
                        )

                    # We're done
                    if die_on_fail:
                        raise NZBGetExitException
                    return False
            else:
                # Nothing more to do
                return True

        # Write our PIDFile
        try:
           fp = open(self.pidfile, "w")

        except:
            if verbose:
                self.logger.warning('Could not open PID-File for writing.')
            if die_on_fail:
                raise NZBGetExitException
            return False

        try:
            fp.write("%s" % str(self.pid))
        except:
            if verbose:
                self.logger.warning('Could not write PID into PID-File.')
            fp.close()
            if die_on_fail:
                raise NZBGetExitException
            return False

        try:
            fp.close()
        except:
            if verbose:
                self.logger.warning('Could not close PID-File.')
            if die_on_fail:
                raise NZBGetExitException
            return False

        # We now want to get the modify time of our pid file
        try:
            self.pidfile_tstamp = datetime\
                .fromtimestamp(stat(self.pidfile)[ST_MTIME])

        except (IndexError, ValueError, OSError):
            if verbose:
                self.logger.warning(
                    'Could not exctract PID-File creation.',
                )

            try:
                # Cleanup
                unlink(self.pidfile)
            except:
                pass

            if die_on_fail:
                raise NZBGetExitException
            return False

        # We wrote our PID file successfully
        if verbose:
            self.logger.info(
                'Created PID-File: %s (pid=%d)' % (
                     self.pidfile, self.pid,
            ))
        return True

    def __del__(self):
        if self.logger_id:
            destroy_logger(self.logger_id)

    def _push(self, key, value):
        """NZBGet has the ability to process certain messages
        delivered to it via stdout. This is just a wrapper
        script to ease this process

        This version of push is just used internally. It's designed
        To update system variables and only supports a specific
        set of commands which are predefined in the scripts that
        inherit this base class.

        users should be utlizing the push() command instead of
        this one.
        """
        # Content is only pushable in certain modes
        if self.script_mode is SCRIPT_MODE.NONE:
            # if there is no script mode, then the calling
            # function isn't supported by NZBGet (or this
            # framework)
            return True

        elif value is None:
            # Never print... well.. nothing, you can acomplish
            # this by passing in an empty string ('')
            return False

        # clean key
        key = VALID_KEY_RE.sub('', key).upper()

        if isinstance(value, bool):
            # convert boolean's to int's for consistency
            value = str(int(value))

        elif not isinstance(value, basestring):
            value = str(value)

        # Push message on to nzbget (by simply sending it to
        # stdout)
        print('%s%s=%s' % (NZBGET_MSG_PREFIX, key, value))

        # No reason to fail if we make it this far
        return True

    def push(self, key, value, use_env=True):
        """Pushes a key/value pair to NZBGet Server

        The content pushed can be retrieved from
        self.config in scripts called after this one
        by the same key you specified in this script.
        """
        # clean key
        key = VALID_KEY_RE.sub('', key).upper()

        # Accomodate other environmental variables
        self.shared[key] = value
        if isinstance(value, bool):
            # convert boolean's to int's for consistency
            value = str(int(value))

        elif not isinstance(value, basestring):
            value = str(value)

        if use_env:
            # Save environment variable
            environ['%s%s' % (SHR_ENVIRO_ID, key)] = value

        # Alert NZBGet of variable being set
        return self._push('%s%s' % (PUSH_ENVIRO_ID, key), value)

    def push_dnzb(self, nzbheaders=None):
        """pushes meta information to NZBGet Server as DNZB content
           if no `nzbheaders` (dictionary) is defined, then the
           default one is used instead.
        """
        if nzbheaders is None:
            nzbheaders = self.nzbheaders

        if not isinstance(nzbheaders, dict):
            return False

        for k, v in nzbheaders.items():
            # Push content to NZB Server
            self.push('%s%s' % (
                SHR_ENVIRO_DNZB_ID,
                k.upper(),
            ), v.strip())

        return True

    def pull_dnzb(self):
        """pulls meta information stored in the DNZB environment
           variables and returns a dictionary
        """
        # Preload nzbheaders based on any DNZB environment variables
        return dict([(DNZB_OPTS_RE.match(k).group(1).upper(), v.strip()) \
            for (k, v) in environ.items() if DNZB_OPTS_RE.match(k)])

    def push_guess(self, guess):
        """pushes guess results to NZBGet Server. The function was
        initially intended to provide a simply way of passing content
        from guessit(), but it can be used by any dictionary with
        common elements used to identify releases
        """

        if not isinstance(guess, dict):
            # A guess is a 'dict' type, so handle the common elements
            # if set.
            return False

        for key in guess.keys():
            if key.upper() in GUESS_KEY_MAP.keys():
                # Push content to NZB Server
                self.push('%s%s' % (
                    SHR_ENVIRO_GUESS_ID,
                    key.upper(),
                ), str(guess[key]).strip())

        return True

    def pull_guess(self):
        """Retrieves guess content in a dictionary
        """
        # Fetch/Load Guess Specific Content
        return dict([
            (GUESS_KEY_MAP[SHR_GUESS_OPTS_RE.match(k).group(1)], v.strip()) \
            for (k, v) in self.shared.items() \
                if SHR_GUESS_OPTS_RE.match(k) and \
                SHR_GUESS_OPTS_RE.match(k).group(1) in GUESS_KEY_MAP])

    def parse_nzbfile(self, nzbfile, check_queued=False):
        """Parse an nzbfile specified and return just the
        meta information within the <head></head> tags

        """
        results = {}
        if not isinstance(nzbfile, basestring):
            # Simple check for nothing found
            self.logger.debug('NZB-File not defined; parse skipped.')
            return results

        if isfile(nzbfile):
            # Nothing expensive to do with i/o; just move along
            pass

        elif check_queued and isdir(dirname(nzbfile)):
            # the specified nzbfile doesn't exist, but that doesn't mean
            # it hasn't been picked up and is been picked up and nzbget
            # renamed it to .queued
            # .processed nzb files can be a result of a scan scripts handling
            # .nzb_processed are also used during the pre-scanning in scan
            #                scripts.
            # .error may be corrupted, but it does't mean we can't attempt
            #        to parse content from it.
            file_escaped = re.escape(basename(nzbfile))
            file_regex = r'^%s|%s' % (file_escaped, file_escaped) + \
                r'(' + \
                r'|\.queued|\.[0-9]+\.queued' + \
                r'|\.processed|\.[0-9]+\.processed' + \
                r'|\.nzb_processed|\.[0-9]+\.nzb_processed' + \
                r'|\.error|\.[0-9]+\.error' + \
                r')$'

            # look in the directory and extract all matches
            _filenames = self.get_files(
                search_dir=dirname(nzbfile),
                regex_filter=file_regex,
                fullstats=True,
                max_depth=1,
            )

            nzb_dir = self.get('NZBDir', None)
            if nzb_dir and abspath(nzb_dir) != abspath(dirname(nzbfile)):
                _filenames = dict(
                    _filenames.items() + self.get_files(
                        search_dir=abspath(nzb_dir),
                        regex_filter=file_regex,
                        fullstats=True,
                        max_depth=1,
                    ).items(),
                )

            if len(_filenames):
                # sort our results by access time
                _files = sorted (
                    _filenames.iterkeys(),
                    key=lambda k: (
                        # Sort by Accessed time first
                        _filenames[k]['accessed'],
                        # Then sort by Created Date
                        _filenames[k]['created'],
                        # Then sort by filename length
                        # file.nzb.2.queued > file.nzb.queued
                        len(k)),
                    reverse=True,
                )
                if self.debug:
                    for _file in _files:
                        self.logger.debug('NZB-Files located: %s (%s)' % (
                            basename(_file),
                            _filenames[_file]['accessed']\
                                .strftime('%Y-%m-%d %H:%M:%S'),
                        ))
                # Assign first file (since we've listed by access time)
                nzbfile = _files[0]
                self.logger.info(
                    'NZB-File detected: %s' % basename(nzbfile),
                )

        try:
            if LXML_TYPE == u'xml.etree.cElementTree':
                # cElementTree does not support tag= option and is not as
                # powerful as some of it's other partners since you have to
                # parse much more to get the results.  It's slower; but it
                # works:
                elements = etree.iterparse(nzbfile)

                for event, element in elements:
                    if element.tag == "{http://www.newzbin.com/DTD/2003/nzb}meta":
                        if isinstance(element.text, basestring) and \
                                element.text.strip():
                            # Only store entries with content
                            results[element.attrib['type'].upper()] = \
                                element.text.strip()
                    element.clear()
            else:
                elements = etree.iterparse(
                    nzbfile,
                    tag="{http://www.newzbin.com/DTD/2003/nzb}head",
                )

                for event, element in elements:
                    for child in element:
                        if child.tag == "{http://www.newzbin.com/DTD/2003/nzb}meta":
                            if isinstance(child.text, basestring) and \
                                    child.text.strip():
                                # Only store entries with content
                                results[child.attrib['type'].upper()] = \
                                    child.text.strip()

                    element.clear()
            self.logger.info(
                'NZBParse - NZB-File parsed %d meta entries' % len(results),
            )

        except NameError:
            self.logger.warning('NZBParse - Skipped; lxml is not installed')

        except IOError:
            self.logger.warning(
                'NZBParse - NZB-File is missing: %s' % basename(nzbfile))

        except XMLSyntaxError as e:
            if e[0] is None:
                # this is a bug with lxml in earlier versions
                # https://bugs.launchpad.net/lxml/+bug/1185701
                # It occurs when the end of the file is reached and lxml
                # simply just doesn't handle the closure properly
                # it was fixed here:
                # https://github.com/lxml/lxml/commit\
                #       /19f0a477c935b402c93395f8c0cb561646f4bdc3
                # So we can relax and return ok results here
                self.logger.info(
                    'NZBParse - NZB-File parsed %d meta entries' % \
                    len(results),
                )
            else:
                # This is the real thing
                self.logger.error(
                    'NZBParse - NZB-File is corrupt: %s' % nzbfile,
                )
                self.logger.debug(
                    'NZBParse - %s Exception %s' % (
                    LXML_TYPE,
                    str(e),
                ))

        except Exception as e:
            self.logger.error(
                'NZBParse - NZB-File is corrupt: %s' % nzbfile,
            )
            self.logger.debug(
                'NZBParse - %s Unhandled Exception %s' % (
                str(e),
                LXML_TYPE,
            ))

        return results

    def parse_nzbcontent(self, nzbcontent):
        """
        Parses nzb-content (extracted from within an NZB-File)

        This script first writes the contents of the NZB to a new file
        so that we can parse it using the parse_nzbfile() which already
        manages all the built in support for the several XML parsers
        out there.

        """
        # Temporarily write content to a temporary file
        fname = mkstemp(
            suffix='.tmp.nzb', dir=self.tempdir, text=True,
        )

        try:
            fd = open(fname)
        except:
            return {}

        try:
            fd.write(nzbcontent)

        finally:
            fd.close()

        results = self.parse_nzbfile(fname)

        try:
            unlink(fname)
        except:
            if verbose:
                self.logger.warning(
                    'Failed to removed (temporary) NZB-File: %s' % \
                    fname)

        return results

    def parse_url(self, url, default_schema='http', qsd_auth=True):
        """A function that greatly simplifies the parsing of a url
        specified by the end user.

         Valid syntaxes are:
            <schema>://<user>@<host>:<port>/<path>
            <schema>://<user>:<passwd>@<host>:<port>/<path>
            <schema>://<host>:<port>/<path>
            <schema>://<host>/<path>
            <schema>://<host>

         Argument parsing is also supported:
            <schema>://<user>@<host>:<port>/<path>?key1=val&key2=val2
            <schema>://<user>:<passwd>@<host>:<port>/<path>?key1=val&key2=val2
            <schema>://<host>:<port>/<path>?key1=val&key2=val2
            <schema>://<host>/<path>?key1=val&key2=val2
            <schema>://<host>?key1=val&key2=val2

         The function returns a simple dictionary with all of
         the parsed content within it and returns 'None' if the
         content could not be extracted.
        """

        if not isinstance(url, basestring):
            # Simple error checking
            return None

        # Default Results
        result = {
            # The username (if specified)
            'user': None,
            # The password (if specified)
            'password': None,
            # The port (if specified)
            'port': None,
            # The hostname
            'host': None,
            # The full path (query + path)
            'fullpath': None,
            # The path
            'path': None,
            # The query
            'query': None,
            # The schema
            'schema': None,
            # The schema
            'url': None,
            # The arguments passed in (the parsed query)
            # This is in a dictionary of {'key': 'val', etc }
            # qsd = Query String Dictionary
            'qsd': {}
        }

        qsdata = ''
        match = VALID_URL_RE.search(url)
        if match:
            # Extract basic results
            result['schema'] = match.group(1).lower().strip()
            host = match.group(2).strip()
            try:
                qsdata = match.group(4).strip()
            except AttributeError:
                # No qsdata
                pass
        else:
            match = VALID_HOST_RE.search(url)
            if not match:
                return None
            result['schema'] = default_schema
            host = match.group(1).strip()

        if not result['schema']:
            result['schema'] = default_schema

        if not host:
            # Invalid Hostname
            return None

        # Now do a proper extraction of data
        parsed = urlparse('http://%s' % host)

        # Parse results
        result['host'] = parsed[1].strip()
        result['fullpath'] = quote(unquote(tidy_path(parsed[2].strip())))
        try:
            # Handle trailing slashes removed by tidy_path
            if result['fullpath'][-1] not in ('/', '\\') and \
               url[-1] in ('/', '\\'):
                result['fullpath'] += url.strip()[-1]
        except IndexError:
            # No problem, there simply isn't any returned results
            # and therefore, no trailing slash
            pass

        # Parse Query Arugments ?val=key&key=val
        # while ensureing that all keys are lowercase
        if qsdata:
            result['qsd'] = dict([(k.lower().strip(), v.strip()) \
                                  for k, v in parse_qsl(
                qsdata,
                keep_blank_values=True,
                strict_parsing=False,
            )])

        if not result['fullpath']:
            # Default
            result['fullpath'] = None
        else:
            # Using full path, extract query from path
            match = VALID_QUERY_RE.search(result['fullpath'])
            if match:
                result['path'] = match.group(1)
                result['query'] = match.group(2)
                if not result['path']:
                    result['path'] = None
                if not result['query']:
                    result['query'] = None
        try:
            (result['user'], result['host']) = \
                    re.split('[\s@]+', result['host'])[:2]

        except ValueError:
            # no problem then, host only exists
            # and it's already assigned
            pass

        if result['user'] is not None:
            try:
                (result['user'], result['password']) = \
                        re.split('[:\s]+', result['user'])[:2]

            except ValueError:
                # no problem then, user only exists
                # and it's already assigned
                pass

        if qsd_auth:
            # Allow people to place a user= inline in the query string
            if result['user'] is None:
                try:
                    if 'user' in result['qsd'] and len(result['qsd']['user']):
                        result['user'] = unquote(result['qsd']['user'])

                except AttributeError:
                    pass

            if result['password'] is None:
                try:
                    if 'pass' in result['qsd'] and len(result['qsd']['pass']):
                        result['password'] = unquote(result['qsd']['pass'])

                except AttributeError:
                    pass

        try:
            (result['host'], result['port']) = \
                    re.split('[\s:]+', result['host'])[:2]

        except ValueError:
            # no problem then, user only exists
            # and it's already assigned
            pass

        if result['port']:
            try:
                result['port'] = int(result['port'])
            except (ValueError, TypeError):
                # Invalid Port Specified
                return None
            if result['port'] == 0:
                result['port'] = None

        # Re-assemble cleaned up version of the url
        result['url'] = '%s://' % result['schema']
        if isinstance(result['user'], basestring):
            result['url'] += result['user']
            if isinstance(result['password'], basestring):
                result['url'] += ':%s@' % result['password']
            else:
                result['url'] += '@'
        result['url'] += result['host']

        if result['port']:
            result['url'] += ':%d' % result['port']

        if result['fullpath']:
            result['url'] += result['fullpath']

        return result

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # set() and get() wrappers
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def unset(self, key, use_env=True, use_db=True):
        """Unset a variable, this also occurs if you call set() with a value
            set to None.
        """
        return self.set(key, None, use_env=use_env, use_db=use_db)

    def set(self, key, value, use_env=True, use_db=True):
        """Sets a key/value pair into the configuration

            if use_env is True, then content is additionaly set in the
            local environment variables.

            if use_db is True, then content is additionally set in a sqlite
            database.
        """
        # clean key
        key = VALID_KEY_RE.sub('', key).upper()
        if not key:
            return False

        if key in self.system:
            self.logger.warning('set() called using a system key (%s)' % key)

        # Save content to database
        if use_db and self.database is None and self.database_key:
            try:
                # Connect to database on first use only
                self.database = Database(
                    container=self.database_key,
                    database=join(
                        self.tempdir,
                        NZBGET_DATABASE_FILENAME,
                    ),
                    logger=self.logger,
                )

                # Database is ready to go
                if value is None:
                    # Remove Entry if it's set to None
                    self.database.unset(key=key)
                    self.logger.debug('unset(database) %s"' % key)

                elif isinstance(value, bool):
                    # Convert boolean to integer (True to 1 or False to 0)
                    self.database.set(key=key, value=int(value))
                    self.logger.debug('set(database) %s="%s"' % (
                        key,
                        int(value)),
                    )

                else:
                    self.database.set(key=key, value=value)
                    self.logger.debug('set(database) %s="%s"' % (key, value))

            except EnvironmentError:
                # Database Access Problem
                # set the dbstore to false so it isn't used anymore
                self.database = False

            except NameError:
                # Sqlite wasn't installed
                # set the dbstore to false so it isn't used anymore
                self.database = False

        elif use_db and self.database:
            # Database is ready to go
            if value is None:
                # Remove Entry if it's set to None
                self.database.unset(key=key)
                self.logger.debug('unset(database) %s"' % key)

            elif isinstance(value, bool):
                # Convert boolean to integer (change True to 1 or False to 0)
                self.database.set(key=key, value=int(value))
                self.logger.debug('set(database) %s="%s"' % (
                    key,
                    int(value),
                ))

            else:
                self.database.set(key=key, value=value)
                self.logger.debug('set(database) %s="%s"' % (key, value))

        if value is None:
            # Remove Entry if it's set to None
            # This also touches the shared dictionary as well.
            # This is intentional as it gives people who push() content
            # a way of unsettting the local variable the set (in the event
            # they should want to)
            if key in self.config:
                del self.config[key]
                self.logger.debug('unset(config) %s' % key)
            if key in self.shared:
                del self.shared[key]
                self.logger.debug('unset(shared) %s' % key)

        else:
            # Set config variables
            self.config[key] = value
            self.logger.debug('set(config) %s="%s"' % (key, value))

        if use_env:
            # convert boolean's to int's for consistency
            if value is None:
                # Remove entry
                if '%s%s' % (CFG_ENVIRO_ID, key) in environ:
                    self.logger.debug('unset(environment) %s' % key)
                    del environ['%s%s' % (CFG_ENVIRO_ID, key)]

            elif isinstance(value, bool):
                # Convert boolean to integer (change True to 1 or False to 0)
                environ['%s%s' % (CFG_ENVIRO_ID, key)] = str(int(value))
                self.logger.debug('set(environment) %s="%s"' % (
                    key,
                    str(int(value))),
                )

            else:
                environ['%s%s' % (CFG_ENVIRO_ID, key)] = str(value)
                self.logger.debug('set(environment) %s="%s"' % (key, value))

        return True

    def get(self, key, default=None, check_system=True,
            check_shared=True, use_db=True):
        """works with set() operation making it easy to retrieve set()
        content
        """

        # clean key
        key = VALID_KEY_RE.sub('', key).upper()
        if not key:
            return False

        if check_system:
            # System variables over-ride all
            value = self.system.get('%s' % key)
            if value is not None:
                # only return if a key was found
                self.logger.debug('get(system) %s="%s"' % (key, value))
                return value

        value = self.config.get('%s' % key)
        if value is not None:
            # only return if a key was found
            self.logger.debug('get(config) %s="%s"' % (key, value))
            return value

        # Fetch content from database
        if use_db and self.database is None and self.database_key:
            try:
                # Connect to database on first use only
                self.database = Database(
                    container=self.database_key,
                    database=join(
                        self.tempdir,
                        NZBGET_DATABASE_FILENAME,
                    ),
                    logger=self.logger,
                )

                # Database is ready to go
                value = self.database.get(key=key)
                if value is not None:
                    # only return if a key was found
                    self.logger.debug('get(database) %s="%s"' % (key, value))
                    return value

            except EnvironmentError:
                # Database Access Problem
                # set the dbstore to false so it isn't used anymore
                self.database = False

            except NameError:
                # Sqlite wasn't installed
                # set the dbstore to false so it isn't used anymore
                self.database = False

        elif use_db and self.database:
            value = self.database.get(key=key)
            if value is not None:
                # only return if a key was found
                self.logger.debug('get(database) %s="%s"' % (key, value))
                return value

        # If we reach here, the content wasn't found in the database
        # or the database simply isn't enabled. We now fetch attempt to
        # fetch the content from it's shared variable now

        # We still haven't found the variable requested
        if check_shared:
            # We'll look for the shared environment variable now
            # These are set by the push() methods
            value = self.shared.get('%s' % key)
            if value is not None:
                self.logger.debug('get(shared) %s="%s"' % (key, value))
                return value

        if default is not None:
            self.logger.debug('get(default) %s="%s"' % (key, str(default)))
        else:
            self.logger.debug('get(default) %s=None' % key)

        return default

    def items(self, check_system=True, check_shared=True, use_db=True):
        """
        This lets you utilize for-loops by returning you a list of keys

        """
        items = list()
        if use_db and self.database is None and self.database_key:
            try:
                # Connect to database on first use only
                self.database = Database(
                    container=self.database_key,
                    database=join(
                        self.tempdir,
                        NZBGET_DATABASE_FILENAME,
                    ),
                    logger=self.logger,
                )

                # Fetch from database first
                items = self.database.items()

            except EnvironmentError:
                # Database Access Problem
                # set the dbstore to false so it isn't used anymore
                self.database = False

            except NameError:
                # Sqlite wasn't installed
                # set the dbstore to false so it isn't used anymore
                self.database = False

        elif use_db and self.database:
            # Fetch from database first
            items = self.database.items()

        if check_shared:
            # Shared values trump any database set ones
            items = dict(items + self.shared.items()).items()

        # configuration trumps shared values
        items = dict(items + self.config.items()).items()

        if check_system:
            # system trumps all values
            items = dict(items + self.system.items()).items()

        return items

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # nzb_set() and nzb_get() wrappers
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def nzb_unset(self, key, use_env=True, use_db=True):
        """Unset a variable, this also occurs if you call nzb_set() with a
            value set to None.
        """
        return self.nzb_set(key, None, use_env=use_env, use_db=use_db)

    def nzb_set(self, key, value, use_env=True, use_db=True):
        """Sets a key/value pair into the nzb headers

            if use_env is True, then content is additionaly set in the
            local environment variables.
        """
        # clean key
        key = VALID_KEY_RE.sub('', key).upper()
        if not key:
            return False

        # Save content to database
        if use_db and self.database is None and self.database_key:
            try:
                # Connect to database on first use only
                self.database = Database(
                    container=self.database_key,
                    database=join(
                        self.tempdir,
                        NZBGET_DATABASE_FILENAME,
                    ),
                    logger=self.logger,
                )

                # Database is ready to go
                if value is None:
                    # Remove Entry if it's set to None
                    self.database.unset(key=key, category=Category.NZB)
                    self.logger.debug('nzb_unset(database) %s"' % key)

                elif isinstance(value, bool):
                    # Convert boolean to integer (True to 1 or False to 0)
                    self.database.set(
                        key=key, value=int(value), category=Category.NZB)
                    self.logger.debug('nzb_set(database) %s="%s"' % (
                        key,
                        int(value)),
                    )

                else:
                    self.database.set(
                        key=key, value=value, category=Category.NZB)
                    self.logger.debug(
                        'nzb_set(database) %s="%s"' % (key, value))

            except EnvironmentError:
                # Database Access Problem
                # set the dbstore to false so it isn't used anymore
                self.database = False

            except NameError:
                # Sqlite wasn't installed
                # set the dbstore to false so it isn't used anymore
                self.database = False

        elif use_db and self.database:
            # Database is ready to go
            if value is None:
                # Remove Entry if it's set to None
                self.database.unset(key=key, category=Category.NZB)
                self.logger.debug('nzb_unset(database) %s"' % key)

            elif isinstance(value, bool):
                # Convert boolean to integer (change True to 1 or False to 0)
                self.database.set(
                    key=key,
                    value=int(value),
                    category=Category.NZB,
                )
                self.logger.debug('nzb_set(database) %s="%s"' % (
                    key,
                    int(value),
                ))

            else:
                self.database.set(key=key, value=value, category=Category.NZB)
                self.logger.debug('nzb_set(database) %s="%s"' % (key, value))

        if value is None:
            # Remove Entry if it's set to None
            # This also touches the shared dictionary as well.
            # This is intentional as it gives people who push() content
            # a way of unsettting the local variable the set (in the event
            # they should want to)
            if key in self.nzbheaders:
                del self.nzbheaders[key]
                self.logger.debug('nzb_unset(config) %s' % key)

            # Remove entry from environment too
            if use_env and '%s%s%s' % (
                    CFG_ENVIRO_ID,
                    SHR_ENVIRO_DNZB_ID,
                    key) in environ:
                del environ['%s%s%s' % (
                    SHR_ENVIRO_ID,
                    SHR_ENVIRO_DNZB_ID,
                    key)]
                self.logger.debug('nzb_unset(environment) %s' % key)
        else:
            # Set config variables
            self.nzbheaders[key] = value

            self.logger.debug('nzb_set(config) %s="%s"' % (key, str(value)))

            if use_env:
                if isinstance(value, bool):
                    # Convert boolean to integer (True to 1 or False to 0)
                    value = str(int(value))

                elif not isinstance(value, basestring):
                    value = str(value)

                environ['%s%s%s' % (
                    SHR_ENVIRO_ID,
                    SHR_ENVIRO_DNZB_ID,
                    key)] = value

                self.logger.debug('nzb_set(environment) %s="%s"' % (
                    key, value),
                )

        return True

    def nzb_get(self, key, default=None, use_db=True):
        """works with nzb_set() operation making it easy to retrieve
        content
        """
        # clean key
        key = VALID_KEY_RE.sub('', key).upper()
        if not key:
            return False

        value = self.nzbheaders.get(key)
        if value is not None:
            # only return if a key was found
            self.logger.debug('nzb_get(config) %s="%s"' % (key, value))
            return value

        # Fetch content from database
        if use_db and self.database is None and self.database_key:
            try:
                # Connect to database on first use only
                self.database = Database(
                    container=self.database_key,
                    database=join(
                        self.tempdir,
                        NZBGET_DATABASE_FILENAME,
                    ),
                    logger=self.logger,
                )

                # Database is ready to go
                value = self.database.get(key=key, category=Category.NZB)
                if value is not None:
                    # only return if a key was found
                    self.logger.debug(
                        'nzb_get(database) %s="%s"' % (key, value))
                    return value

            except EnvironmentError:
                # Database Access Problem
                # set the dbstore to false so it isn't used anymore
                self.database = False

            except NameError:
                # Sqlite wasn't installed
                # set the dbstore to false so it isn't used anymore
                self.database = False

        elif use_db and self.database:
            value = self.database.get(key=key, category=Category.NZB)
            if value is not None:
                # only return if a key was found
                self.logger.debug('nzb_get(database) %s="%s"' % (key, value))
                return value

        if default is not None:
            self.logger.debug('nzb_get(default) %s="%s"' % (key, str(default)))
        else:
            self.logger.debug('nzb_get(default) %s=None' % key)

        return default

    def nzb_items(self, use_db=True):
        """
        This lets you utilize for-loops by returning you a list of keys

        """
        items = list()
        if use_db and self.database is None and self.database_key:
            try:
                # Connect to database on first use only
                self.database = Database(
                    container=self.database_key,
                    database=join(
                        self.tempdir,
                        NZBGET_DATABASE_FILENAME,
                    ),
                    logger=self.logger,
                )

                # Fetch from database first
                items = self.database.items()

            except EnvironmentError:
                # Database Access Problem
                # set the dbstore to false so it isn't used anymore
                self.database = False

            except NameError:
                # Sqlite wasn't installed
                # set the dbstore to false so it isn't used anymore
                self.database = False

        elif use_db and self.database:
            # Fetch from database first
            items = self.database.items(category=Category.NZB)

        # configuration trumps shared values
        items = dict(items + self.nzbheaders.items()).items()

        return items

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Sanity
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def _sanity_check(self):
        """Sanity checks on a base class are always successful
        """
        return True

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Validatation
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def validate(self, *args, **kwargs):
        """A system wrapper to _validate() allowing a mult-script environment
        """
        # Default
        core_function = self._validate
        if hasattr(self, '%s_%s' % (self.script_mode, 'validate')):
            core_function = getattr(
                self, '%s_%s' % (self.script_mode, 'validate'))

        # Execute
        return core_function(*args, **kwargs)

    def _validate(self, keys=None, min_version=11, *args, **kwargs):
        """validate against environment variables
        """

        # Initialize a global variable, we run through the entire function
        # so all errors can be caught to make it easier for debugging
        is_okay = True

        if keys:
            missing = []
            if isinstance(keys, basestring):
                keys = self.parse_list(keys)

            missing = [
                k for k in keys \
                        if not (k.upper() in self.system \
                             or k.upper() in self.config)
            ]

            if missing:
                self.logger.error('Validation - Directives not set: %s' % \
                      ', '.join(missing))
                is_okay = False

        # We should fail if the temporary directory is not accessible
        if not access(self.tempdir, (R_OK|W_OK|X_OK)):
            self.logger.error(
                'Validation - Temporary directory is not accessible %s' % \
                self.tempdir,
            )
            is_okay = False

        if self.script_mode == SCRIPT_MODE.NONE:
            # Nothing more to process if not utilizaing
            # NZBGet environment
            return is_okay

        if min_version > self.version:
            self.logger.error(
                'Validation - detected version %d, (min expected=%d)' % (
                    self.version, min_version)
            )
            is_okay = False

        # Always a bad thing if SCRIPTDIR doesn't work since that is
        # introduced in v11 (the minimum version we support)
        if not 'SCRIPTDIR' in self.system:
            self.logger.error(
                'Validation - (<v11) Directive not set: %s' % 'SCRIPTDIR',
            )
            is_okay = False

        return is_okay

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Health Check
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def health_check(self, *args, **kwargs):
        """A system wrapper to _health_check() allowing a mult-script environment
        """
        # Default
        core_function = self._health_check
        if hasattr(self, '%s_%s' % (self.script_mode, 'health_check')):
            core_function = getattr(
                self, '%s_%s' % (self.script_mode, 'health_check'))

        # Execute
        return core_function(*args, **kwargs)

    def _health_check(self, *args, **kwargs):
        """Health Check
        """
        return True

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # API Factory
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def api_connect(self, user=None, password=None,
                    host=None, port=None, secure=None, reset=False):
        """Configures an API connection
        """
        if reset:
            # Reset
            self.api = None

        # If we're already connected; then there is nothing more to do
        if self.api is not None:
            return True

        # if we reach here, we have enough data to build an RCP connection
        if host is None:
            host = self.system.get('ControlIP', '127.0.0.1')

        if host == "0.0.0.0":
            host = "127.0.0.1"

        #Build URL
        if secure is None:
            # Secure only works if the KeyFiles exist too
            # Otherwise, setting this to True means nothing
            secure = self.parse_bool(self.get('SecureControl', False))
            cert = self.get('SecureCert', '')
            key = self.get('SecureKey', '')

            # Update Flag
            secure = (secure and isfile(cert) and isfile(key))

        if secure:
            xmlrpc_url = 'https://'
            if port is None:
                port = self.get('SecurePort', '6791')
        else:
            if port is None:
                port = self.get('ControlPort', '6789')

            xmlrpc_url = 'http://'

        if user is None:
            user = self.get('ControlUsername', '')

        if password is None:
            password = self.get('ControlPassword', '')

        if user and password:
            xmlrpc_url += '%s:%s@' % (user, password)

        xmlrpc_url += '%s:%s/xmlrpc' % ( \
            host,
            str(port),
        )

        # Establish a connection to the server; since most NZBGet secure
        # servers can't verified since they're hosted internally, we set
        # the CERT_NONE flag.

        # Future TODO: make this an option for those who want to verify
        # the host.
        try:
            # Python >= 2.7.9
            context = ssl._create_unverified_context()
            try:
                self.api = ServerProxy(
                    xmlrpc_url,
                    verbose=False,
                    use_datetime=True,
                    context=context,
                )
            except:
                self.logger.debug('API connection failed @ %s' % xmlrpc_url)
                return False

        except AttributeError:
            # Python < 2.7.9
            transport = SafeTransport(
                use_datetime=True,
                context=context,
            )

            try:
                self.api = ServerProxy(
                    xmlrpc_url,
                    verbose=False,
                    use_datetime=True,
                    transport=transport,
                )

            except:
                self.logger.debug('API connection failed @ %s' % xmlrpc_url)
                return False

            self.logger.debug('API connected @ %s' % xmlrpc_url)

        return True

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Retrieve System Logs
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def get_logs(self, max_lines=1000, oldest_first=False):
        """
        Returns log entries (via the API)
        """
        if not self.api_connect():
            # Could not connect
            return None

        try:
            logs = self.api.postqueue(10000)
            logs = logs[0]['Log']
        except (IndexError, KeyError):
            # No logs
            return []

        # Return a simple ordered list of strings
        if oldest_first == True:
            return list(reversed([ '%s - %s - %s' % (
                datetime.fromtimestamp(int(entry['Time']))\
                        .strftime('%Y-%m-%d %H:%M:%S'),
                entry['Kind'], entry['Text'].strip(),
            ) for entry in logs ]))[:max_lines]

        # If we reach here, we are to return the contents
        # where the newest item is the first entry in
        # the list; under normal circumstances, this is the
        # order that the server automatically returns content in
        return [ '%s - %s - %s' % (
            datetime.fromtimestamp(int(entry['Time']))\
                    .strftime('%Y-%m-%d %H:%M:%S'),
            entry['Kind'], entry['Text'].strip(),
        ) for entry in logs ][max_lines:]


    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Add NZB File to Queue
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def add_nzb(self, filename, content=None, category=None,
                priority=PRIORITY.NORMAL):
        """Simply add's an NZB file to NZBGet (via the API)
        """
        if not self.api_connect():
            # Could not connect
            return None

        # Defaults
        add_to_top = False
        add_paused = False
        dup_key = ''
        dup_score = 0
        dup_mode = NZBGetDuplicateMode.FORCE

        if content is None:
            if not category:
                # Verify content is an NZB-File
                meta = self.parse_nzbfile(filename)
                category = unescape_xml(meta.get('CATEGORY', '').strip())

            try:
                f = open(filename, "r")

            except:
                self.logger.debug('API:NZB-File Could not open: %s' % filename)
                return False

            try:
                content = f.read()

            except:
                self.logger.debug('API:NZB-File Could not read: %s' % filename)
                return False

            f.close()

        elif not category:
            # We have content already loaded; We need to convert it into an
            # XML object for parsing
            meta = self.parse_nzbcontent(content)
            category = unescape_xml(meta.get('CATEGORY', '').strip())

        # Encode content
        b64content = standard_b64encode(content)

        try:
            return self.api.append(
                filename,
                b64content,
                category,
                priority,
                add_to_top,
                add_paused,
                dup_key,
                dup_score,
                dup_mode,
            )

        except:
            # Try to capture error
            exc_type, exc_value, exc_traceback = exc_info()
            lines = traceback.format_exception(
                     exc_type, exc_value, exc_traceback)
            if self.script_mode != SCRIPT_MODE.NONE:
                # NZBGet Mode enabled
                for line in lines:
                    self.logger.error(line)
            else:
                # Display error as is
                self.logger.error('API:NZB-File append() Exception:\n%s' % \
                    ''.join('  ' + line for line in lines))

            return False
        return True

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # File Retrieval
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def get_files(self, *args, **kwargs):
        """A system wrapper to _get_files() allowing a mult-script environment
        """

        # Default
        core_function = self._get_files
        if self.script_mode is not None and \
           hasattr(self, '%s_%s' % (self.script_mode, 'get_files')):
            core_function = getattr(
                self, '%s_%s' % (self.script_mode, 'get_files'))

        # Execute
        return core_function(*args, **kwargs)

    def _get_files(self, search_dir, regex_filter=None, prefix_filter=None,
                    suffix_filter=None, fullstats=False,
                   followlinks=False, min_depth=None, max_depth=None,
                  case_sensitive=False, skip_directories=SKIP_DIRECTORIES,
                  *args, **kwargs):
        """Returns a dict object of the files found in the download
           directory. You can additionally pass in filters as a list or
           string) to filter the results returned.

              ex:
              {
                 '/full/path/to/file.mkv': {
                     'basename': 'file.mkv',
                     'dirname': '/full/path/to',
                     # identify the filename (without applied extension)
                     'filename': 'file',
                     # always tolower() applied to:
                     'extension': 'mkv',

                     # If fullstatus == True then the following additional
                     # content is provided.

                     # filesize is in bytes
                     'filesize': 10000,
                     # accessed date
                     'accessed': datetime(),
                     # created date
                     'created': datetime(),
                     # created date
                     'modified': datetime(),
                 }
              }

        """

        # Internal Tracking of Directory Depth
        current_depth = kwargs.get('__current_depth', 1)

        # Build file list
        files = {}
        if isinstance(search_dir, (list, tuple)):
            for _dir in search_dir:
                # use recursion to build a master (unique) list
                files = dict(files.items() + self._get_files(
                    search_dir=_dir,
                    regex_filter=regex_filter,
                    prefix_filter=prefix_filter,
                    suffix_filter=suffix_filter,
                    fullstats=fullstats,
                    followlinks=followlinks,
                    min_depth=min_depth,
                    max_depth=max_depth,
                    case_sensitive=case_sensitive,
                    skip_directories=skip_directories,
                    # Internal Current Directory Depth tracking
                    __current_depth=current_depth,
                ).items())
            return files

        elif not isinstance(search_dir, basestring):
            # Unsupported
            return {}

        # Change all filters strings lists (if they aren't already)
        if regex_filter is None:
            regex_filter = tuple()
        if isinstance(regex_filter, basestring):
            regex_filter = (regex_filter,)
        elif isinstance(regex_filter, re._pattern_type):
            regex_filter = (regex_filter,)
        if suffix_filter is None:
            suffix_filter = tuple()
        if isinstance(suffix_filter, basestring):
            suffix_filter = (suffix_filter, )
        if prefix_filter is None:
            prefix_filter = tuple()
        if isinstance(prefix_filter, basestring):
            prefix_filter = (prefix_filter, )

        # clean prefix list
        if prefix_filter:
            prefix_filter = self.parse_list(prefix_filter)

        # clean up suffix list
        if suffix_filter:
            suffix_filter = self.parse_list(suffix_filter)

        # Precompile any defined regex definitions
        if regex_filter:
            _filters = []
            for f in regex_filter:
                if not isinstance(f, re._pattern_type):
                    flags = re.MULTILINE
                    if not case_sensitive:
                        flags |= re.IGNORECASE
                    try:
                        _filters.append(re.compile(f, flags=flags))
                        self.logger.vdebug('Compiled regex "%s"' % f)
                    except:
                        self.logger.error(
                            'Invalid regular expression: "%s"' % f,
                        )
                        return {}
                else:
                    # precompiled already
                    _filters.append(f)
            # apply
            regex_filter = _filters

        if current_depth == 1:
            # noise reduction; only display this notice once (but not on
            # each recursive call)
            self.logger.debug("get_files('%s') with %d filter(s)" % (
                search_dir,
                len(prefix_filter) + len(suffix_filter) + len(regex_filter),
            ))

        if not dirname(search_dir):
            search_dir = join(self.curdir, search_dir)

        if isfile(search_dir):
            fname = basename(search_dir)
            dname = abspath(dirname(search_dir))
            filtered = False
            if regex_filter:
                filtered = True
                for regex in regex_filter:
                    if regex.search(fname):
                        self.logger.debug('Allowed %s (regex)' % fname)
                        filtered = False
                        break
                if filtered:
                    self.logger.vdebug('Denied %s (regex)' % fname)

            if not filtered and prefix_filter:
                filtered = True
                for prefix in prefix_filter:
                    if case_sensitive:
                        if fname[0:len(prefix)] == prefix:
                            self.logger.debug('Allowed %s (prefix)' % fname)
                            filtered = False
                            break
                    else:
                        # Not Case Sensitive
                        if fname[0:len(prefix)].lower() == prefix.lower():
                            self.logger.debug('Allowed %s (prefix)' % fname)
                            filtered = False
                            break
                if filtered:
                    self.logger.vdebug('Denied %s (prefix)' % fname)

            if not filtered and suffix_filter:
                filtered = True
                for suffix in suffix_filter:
                    if case_sensitive:
                        if fname[-len(suffix):] == suffix:
                            self.logger.vdebug('Allowed %s (suffix)' % fname)
                            filtered = False
                            break
                    else:
                        # Not Case Sensitive
                        if fname[-len(suffix):].lower() == suffix.lower():
                            self.logger.debug('Allowed %s (suffix)' % fname)
                            filtered = False
                            break
                if filtered:
                    self.logger.vdebug('Denied %s (suffix)' % fname)

            if filtered:
                # File does not meet implied filters
                return {}

            # Update our search_dir
            search_dir = join(dname, fname)

            # If we reach here, we can prepare a file using the data
            # we fetch
            _file = {
                search_dir: {
                'basename': fname,
                'dirname': dname,
                'extension': splitext(basename(fname))[1].lower(),
                'filename': splitext(basename(fname))[0],
                }
            }
            if fullstats:
                # Extend file information
                try:
                    stat_obj = stat(search_dir)
                except OSError:
                    # File was not found or recently removed
                    del files[search_dir]
                    self.logger.warning(
                        'The file %s became inaccessible' % fname,
                    )
                    return {}
                try:
                    _file[search_dir]['modified'] = \
                        datetime.fromtimestamp(stat_obj[ST_MTIME])
                except ValueError:
                    _file[search_dir]['modified'] = \
                        datetime(1980, 1, 1, 0, 0, 0, 0)
                try:
                    _file[search_dir]['accessed'] = \
                        datetime.fromtimestamp(stat_obj[ST_ATIME])
                except ValueError:
                    _file[search_dir]['accessed'] = \
                        datetime(1980, 1, 1, 0, 0, 0, 0)
                try:
                    _file[search_dir]['created'] = \
                        datetime.fromtimestamp(stat_obj[ST_CTIME])
                except ValueError:
                    _file[search_dir]['created'] = \
                        datetime(1980, 1, 1, 0, 0, 0, 0)

                _file[search_dir]['filesize'] = stat_obj[ST_SIZE]
            return _file

        elif not isdir(search_dir):
            return {}

        # For depth matching
        search_dir = normpath(search_dir)
        current_depth += 1
        self.logger.vdebug('Directory depth offset %d' % current_depth)

        # Get Directory entries
        dirents = [ d for d in listdir(search_dir) \
                  if d not in ('..', '.') ]

        for dirent in dirents:
            # Store Path
            fullpath = join(search_dir, dirent)

            ## Iterate over entries and process the files
            #for dname, dnames, fnames in walk(
            #search_dir, followlinks=followlinks):

            if isdir(fullpath):
                # Min and Max depth handling
                if max_depth and max_depth < current_depth:
                    continue
                if min_depth and min_depth > current_depth:
                    continue

                # Handle skip_directory directive
                if (isinstance(skip_directories, list) and \
                        dirent in skip_directories) or \
                        (skip_directories and dirent in SKIP_DIRECTORIES):
                    self.logger.vdebug(
                        'Skipping directory %s' % dirent,
                    )
                    continue

                if not followlinks and islink(fullpath):
                    # honor followlinks
                    self.logger.vdebug(
                        'Skipping (link) directory %s' % dirent,
                    )
                    continue

                # use recursion to build a master (unique) list
                files = dict(files.items() + self._get_files(
                    search_dir=fullpath,
                    regex_filter=regex_filter,
                    prefix_filter=prefix_filter,
                    suffix_filter=suffix_filter,
                    fullstats=fullstats,
                    followlinks=followlinks,
                    min_depth=min_depth,
                    max_depth=max_depth,
                    case_sensitive=case_sensitive,
                    skip_directories=skip_directories,
                    # Internal Current Directory Depth tracking
                    __current_depth=current_depth,
                ).items())
                continue

            elif not isfile(fullpath):
                self.logger.vdebug(
                    'Skipping unknown %s' % dirent,
                )
                continue

            filtered = False

            # Apply filters to match filed
            if regex_filter:
                filtered = True
                for regex in regex_filter:
                    if regex.search(dirent):
                        self.logger.debug('Allowed %s (regex)' % dirent)
                        filtered = False
                        break
                if filtered:
                    self.logger.vdebug('Denied %s (regex)' % dirent)
                    continue

            if not filtered and prefix_filter:
                filtered = True
                for prefix in prefix_filter:
                    if dirent[0:len(prefix)] == prefix:
                        self.logger.debug('Allowed %s (prefix)' % dirent)
                        filtered = False
                        break
                if filtered:
                    self.logger.vdebug('Denied %s (prefix)' % dirent)
                    continue

            if not filtered and suffix_filter:
                filtered = True
                for suffix in suffix_filter:
                    if dirent[-len(suffix):] == suffix:
                        self.logger.debug('Allowed %s (suffix)' % dirent)
                        filtered = False
                        break
                if filtered:
                    self.logger.vdebug('Denied %s (suffix)' % dirent)
                    continue

            # If we reach here, we store the file found
            files[fullpath] = {
                'basename': dirent,
                'dirname': search_dir,
                'extension': splitext(basename(dirent))[1].lower(),
                'filename': splitext(basename(dirent))[0],
            }

            if fullstats:
                # Extend file information
                try:
                    stat_obj = stat(fullpath)
                except OSError:
                    # File was not found or recently removed
                    del files[fullpath]
                    self.logger.warning(
                        'The file %s became inaccessible' % dirent,
                    )
                    continue

                try:
                    files[fullpath]['modified'] = \
                        datetime.fromtimestamp(stat_obj[ST_MTIME])
                except ValueError:
                    files[fullpath]['modified'] = \
                            datetime(1980, 1, 1, 0, 0, 0, 0)
                try:
                    files[fullpath]['accessed'] = \
                        datetime.fromtimestamp(stat_obj[ST_ATIME])
                except ValueError:
                    files[fullpath]['accessed'] = \
                            datetime(1980, 1, 1, 0, 0, 0, 0)
                try:
                    files[fullpath]['created'] = \
                        datetime.fromtimestamp(stat_obj[ST_CTIME])
                except ValueError:
                    files[fullpath]['created'] = \
                            datetime(1980, 1, 1, 0, 0, 0, 0)

                files[fullpath]['filesize'] = stat_obj[ST_SIZE]
        # Return all files
        return files

    def run(self, *args, **kwargs):
        """The intent is this is the script you run from within your script
        after overloading the main() function of your class
        """
        # Default
        main_function = self.main

        # Determine the function to use
        # multi-scripts need to define a
        #  - postprocess_main()
        #  - scan_main()
        #  - scheduler_main()
        #  - queue_main()
        #  - feed_main()
        #  - action_<configname>()

        if self.script_mode is SCRIPT_MODE.CONFIG_ACTION:
            # Line up our action_<name>() script
            main_function = self._config_action

        # otherwise main() is executed
        elif hasattr(self, '%s_%s' % (self.script_mode, 'main')):
            main_function = getattr(
                self, '%s_%s' % (self.script_mode, 'main'))

        try:
            exit_code = main_function(*args, **kwargs)

        except NZBGetExitException, e:
            # One of our own exceptions
            exit_code = e.code

        except:
            # Try to capture error
            exc_type, exc_value, exc_traceback = exc_info()
            lines = traceback.format_exception(
                     exc_type, exc_value, exc_traceback)
            if self.script_mode != SCRIPT_MODE.NONE:
                # NZBGet Mode enabled
                for line in lines:
                    self.logger.error(line)
            else:
                # Display error as is
                self.logger.error('Fatal Exception:\n%s' % \
                    ''.join('  ' + line for line in lines))
            exit_code = EXIT_CODE.FAILURE

        # Handle tidying of PID-File if it exists
        if isinstance(self.pidfile, basestring):
            if self.is_unique_instance(die_on_fail=False, verbose=False):
                # It is our PID-File; so do our cleanup
                try:
                    unlink(self.pidfile)
                    self.logger.info(
                        'Removed PID-File: %s' % self.pidfile)
                except:
                    self.logger.warning(
                        'Failed to remove PID-File: %s' % self.pidfile)
                    pass

        # Simplify return codes for those who just want to use
        # True/False/None
        if exit_code is None:
            exit_code = EXIT_CODE.NONE

        elif exit_code is True:
            exit_code = EXIT_CODE.SUCCESS

        elif exit_code is False:
            exit_code = EXIT_CODE.FAILURE

        # Otherwise Be specific and if the code is not a valid one
        # then simply swap it with the FAILURE one
        if exit_code not in EXIT_CODES:
            self.logger.error(
                'The exit code %d is not valid, ' % exit_code + \
                'changing response to a failure (%d).' % (EXIT_CODE.FAILURE),
            )
            exit_code = EXIT_CODE.FAILURE
        self.logger.debug(
           'Exiting with return code: %d' % exit_code)
        return exit_code

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Simplify Parsing
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def parse_list(self, *args):
        """
        Take a string list and break it into a delimited
        list of arguments. This funciton also supports
        the processing of a list of delmited strings and will
        always return a unique set of arguments. Duplicates are
        always combined in the final results.

        You can append as many items to the argument listing for
        parsing.

        Hence: parse_list('.mkv, .iso, .avi') becomes:
            ['.mkv', '.iso', '.avi']

        Hence: parse_list('.mkv, .iso, .avi', ['.avi', '.mp4']) becomes:
            ['.mkv', '.iso', '.avi', '.mp4']

        The parsing is very forgiving and accepts spaces, slashes, commas
        semicolons, and pipes as delimiters
        """

        result = []
        for arg in args:
            if isinstance(arg, basestring):
                result += re.split(STRING_DELIMITERS, arg)

            elif isinstance(arg, (list, tuple)):
                for _arg in arg:
                    if isinstance(arg, basestring):
                        result += re.split(STRING_DELIMITERS, arg)
                    # A list inside a list? - use recursion
                    elif isinstance(_arg, (list, tuple)):
                        result += self.parse_list(_arg)
                    else:
                        # Convert whatever it is to a string and work with it
                        result += self.parse_list(str(_arg))
            else:
                # Convert whatever it is to a string and work with it
                result += self.parse_list(str(arg))

        # apply as well as make the list unique by converting it
        # to a set() first. filter() eliminates any empty entries
        return filter(bool, list(set(result)))

    def parse_path_list(self, *args):
        """
        Very similar to the parse_list() however this parses a listing of
        provided directories.  The difference is that white space is
        treated a bit more strictly since directory paths can contain
        spaces in them. Trailing (back)slashes are always removed from
        results. Duplicates are always combined in final results.

        Hence: parse_path_list('C:\\test dir\\, D:\\test2') becomes:
            [ 'C:\\test dir', D:\\test2' ]

        Hence: parse_path_list('C:\\test dir\\, D:\\test2',
            [ 'H:\\test 4', 'C:\\test dir', 'D:\\test2' ]
        becomes:
            [ 'C:\\test dir', D:\\test2', 'H:\\test 4' ]
        """

        if not hasattr(self, '_path_delimiter_re'):
            # Compile for speed on first pass though
            self._path_delimiter_re = re.compile(PATH_DELIMITERS)

            # Compile for speed on first pass though
            # This separates D:\entry E:\entry2 by forcing a delimiter
            # that will be caught with the _path_delimiter_re is ran
            # afterwards
            self._path_win_drive_re = re.compile(
                r'[\s,\|]+([A-Za-z]):+(%s)%s*' % (
                    ESCAPED_WIN_PATH_SEPARATOR,
                    ESCAPED_WIN_PATH_SEPARATOR,
            ))

            self._path_win_re = re.compile(
                r'[%s]+[\s,\|]+([%s]{2}%s*|[^%s])' % (
                    ESCAPED_WIN_PATH_SEPARATOR,
                    ESCAPED_WIN_PATH_SEPARATOR,
                    ESCAPED_WIN_PATH_SEPARATOR,
                    ESCAPED_WIN_PATH_SEPARATOR,
            ))

            self._path_winnw_re = re.compile(
                r'[\s,\|]+(%s%s)%s*' % (
                    ESCAPED_WIN_PATH_SEPARATOR,
                    ESCAPED_WIN_PATH_SEPARATOR,
                    ESCAPED_WIN_PATH_SEPARATOR,
            ))

        result = []
        for arg in args:
            if isinstance(arg, basestring):
                cleaned = self._path_delimiter_re.sub('|/', tidy_path(arg))
                cleaned = self._path_win_re.sub('|\\1', cleaned)
                cleaned = self._path_winnw_re.sub('|\\1', cleaned)
                cleaned = self._path_win_drive_re.sub('|\\1:\\2', cleaned)
                result += re.split('[,|]+', cleaned)

            elif isinstance(arg, (list, tuple)):
                for _arg in arg:
                    if isinstance(_arg, basestring):
                        cleaned = self._path_delimiter_re.sub('|', tidy_path(_arg))
                        cleaned = self._path_win_re.sub('|\\1', cleaned)
                        cleaned = self._path_winnw_re.sub('|\\1', cleaned)
                        cleaned = self._path_win_drive_re.sub('|\\1:\\2', cleaned)
                        result += re.split('[,|]+', cleaned)

                    # A list inside a list? - use recursion
                    elif isinstance(_arg, (list, tuple)):
                        result += self.parse_path_list(_arg)
                    else:
                        # unsupported content
                        continue
            else:
                # unsupported content (None, bool's, int's, floats, etc)
                continue

        # apply as well as make the list unique by converting it
        # to a set() first. filter() eliminates any empty entries
        return filter(bool, list(set([tidy_path(p) for p in result])))

    def parse_bool(self, arg, default=False):
        """
        NZBGet uses 'yes' and 'no' as well as other strings such
        as 'on' or 'off' etch to handle boolean operations from
        it's control interface.

        This method can just simplify checks to these variables.

        If the content could not be parsed, then the default is
        returned.
        """

        if isinstance(arg, basestring):
            # no = no - False
            # of = short for off - False
            # 0  = int for False
            # fa = short for False - False
            # f  = short for False - False
            # n  = short for No or Never - False
            # ne  = short for Never - False
            # di  = short for Disable(d) - False
            # de  = short for Deny - False
            if arg.lower()[0:2] in ('de', 'di', 'ne', 'f', 'n', 'no', 'of', '0', 'fa'):
                return False
            # ye = yes - True
            # on = short for off - True
            # 1  = int for True
            # tr = short for True - True
            # t  = short for True - True
            # al = short for Always (and Allow) - True
            # en  = short for Enable(d) - True
            elif arg.lower()[0:2] in ('en', 'al', 't', 'y', 'ye', 'on', '1', 'tr'):
                return True
            # otherwise
            return default

        # Handle other types
        return bool(arg)

    def action_sanity_check(self):
        """Sanity checking to ensure this really is a Config Test
        """

        if TEST_COMMAND not in environ:
            # Nothing more to do
            return False

        # Extract our content
        command = environ.get(TEST_COMMAND)
        if not command:
            # Nothing more to do
            return False

        if hasattr(self, '%s_%s' % (SCRIPT_MODE.CONFIG_ACTION, command)):
            self._config_action = getattr(self, '%s_%s' % (
                SCRIPT_MODE.CONFIG_ACTION,
                command,
            ))

            if not callable(self._config_action):
                self.logger.debug('The internal script variable '\
                    '%s is not a function (type=%s)' % (
                        (SCRIPT_MODE.CONFIG_ACTION, command()),
                        type(self._config_action),
                ))

                # Reset it's variable
                self._config_action = None
                return False

            # We're set
            return True

        elif hasattr(self, '%s_%s' % (
            SCRIPT_MODE.CONFIG_ACTION, command.lower())):
            self._config_action = getattr(self, '%s_%s' % (
                SCRIPT_MODE.CONFIG_ACTION,
                command.lower(),
            ))

            if not callable(self._config_action):
                self.logger.debug('The internal script variable '\
                    '%s is not a function (type=%s)' % (
                        (SCRIPT_MODE.CONFIG_ACTION, command.lower()),
                        type(self._config_action),
                ))
                # Reset it's variable
                self._config_action = None
                return False

            # We're set
            return True

        self.logger.warning('The developer of this script did not'\
            ' create test mapping to this command.')
        return False

    def detect_mode(self):
        """
        Attempt to detect the script mode based on environment variables
        The modes are defied at the top and are determined by a certain
        set of global variables defined.
        """
        if self.script_mode is not None:
            return self.script_mode

        if len(self.script_dict):
            self.logger.vdebug('Detecting possible script mode from: %s' % \
                         ', '.join(self.script_dict.keys()))

        if len(self.script_dict.keys()):
            for k in [ v for v in SCRIPT_MODES \
                      if v in self.script_dict.keys() + [
                              SCRIPT_MODE.CONFIG_ACTION, SCRIPT_MODE.NONE,]]:
                if hasattr(self, '%s_%s' % (k, 'sanity_check')):
                    if getattr(self, '%s_%s' % (k, 'sanity_check'))():
                        self.script_mode = k
                        if self.script_mode != SCRIPT_MODE.NONE:
                            self.logger.vdebug(
                                'Script Mode: %s' % self.script_mode.upper())
                            return self.script_mode

        self.logger.vdebug('Script Mode: STANDALONE')
        self.script_mode = SCRIPT_MODE.NONE

        return self.script_mode

    def signal_quit(self, signum, frame):
        """
        Quit signal received
        """
        # Determine the function to use
        # multi-scripts need to define a
        #  - postprocess_signal_quit()
        #  - scan_signal_quit()
        #  - scheduler_signal_quit()
        #  - queue_signal_quit()
        #  - feed_signal_quit()
        #
        # otherwise we go ahead and gracefully exit
        exit_code = 1
        if hasattr(self, '%s_%s' % (self.script_mode, 'signal_quit')):
            signal_function = getattr(
                self, '%s_%s' % (self.script_mode, 'signal_quit'))
            exit_code = signal_function(*args, **kwargs)

        self.logger.info('Quit Signal Received; Exiting.')
        self.logger.debug('%d Signal Received.' % signum)
        raise NZBGetExitException

    def main(self, *args, **kwargs):
        """Write all of your code here making uses of your functions while
        returning your exit code
        """
        if not self.validate():
            # We're running a version < v11
            return False

        return True

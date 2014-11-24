# -*- encoding: utf-8 -*-
#
# A simple SQLite (3) Database wrapper for shared NZBGet transactions
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
This script will allow a common gateway between scripts that require
interaction with one another. It sets up a simple hash table like system
that can be used as a method of passing variables around using the
get() and set() operation.

It's initialized by setting up a container object. This keeps all set()
get() operations limited to what is set by the container itself.

NZBScripts should not be dependant on one another.  The intention
is not to use this to set a variable so it can be retrieved late by another
script. However setting a variable in advance that another script needs
to preform the same proceedure to get to can be grealy simplified by sharing
cpu power by just sharing your results in advance.
"""
import sqlite3
import re
from datetime import datetime
from datetime import timedelta
from os.path import isfile
from os.path import dirname
from os.path import isdir
from os import unlink
from os import makedirs

from Logger import init_logger
from Logger import destroy_logger
from logging import Logger

# This should always be set to the current database version
NZBGET_DATABASE_VERSION = 1

# In seconds, we identify how long to let content linger in the
# database for before it's purged (no sense letting content grow)
# below sets the timer for 12 hours.  This database contains just transient
# information; there is no need to keep content longer then this.
PURGE_AGE = 60 * 60 * 12

# Format required to correctly query and handle SQLite Dates
SQLITE_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

NZBGET_SCHEMA = {
  1: [
     # Lookup just contains static content and VSPs used by the database
     # and it's handling of data.  You should not write content here. this
     # is just reserved for internal operations
     "CREATE TABLE lookup (key TEXT PRIMARY KEY, value TEXT)",
     # Init base version of zero (0), the _build_schema takes care
     # of updating this value
     "INSERT INTO lookup (key, value) VALUES ('SCHEMA_VERSION', '0')",
     "INSERT INTO lookup (key, value) VALUES ('PURGE_AGE', '%d')" % \
         PURGE_AGE,
     # Key Store free for use for developers of scripts
     # just use the set() and get() functions
     "CREATE TABLE keystore (" + \
        "container TEXT, " + \
        "category TEXT, " + \
        "key TEXT, " + \
        "value TEXT, " + \
        "last_update DATETIME DEFAULT current_timestamp" + \
     ")",
     "CREATE UNIQUE INDEX keystore_idx ON keystore (container, category, key)",
     "CREATE INDEX last_update_idx ON keystore (last_update)",
  ],
}
# This is just used for a quick reference when verifying that
# all of the schema is present (during initialization)
# Define just table names here that were fully declared above in
# the schema
NZBGET_SCHEMA_TABLES = (
   u'lookup',
   u'keystore',
)

# Categories allow us to further partition our keystore hash table
# into groups for others subsections to use without stepping on
# each other.
class Category(object):
    # General Script Configuration
    CONFIG = u'config'
    # NZB/NZBD Defined Variables
    NZB = u'nzb'

CATEGORIES = [ Category.CONFIG, Category.NZB, ]
DEFAULT_CATEGORY = Category.CONFIG

# keys should not be complicated... make it so they aren't
VALID_KEY_RE = re.compile('[^a-zA-Z0-9_.-]')

class Database(object):
    def __init__(self, container, database, reset=False,
                 logger=True, debug=False):
        """Initializes the database if it isn't already prepared,
           Th en fetches an index to work with based on the key passed in.
           If reset is set to True, then if an existing entry is found, it is
           automatically reset and treated as a fresh process.
        """
        # self.container
        # This acts as the index for fetching content to and from
        # the keystore as well as tracking what goes on.
        self.container = container
        self.database = database

        # A global switch that basically disables this class silently
        # the purpose it to prevent it from thrashing on re-occuring
        # failures that are a result of the users system environment
        self.disabled = False

        # Database Connection
        self.socket = None

        # logger identifier
        self.logger_id = self.__class__.__name__
        self.logger = logger
        self.debug = debug

        if isinstance(self.logger, basestring):
            # Use Log File
            self.logger = init_logger(
                name=self.logger_id,
                logger=logger,
                debug=debug,
            )

        elif not isinstance(self.logger, Logger):
            # handle all other types
            if logger is None:
                # None means don't log anything
                self.logger = init_logger(
                    name=self.logger_id,
                    logger=None,
                    debug=debug,
                )
            else:
                # Use STDOUT for now
                self.logger = init_logger(
                    name=self.logger_id,
                    logger=True,
                    debug=debug,
                )
        else:
            self.logger_id = None

        if reset or not isfile(self.database):
            # Initialize
            self._reset()

        # Connect to Database
        if not self.connect():
            raise EnvironmentError('Could not access database.')

        if not self._schema_okay():
            # fail-safe
            self._reset()
            if not self._schema_okay():
                raise EnvironmentError('Could not prepare database.')

        # Keep content clean
        self.prune()

    def __del__(self):
        """Gracefully close any connection to the database on
           destruction of this class
        """
        self.close()
        if self.logger_id:
            destroy_logger(self.logger_id)

    def _reset(self, rebuild=True):
        """Resets the database
        If rebuild is set to True then the schema is re-prepared
        """
        try:
            self.close()
        except:
            pass

        try:
            # Best way to reset the database is to
            # remove it entirely
            unlink(self.database)
        except:
            pass

        if not isdir(dirname(self.database)):
            try:
                # safely ensure the directory exists
                makedirs(dirname(self.database))
            except:
                self.logger.error('Could not create directory: %s' % \
                                  dirname(self.database))
                return False

        if rebuild:
            # Connect to Database
            self.connect()
            if not self._schema_okay():
                if not self._build_schema():
                    return False

        self.logger.debug('Successsfully reset database: %s' % self.database)
        return True

    def connect(self):
        """Establish a connection to the database
        """
        if  self.socket is not None:
            # Already connected
            return True

        if self.disabled:
            # Connections turned off
            return False

        try:
            self.socket = sqlite3.connect(self.database, 20)
            self.logger.debug(
                'Opened connection to SQLite Database: %s' % \
                self.database,
            )

        except Exception as e:
            self.socket = None
            self.logger.error('Failed to connect SQLite Database')
            self.logger.debug(
                'SQLite Database (%s) failure message: %s' % (
                    self.database,
                    str(e),
            ))
            return False

        return True

    def close(self):
        if self.socket is not None:
            try:
                self.socket.close()
            except:
                pass

            self.socket = None
            self.logger.debug(
                'Closed connection to SQLite Database %s' % \
                self.database,
            )
        return

    def execute(self, *args, **kwargs):

        if not self.socket:
            if not self.connect():
                return None

        try:
            result = self.socket.execute(*args, **kwargs)
            self.logger.vdebug('DB Executing: %s' % str(args))

        except sqlite3.OperationalError as e:
            self.logger.debug('DB Execute OpError: %s' % str(e))
            return None

        except Exception as e:
            self.logger.debug('DB Execute Error: %s' % str(e))
            return None

        return result


    def _build_schema(self, start_version=None):
        """Build the schema or upgrade it (depending on the
           start_version defined)
        """
        if not self.socket:
            if not self.connect():
                return False

        if not isinstance(start_version, int):
            start_version = self._get_version()

        for version in [ k for k in sorted(NZBGET_SCHEMA.keys()) \
             if k > start_version]:
            for query in NZBGET_SCHEMA[version]:
                self.execute(query)
            self.execute(
                "UPDATE lookup SET value = ? " + \
                "WHERE key = 'SCHEMA_VERSION'",
                (str(version),),
            )
        return True

    def _schema_okay(self):
        """A simple check to see if the schema is okay
        """
        if not self.socket:
            if not self.connect():
                return False

        for table in NZBGET_SCHEMA_TABLES:
            try:
                if not bool(len(self.execute(
                    "SELECT 1 FROM sqlite_master WHERE name = ?", (table, )
                   ).fetchall())):
                    return False
            except AttributeError:
                # execute() returned None causing fetchall() not be
                # a valid attribute; this is the same as just being a
                # bad schema
                return False

        return self._get_version() == NZBGET_DATABASE_VERSION

    def _get_version(self):
        if not self.socket:
            if not self.connect():
                return 0

        result = self.execute(
            "SELECT value FROM lookup WHERE key = ?",
            ('SCHEMA_VERSION', ),
        )
        if result:
            try:
                return int(result.fetchall()[0][-1])
            except:
                return 0
        return 0

    def prune(self, age=None, vacuum=True):
        """Sweep old entries out of database to keep it's size
           under control
        """
        if not self.socket:
            if not self.connect():
                return False

        # Default
        prune_age = PURGE_AGE
        if not isinstance(age , int):
            result = self.execute(
                "SELECT value FROM lookup WHERE key = ?",
                ('PURGE_AGE', ),
            )
            if not result:
                # Simply put, if you remove this key, pruning will not
                # take place ever.
                return True

            try:
                prune_age = int(result.fetchall()[0][-1])
            except:
                pass
        else:
            prune_age = age

        purge_ref = datetime.now() - timedelta(seconds=prune_age)
        purge_ref = purge_ref.strftime(SQLITE_DATE_FORMAT)

        self.execute(
            "DELETE FROM keystore WHERE last_update <= ?",
            (purge_ref, ),
        )
        if vacuum:
            self.execute("VACUUM")

        return True

    def unset(self, key, category=None):
        """Remove a key from the database
        """
        if not self.socket:
            if not self.connect():
                return False

        if not category:
            category = DEFAULT_CATEGORY
        else:
            category = VALID_KEY_RE.sub('', category).lower()

        if category not in CATEGORIES:
            self.logger.error("Database category '%s' does not exist.")
            return False

        # clean key
        key = VALID_KEY_RE.sub('', key).upper()
        if not key:
            return False

        try:
            # First see if keystore already has a match
            if(bool(len(self.socket.execute(
                "SELECT value FROM keystore WHERE " + \
                "container = ? AND category = ? AND key = ?",
                (self.container, category, key)).fetchall()))):
                if not self.socket.execute(
                    "DELETE FROM keystore WHERE " +\
                    "container = ? AND category = ? AND key = ?",
                    (self.container, category, key),):
                    return False

        except sqlite3.OperationalError as e:
            # Database is corrupt or changed
            self.logger.debug(
                "Database.unset() Operational Error: %s" % str(e))

            if not self._reset():
                self.logger.error(
                    "Detected damaged database; countermeasures failed.",
                )
                self.disabled = True

            else:
                self.logger.info(
                    "Detected damaged database; situation corrected.",
                )

        return True


    def set(self, key, value, category=None):
        """Set a key and a value into the database for retrieval later
        """
        if not self.socket:
            if not self.connect():
                return False

        if not category:
            category = DEFAULT_CATEGORY
        else:
            category = VALID_KEY_RE.sub('', category).lower()

        if category not in CATEGORIES:
            self.logger.error("Database category '%s' does not exist.")
            return False

        now = datetime.now().strftime(SQLITE_DATE_FORMAT)

        # clean key
        key = VALID_KEY_RE.sub('', key).upper()
        if not key:
            return False

        # Get a cursor object
        cursor = self.socket.cursor()

        try:
            # First see if keystore already has a match
            if(bool(len(cursor.execute(
                "SELECT value FROM keystore WHERE " + \
                "container = ? AND category = ? AND key = ?",
                (self.container, category, key)).fetchall()))):
                if not cursor.execute(
                    "UPDATE keystore SET value = ?, last_update = ?" + \
                    " WHERE container = ? AND category = ? AND key = ?",
                    (value, now, self.container, category, key),):
                    return False
            else:
                if not cursor.execute(
                    "INSERT INTO keystore " + \
                    "(container, category, key, value, last_update) " + \
                    "VALUES (?, ?, ?, ?, ?)",
                    (self.container, category, key, value, now),):
                    return False
            # commit changes
            self.socket.commit()

        except sqlite3.OperationalError as e:
            # Database is corrupt or changed
            self.logger.debug(
                "Database.set() Operational Error: %s" % str(e))

            if not self._reset():
                self.logger.error(
                    "Detected damaged database; countermeasures failed.",
                )
                self.disabled = True

            else:
                self.logger.info(
                    "Detected damaged database; situation corrected.",
                )
            return False

        return True

    def get(self, key, default=None, category=None):
        """Get a value after specifying a key
        """

        if not self.socket:
            if not self.connect():
                return default

        if not category:
            category = DEFAULT_CATEGORY
        else:
            category = VALID_KEY_RE.sub('', category).lower()

        if category not in CATEGORIES:
            self.logger.error("Database category '%s' does not exist.")
            return default

        # clean key
        key = VALID_KEY_RE.sub('', key).upper()

        try:
            result = self.socket.execute(
                "SELECT value FROM keystore " + \
                "WHERE container = ? AND category = ? AND key = ?",
                (self.container, category, key),
            )
            if result:
                try:
                    return result.fetchall()[0][-1]
                except:
                    return default

        except sqlite3.OperationalError as e:
            # Database is corrupt or changed
            self.logger.debug(
                "Database.get() Operational Error: %s" % str(e))

            if not self._reset():
                self.logger.error(
                    "Detected damaged database; countermeasures failed.",
                )
                self.disabled = True

            else:
                self.logger.info(
                    "Detected damaged database; situation corrected.",
                )

        return default

    def items(self, category=None):
        """Return all variables as a list of tuples (k, p)
        """

        items = list()

        if not self.socket:
            if not self.connect():
                return items

        if not category:
            category = DEFAULT_CATEGORY
        else:
            category = VALID_KEY_RE.sub('', category).lower()

        if category not in CATEGORIES:
            self.logger.error("Database category '%s' does not exist.")
            return items

        # Get a cursor object
        cursor = self.socket.cursor()

        try:
            cursor.execute(
                "SELECT key, value FROM keystore " + \
                "WHERE container = ? AND category = ?",
                (self.container, category),
            )

        except sqlite3.OperationalError as e:
            # Database is corrupt or changed
            self.logger.debug(
                "Database.items() Operational Error: %s" % str(e))

            if not self._reset():
                self.logger.error(
                    "Detected damaged database; countermeasures failed.",
                )
                self.disabled = True

            else:
                self.logger.info(
                    "Detected damaged database; situation corrected.",
                )

            # early return of empty list
            return items

        while True:
            row = cursor.fetchone()
            if row is None:
                break

            items.append((row[0], row[1]))

        return items

# -*- encoding: utf-8 -*-
#
# A scripting wrapper for SABnzbd's Post Processing Scripting
#
# Copyright (C) 2017 Chris Caron <lead2gold@gmail.com>
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
This class was intended to make writing SABnzbd Post Process Scripts easier to
manage and write by handling the common error handling and simplify commont
tasks.

Some inline documentation was based on content provided at:
   - https://sabnzbd.org/wiki/scripts/post-processing-scripts


from nzbget import SABPostProcessScript

# Now define your class while inheriting the rest
class MySABPostProcessScript(SABPostProcessScript):
    def main(self, *args, **kwargs):

        # Version Checking, Environment Variables Present, etc
        if not self.validate():
            # No need to document a failure, validate will do that
            # on the reason it failed anyway
            return False

        # write all of your code here you would have otherwise put in the
        # script

        # All system environment variables (SAB_.*)

        print('SCRIPT (The current script is: %s' % self.get('SCRIPT'))
        print('NZO_ID %s' self.get('NZO_ID'))
        print('FILENAME %s' self.get('FILENAME'))
        print('PP_STATUS %s' self.get('PP_STATUS'))
        # ... etc

        # Set any variable you want by any key.  Note that if you use
        # keys that were defined by the system (such as CAT, DIRECTORY,
        # etc, you may have some undesirable results.  Try to avoid reusing
        # system variables already defined (identified above):
        self.set('MY_KEY', 'MY_VALUE')

        # You can fetch it back; this will also set an entry in  the
        # sqlite database for each hash references that can be pulled from
        # another script that simply calls self.get('MY_KEY')
        print(self.get('MY_KEY')) # prints MY_VALUE

        # You can also use push() which is similar to set()
        # except that it interacts with the NZBGet Server and does not use
        # the sqlite database. This can only be reached across other
        # scripts if the calling application is NZBGet itself
        self.push('ANOTHER_KEY', 'ANOTHER_VALUE')

        # You can still however locally retrieve what you set using push()
        # with the get() function
        print(self.get('ANOTHER_KEY')) # prints ANOTHER_VALUE

        # Returns have been made easy.  Just return:
        #   * True if everything was successful
        #   * False if there was a problem

        return True

# Call your script as follows:
if __name__ == "__main__":
    from sys import exit

    # Create an instance of your Script
    myscript = MySABPostProcessScript()

    # call run() and exit() using it's returned value
    exit(myscript.run())
"""

import re
from os import chdir
from os import unlink
from os import environ
from os.path import isdir
from os.path import isfile
from os.path import join
from os.path import splitext
from os.path import basename
from os.path import abspath

# NZB-File Compression Handling
import gzip
from tempfile import mkstemp

# Relative Includes
from .ScriptBase import ScriptBase
from .ScriptBase import SAB_ENVIRO_ID
from .ScriptBase import SCRIPT_MODE
from .ScriptBase import NZBGET_BOOL_FALSE
from .PostProcessCommon import OBFUSCATED_PATH_RE
from .PostProcessCommon import OBFUSCATED_FILE_RE

from .Utils import os_path_split as split


class TOTAL_STATUS(object):
    """Cumulative (Total) Status of NZB Processing
    """
    # everything OK
    SUCCESS = 'SUCCESS'
    # download is damaged but probably can be repaired; user intervention is
    # required;
    WARNING = 'WARNING'
    # download has failed or a serious error occurred during
    # post-processing (unpack, par);
    FAILURE = 'FAILURE'
    # download was deleted; post-processing scripts are usually not called in
    # this case; however it's possible to force calling scripts with command
    # "post-process again".
    DELETED = 'DELETED'


class PP_STATUS(object):
    """This provides the Post Process Status of SABNzbd set in the
    SAB_PP_STATUS environment variable
    """
    # checked and successfully repaired
    SUCCESS = 0
    # verification failed
    VERIFY_FAIL = 1
    # unpacking failed
    UNPACK_FAIL = 2
    # both verification and vunpack failed
    VERIFY_UNPACK_FAIL = 3
    # Failed Post Processing
    FAILURE = -1


class SABPostProcessScript(ScriptBase):
    """POST PROCESS mode is called after the unpack stage
    """
    def __init__(self, *args, **kwargs):
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Multi-Script Support
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        if not hasattr(self, 'script_dict'):
            # Only define once
            self.script_dict = {}
        self.script_dict[SCRIPT_MODE.SABNZBD_POSTPROCESSING] = self

        # Used to track a temporary NZB-File if we need one.
        self._sab_temp_nzb = None

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Initialize Parent
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        super(SABPostProcessScript, self).__init__(*args, **kwargs)

    def sabnzbd_postprocess_init(self, *args, **kwargs):
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Fetch Script Specific Arguments
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        directory = kwargs.get('directory')
        nzbname = kwargs.get('nzbname')
        nzbfilename = kwargs.get('nzbfilename')
        category = kwargs.get('category')
        status = kwargs.get('status')
        parse_nzbfile = kwargs.get('parse_nzbfile', True)
        use_database = kwargs.get('use_database', True)

        # self.directory
        # This is the path to the destination directory for downloaded files.
        if directory is None:
            self.directory = environ.get(
                '%sDIRECTORY' % SAB_ENVIRO_ID,
            )
            _final_directory = environ.get(
                '%sCOMPLETE_DIR' % SAB_ENVIRO_ID,
            )
            if self.directory and not isdir(self.directory):
                if _final_directory and isdir(_final_directory):
                    # adjust path
                    self.directory = _final_directory

            elif _final_directory and isdir(_final_directory):
                # adjust path
                self.directory = _final_directory
        else:
            self.directory = directory

        if self.directory:
            self.directory = abspath(self.directory)

        # self.nzbname
        # User-friendly name of processed nzb-file as it is displayed by the
        # program.  The file path and extension are removed.  If download was
        # renamed, this parameter reflects the new name.
        if nzbname is None:
            self.nzbname = environ.get(
                '%sFILENAME' % SAB_ENVIRO_ID,
            )
        else:
            self.nzbname = nzbname

        # self.nzbfilename
        # Name of processed nzb-file. If the file was added from incoming
        # nzb-directory, this is a full file name, including path and
        # extension. If the file was added from web-interface, it's only the
        # file name with extension. If the file was added via RPC-API (method
        # append), this can be any string but the use of actual file name is
        # recommended for developers.
        if nzbfilename is None:
            self.nzbfilename = environ.get(
                '%sORIG_NZB_GZ' % SAB_ENVIRO_ID,
            )
            if not self.nzbfilename:
                self.nzbfilename = environ.get(
                    '%sNZBNAME' % SAB_ENVIRO_ID,
                )
            # Fallback Check
            if not self.nzbfilename:
                self.nzbfilename = environ.get(
                    '%sURL' % SAB_ENVIRO_ID,
                )
            # last resort because we want to have this variable defined!
            if not self.nzbfilename:
                self.nzbfilename = self.nzbname

        else:
            self.nzbfilename = nzbfilename

        self.nzbfilename = self.handle_nzbfile(self.nzbfilename)

        # self.category
        # Category assigned to nzb-file (can be empty string).
        if category is None:
            self.category = environ.get(
                '%sCAT' % SAB_ENVIRO_ID,
            )
        else:
            self.category = category

        # self.status
        if status is None:
            self.status = environ.get(
                '%sPP_STATUS' % SAB_ENVIRO_ID,
            )
        else:
            self.status = status

        try:
            self.status = int(self.status)

        except (ValueError, TypeError):
            self.status = PP_STATUS.FAILURE

        _err = environ.get(
            '%sFAIL_MSG' % SAB_ENVIRO_ID,
        )

        self.logger.debug('SABnzbd PP Status: %s' % str(self.status))
        if _err:
            self.logger.debug('SABnzbd PP Error Message: %s' % str(_err))
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Error Handling
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        if self.nzbfilename:
            # absolute path names
            self.nzbfilename = abspath(self.nzbfilename)

            if parse_nzbfile:
                # Initialize information fetched from NZB-File
                # We intentionally allow existing nzbheaders to over-ride
                # any found in the nzbfile
                self.nzbheaders = dict(
                    self.parse_nzbfile(
                        self.nzbfilename, check_queued=True)\
                )

        if self.directory:
            # absolute path names
            self.directory = abspath(self.directory)

        if not (self.directory and isdir(self.directory)):
            self.logger.debug('Process directory is missing: %s' % \
                self.directory)
        else:
            try:
                chdir(self.directory)
            except OSError:
                self.logger.debug('Process directory is not accessible: %s' % \
                    self.directory)

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Enforce system/global variables for script processing
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        self.system['DIRECTORY'] = self.directory
        if self.directory is not None:
            environ['%sDIRECTORY' % SAB_ENVIRO_ID] = \
                self.directory

        self.system['FILENAME'] = self.nzbname
        if self.nzbname is not None:
            environ['%sFILENAME' % SAB_ENVIRO_ID] = \
                self.nzbname

        self.system['NZBNAME'] = self.nzbfilename
        if self.nzbfilename is not None:
            environ['%sNZBNAME' % SAB_ENVIRO_ID] = \
                self.nzbfilename

        self.system['CAT'] = self.category
        if self.category is not None:
            environ['%sCAT' % SAB_ENVIRO_ID] = \
                self.category

        self.system['PP_STATUS'] = str(self.status)
        if self.status is not None:
            environ['%sPP_STATUS' % SAB_ENVIRO_ID] = \
                str(self.status)

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Create Database for set() and get() operations
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        if use_database:
            # database_key is inherited in the parent class
            # future calls of set() and get() will allow access
            # to the database now
            try:
                self.database_key = \
                        self.get('NZO_ID', basename(self.nzbfilename))
            except AttributeError:
                pass

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Debug Flag Check
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def sabnzbd_postprocess_debug(self, *args, **kwargs):
        """Uses the environment variables to detect if debug mode is set
        """
        return self.parse_bool(
            environ.get('%sDEBUG' % SAB_ENVIRO_ID, NZBGET_BOOL_FALSE),
        )

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Sanity
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def sabnzbd_postprocess_sanity_check(self, *args, **kwargs):
        """Sanity checking to ensure this really is a SAB Post-Process Script
        """
        return ('%sCOMPLETE_DIR' % SAB_ENVIRO_ID in environ)

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Validatation
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def sabnzbd_postprocess_validate(self, keys=None, min_version=2,
                                     *args, **kwargs):
        """validate against environment variables
        """

        is_okay = super(SABPostProcessScript, self)._validate(
            keys=keys,
            min_version=min_version,
        )

        if min_version >= 2:
            required_opts = set((
                'COMPLETE_DIR',
                'PP_STATUS',
                'VERSION',
            ))
            found_opts = set(self.system) & required_opts
            if found_opts != required_opts:
                missing_opts = list(required_opts ^ found_opts)
                self.logger.error(
                    'Validation - (v2.x) Directives not set: %s' % \
                      ', '.join(missing_opts),
                )
                is_okay = False

        return is_okay

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Health Check
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def sabnzbd_postprocess_health_check(self, is_unpacked=True,
                                         has_archive=False, *args, **kwargs):
        """Similar to validate, except some scripts don't need to
        out right fail if the download health is bad. Some might just
        return silently, others may try to correct the health
        """

        is_okay = super(SABPostProcessScript, self)\
                ._health_check(*args, **kwargs)

        if self.status != PP_STATUS.SUCCESS:
            is_okay = False

        return is_okay

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # File Retrieval
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def sabnzbd_postprocess_get_files(self, search_dir=None, *args, **kwargs):
        """a wrapper to the get_files() function defined in the inherited class
           the only difference is the search_dir automatically uses the
           defined download `directory` as a default (if not specified).
        """
        if search_dir is None:
            search_dir = self.directory

        return super(SABPostProcessScript, self)._get_files(
            search_dir=search_dir, *args, **kwargs)

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Retrieve Statistics
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def get_statistics(self, nzbid=None):
        """
        Returns the download statistics (via the API)

        The result is returned in an easy to interpret dictionary like so
        {
            'download_time_sec': 40.0,
            'download_avg': 2.0,
            'bytes_downloaded': 2.0,
            'download_total': 2.0,
        }

        If an error occurs, then 'None' is returned.
        """

        return {
            # File Download Total Time (in seconds)
            'download_time_sec': self.get('DOWNLOAD_TIME'),
            # File Download Average Transfer Speed
            'download_avg': self.get('AVG_BPS'),
            # How many bytes were recieved (can be more than tried, due to
            # overhead)
            'bytes_downloaded': self.get('BYTES_DOWNLOADED'),
            'download_total': self.get('BYTES'),
        }

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Obfuscation Handling
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def deobfuscate(self, filename, ref_dir=None, ref_nzbfile=None):
        """attempts to detect and update
        """

        if ref_dir is None:
            ref_dir = self.directory

        if ref_nzbfile is None:
            ref_nzbfile = self.nzbfilename

        if filename[0:len(ref_dir):] == ref_dir:
            new_name = filename[len(ref_dir)+1:]
            self.logger.debug(
                'Deobfuscate - Stripped filename down to: %s' % new_name,
            )
        else:
            new_name = filename

        parts = split(new_name)
        part_removed = 0
        for x in range(0, len(parts)-1):
            fn = parts[x]
            if OBFUSCATED_PATH_RE.match(fn):
                self.logger.info(
                    'Detected obfuscated directory name %s,' % fn +
                    ' removing from path',
                )
                parts[x] = None
                part_removed += 1

        if OBFUSCATED_FILE_RE.match(basename(filename)):
            self.logger.info(
                'Detected obfuscated filename %s,' % basename(filename) +
                ' removing from path')
            parts[len(parts)-1] = '-' + splitext(filename)[1]
            part_removed += 1

        if part_removed < len(parts):
            new_name = ''
            for x in range(0, len(parts)):
                if parts[x] is not None:
                    new_name = join(new_name, parts[x])
            return new_name

        if OBFUSCATED_FILE_RE.match(new_name):
            new_name = ''

        # Check out NZB-Filename
        if len(self.nzb_items()):
            self.logger.info(
                'All file path parts are obfuscated, using obfuscated ' +
                'NZB-Headers',
            )

            # Fetch category
            category = self.nzb_get('category', '')\
                .split(' ')[0].lower()
            subcategory = self.nzb_get('category', '')\
                .split(' ')[-1].lower()

            if self.nzb_get('name'):
                # We can pick from the nzb headers
                nzb_name = self.nzb_get('name')
                new_name = join(ref_dir, '%s%s' % (
                    re.sub('[\s]+', '.', nzb_name),
                    splitext(basename(new_name))[1],
                ))

            elif category[0:5] == 'movie' and \
                    self.nzb_get('propername'):
                nzb_name = self.nzb_get('propername')

                if self.nzb_get('movieyear'):
                    nzb_name += '(%s)' % self.nzb_get('movieyear')

                new_name = join(ref_dir, '%s%s' % (
                    re.sub('[\s]+', '.', nzb_name),
                    splitext(basename(new_name))[1],
                ))

            elif category == 'tv' and \
                    self.nzb_get('propername'):
                nzb_name = self.nzb_get('propername')
                if self.nzb_get('episodename'):
                    nzb_name += '-%s' % \
                        self.nzb_get('episodename')

                if subcategory == 'hd':
                    nzb_name += '-HDTV'

                new_name = join(ref_dir, '%s%s' % (
                    re.sub('[\s]+', '.', nzb_name),
                    splitext(basename(new_name))[1],
                ))

            elif self.nzb_get('propername'):
                nzb_name = self.nzb_get('propername')
                new_name = join(ref_dir, '%s%s' % (
                    re.sub('[\s]+', '.', nzb_name),
                    splitext(basename(filename))[1],
                ))
            else:
                # No possible
                new_name = ''

        if new_name:
            self.logger.debug(
                'Deobfuscate - Generated filename: %s' % new_name,
            )
            return new_name

        # we're running out of new names :)... try the NZB-FileName
        if ref_nzbfile and not OBFUSCATED_FILE_RE.match(basename(ref_nzbfile)):
            self.logger.info(
                'All file path parts are obfuscated, using NZB-FileName',
            )
            new_name = join(ref_dir, '%s%s' % (
                re.sub('[\s]+', '.',
                       splitext(basename(ref_nzbfile))[0]),
                splitext(basename(filename))[1],
            ))

        else:
            self.logger.info('Deobfuscation is not possible')
            return filename

        self.logger.debug('Deobfuscate - Generated filename: %s' % new_name)
        return new_name

    def handle_nzbfile(self, nzbfile):
        """
        Takes an nzbfile and if it's compressed it creates a temporary
        uncompressed version we can reference. The function returns
        an uncompressed NZB-File if it can (obviously depends on what was
        passed in.
        """

        if not nzbfile:
            # Nothing we can do
            return ''

        # Handle .gz compressed NZB-Files and update our pointer accordingly
        if not isfile(nzbfile):
            # Nothing we can do; return what we started with
            return nzbfile

        # Extract our filename
        result = re.match('^(?P<filename>.+\.nzb)\.gz$', nzbfile, re.I)
        if not result:
            # We're done; that was easy
            return nzbfile

        # Extract our file into a temporary directory
        fo, self._sab_temp_nzb = mkstemp(dir=self.tempdir, suffix='.nzb')

        # Our file descriptors
        fi = None
        try:
            fi = gzip.open(nzbfile, "rb")

        except Exception:
            # Can't open the file
            return nzbfile

        try:
            fo = open(self._sab_temp_nzb, 'wb')
        except Exception:
            # Can't open the file
            return nzbfile

        try:
            while 1:
                buf = fi.read(16384)
                if not buf:
                    # We're Done
                    break
                fo.write(buf)

        except Exception:
            # oh well..
            unlink(self._sab_temp_nzb)
            self._sab_temp_nzb = None

        try:
            fo.close()
        except Exception:
            pass

        try:
            fi.close()
        except Exception:
            pass

        return self._sab_temp_nzb

    def sabnzbd_postprocess_close(self):
        """
        Allow the graceful handling of our temporary NZB-File
        """
        if self._sab_temp_nzb and isfile(self._sab_temp_nzb):
            try:
                # Cleanup
                unlink(self._sab_temp_nzb)
                self._sab_temp_nzb = None
            except:
                # we tried...
                pass

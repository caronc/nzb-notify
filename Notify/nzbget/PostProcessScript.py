# -*- encoding: utf-8 -*-
#
# A scripting wrapper for NZBGet's Post Processing Scripting
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
This class was intended to make writing NZBGet Scripts easier to manage and
write by handling the common error handling and provide the most reused code
in a re-usable container. It was initially written to work with NZBGet v13
but provides most backwards compatibility.

It was designed to be inheritied as a base class requiring you to only write
the main() function which should preform the task you are intending.

It looks after fetching all of the environment variables and will parse
the meta information out of the NZB-File.

It allows you to set variables that other scripts can access if they need to
using the set() and get() variables. This is done through a simply self
maintained hash table type structure within a sqlite database. All the
wrapper functions are already written.  If you call 'set('MYKEY', 1')
you can call get('MYKEY') in another script and continue working

push() functions written to pass information back to nzbget using it's
processing engine.

all exceptions are now automatically handled and logging can be easily
changed from stdout, to stderr or to a file.

Test suite built in (using python-nose) to ensure old global variables
will still work as well as make them easier to access and manipulate.

Some inline documentation was based on content provided at:
   - http://nzbget.net/Extension_scripts


############################################################################
Post Process Script Usage/Example
############################################################################

#############################################################################
### NZBGET POST-PROCESSING SCRIPT                                         ###
#
# Describe your Post-Process Script here
# Author: Chris Caron <lead2gold@gmail.com>
#

############################################################################
### OPTIONS                                                              ###

#
# Enable NZBGet debug logging (yes, no)
# Debug=no
#

### NZBGET POST-PROCESSING SCRIPT                                         ###
#############################################################################

from nzbget import PostProcessScript

# Now define your class while inheriting the rest
class MyPostProcessScript(PostProcessScript):
    def main(self, *args, **kwargs):

        # Version Checking, Environment Variables Present, etc
        if not self.validate():
            # No need to document a failure, validate will do that
            # on the reason it failed anyway
            return False

        # write all of your code here you would have otherwise put in the
        # script

        # All system environment variables (NZBOP_.*) as well as Post
        # Process script specific content (NZBPP_.*)
        # following dictionary (without the NZBOP_ or NZBPP_ prefix):
        print('TEMPDIR (directory is: %s' % self.get('TEMPDIR'))
        print('DIRECTORY %s' self.get('DIRECTORY'))
        print('NZBNAME %s' self.get('NZBNAME'))
        print('NZBFILENAME %s' self.get('NZBFILENAME'))
        print('CATEGORY %s' self.get('CATEGORY'))
        print('TOTALSTATUS %s' self.get('TOTALSTATUS'))
        print('STATUS %s' self.get('STATUS'))
        print('SCRIPTSTATUS %s' self.get('SCRIPTSTATUS'))

        # Set any variable you want by any key.  Note that if you use
        # keys that were defined by the system (such as CATEGORY, DIRECTORY,
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

        # Your script configuration files (NZBPP_.*) are here in this
        # dictionary (again without the NZBPP_ prefix):
        # assume you defined `Debug=no` in the first 10K of your PostProcessScript
        # NZBGet translates this to `NZBPP_DEBUG` which can be retrieved
        # as follows:
        print('DEBUG %s' self.get('DEBUG'))

        # Returns have been made easy.  Just return:
        #   * True if everything was successful
        #   * False if there was a problem
        #   * None if you want to report that you've just gracefully
                  skipped processing (this is better then False)
                  in some circumstances. This is neither a failure or a
                  success status.

        # Feel free to use the actual exit codes as well defined by
        # NZBGet on their website.  They have also been defined here
        # from nzbget import EXIT_CODE

        return True

# Call your script as follows:
if __name__ == "__main__":
    from sys import exit

    # Create an instance of your Script
    myscript = MyPostProcessScript()

    # call run() and exit() using it's returned value
    exit(myscript.run())
"""

import re
from os import chdir
from os import environ
from os.path import isdir
from os.path import isfile
from os.path import join
from os.path import splitext
from os.path import basename
from os.path import dirname
from os.path import abspath

from socket import error as SocketError

# Relative Includes
from ScriptBase import ScriptBase
from ScriptBase import Health
from ScriptBase import SCRIPT_MODE
from ScriptBase import NZBGET_BOOL_FALSE
from Utils import os_path_split as split

# Obfuscated Expression
OBFUSCATED_PATH_RE = re.compile(
    '^[a-z0-9]+$',
    re.IGNORECASE,
)
OBFUSCATED_FILE_RE = re.compile(
    '^[a-z0-9]+\.[a-z0-9]+$',
    re.IGNORECASE,
)

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

# TOTALSTATUS Delimiter
TOTALSTATUS_DELIMITER = '/'

class SCRIPT_STATUS(object):
    """Summary status of the scripts executed before the current one
    """
    # no other scripts were executed yet or all of them have ended with an exit
    # code of: NONE
    NONE = 'NONE'
    # all other scripts have ended with exit code "SUCCESS"
    SUCCESS = 'SUCCESS'
    # at least one of the script has failed
    FAILURE = 'FAILURE'

class PAR_STATUS(object):
    """This is a depricated flag (as of NZBGet v13) but previously
    provides the status of the par-check of the downloaded content.
    """
    # not checked: par-check is disabled or nzb-file does not contain
    # any par-files
    SKIPPED = 0
    # checked and failed to repair
    FAILURE = 1
    # checked and successfully repaired
    SUCCESS = 2
    # checked and can be repaired but repair is disabled
    DISABLED = 3

class UNPACK_STATUS(object):
    """This is a depricated flag (as of NZBGet v13) but previously
    provides the status of the unpacking of the downloaded content.
    """
    # unpack is disabled or was skipped due to nzb-file properties
    # or due to errors during par-check
    SKIPPED = 0
    # unpack failed
    FAILURE = 1
    # unpack was successful
    SUCCESS = 2

# Environment variable that prefixes all NZBGET options being passed into
# scripts with respect to the NZB-File (used in Post Processing Scripts)
POSTPROC_ENVIRO_ID = 'NZBPP_'

# Precompile Regulare Expression for Speed
POSTPROC_OPTS_RE = re.compile('^%s([A-Z0-9_]+)$' % POSTPROC_ENVIRO_ID)

class PostProcessScript(ScriptBase):
    """POST PROCESS mode is called after the unpack stage
    """
    def __init__(self, *args, **kwargs):
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Multi-Script Support
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        if not hasattr(self, 'script_dict'):
            # Only define once
            self.script_dict = {}
        self.script_dict[SCRIPT_MODE.POSTPROCESSING] = self

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Initialize Parent
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        super(PostProcessScript, self).__init__(*args, **kwargs)

    def postprocess_init(self, *args, **kwargs):
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Fetch Script Specific Arguments
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        directory = kwargs.get('directory')
        nzbname = kwargs.get('nzbname')
        nzbfilename = kwargs.get('nzbfilename')
        category = kwargs.get('category')
        totalstatus = kwargs.get('totalstatus')
        status = kwargs.get('status')
        scriptstatus = kwargs.get('scriptstatus')
        parse_nzbfile = kwargs.get('parse_nzbfile', True)
        use_database = kwargs.get('use_database', True)

        # Support Depricated Variables
        parstatus = kwargs.get('parstatus')
        unpackstatus = kwargs.get('unpackstatus')

        # Fetch/Load Post Process Script Configuration
        script_config = dict([(POSTPROC_OPTS_RE.match(k).group(1), v.strip()) \
               for (k, v) in environ.items() if POSTPROC_OPTS_RE.match(k)])

        if self.vvdebug:
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
            # Print Global Script Varables to help debugging process
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
            for k, v in script_config.items():
                self.logger.vvdebug('%s%s=%s' % (POSTPROC_ENVIRO_ID, k, v))

        # Merge Script Configuration With System Config
        self.system = dict(script_config.items() + self.system.items())

        # self.directory
        # This is the path to the destination directory for downloaded files.
        if directory is None:
            self.directory = environ.get(
                '%sDIRECTORY' % POSTPROC_ENVIRO_ID,
            )
            _final_directory = environ.get(
                '%sFINALDIR' % POSTPROC_ENVIRO_ID,
            )
            if self.directory and not isdir(self.directory):
                if _final_directory and isdir(_final_directory):
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
                '%sNZBNAME' % POSTPROC_ENVIRO_ID,
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
                '%sNZBFILENAME' % POSTPROC_ENVIRO_ID,
            )
        else:
            self.nzbfilename = nzbfilename

        # self.category
        # Category assigned to nzb-file (can be empty string).
        if category is None:
            self.category = environ.get(
                '%sCATEGORY' % POSTPROC_ENVIRO_ID,
            )
        else:
            self.category = category

        # self.totalstatus
        # Total status of the processing of the NZB-File.  This value
        # includes the result from previous scripts that may have ran
        # before this one.
        if totalstatus is None:
            self.totalstatus = environ.get(
                '%sTOTALSTATUS' % POSTPROC_ENVIRO_ID,
            )
        else:
            self.totalstatus = totalstatus

        # self.status
        # Complete status info for nzb-file: it consists of total status and
        # status detail separated with slash. There are many combinations.
        # Just few examples:
        #         FAILURE/HEALTH
        #         FAILURE/PAR
        #         FAILURE/UNPACK
        #         WARNING/REPAIRABLE
        #         WARNING/SPACE
        #         WARNING/PASSWORD
        #         SUCCESS/ALL
        #         SUCCESS/UNPACK
        #
        # For the complete list see description of method history in RPC API
        # reference: http://nzbget.net/RPC_API_reference
        if status is None:
            self.status = Health(environ.get(
                '%sSTATUS' % POSTPROC_ENVIRO_ID,
            ))
        else:
            self.status = Health(status)

        # self.scriptstatus
        # Summary status of the scripts executed before the current one
        if scriptstatus is None:
            self.scriptstatus = environ.get(
                '%sSCRIPTSTATUS' % POSTPROC_ENVIRO_ID,
            )
        else:
            self.scriptstatus = scriptstatus

        # self.parstatus (NZBGet < v13) - Depreciated
        # Result of par-check
        if parstatus is None:
            self.parstatus = environ.get(
                '%sPARSTATUS' % POSTPROC_ENVIRO_ID,
                # Default
                PAR_STATUS.SKIPPED,
            )
        else:
            self.parstatus = parstatus

        # self.unpackstatus (NZBGet < v13) - Depreciated
        # Result of unpack
        if unpackstatus is None:
            self.unpackstatus = environ.get(
                '%sUNPACKSTATUS' % POSTPROC_ENVIRO_ID,
                # Default
                UNPACK_STATUS.SKIPPED,
            )
        else:
            self.unpackstatus = unpackstatus

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
                        .items() + self.pull_dnzb().items(),
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

        # Total Status
        if not isinstance(self.totalstatus, basestring):
            self.totalstatus = TOTAL_STATUS.SUCCESS

        # Par Status
        if not isinstance(self.parstatus, int):
            try:
                self.parstatus = int(self.parstatus)
            except:
                self.parstatus = PAR_STATUS.SKIPPED

        # Unpack Status
        if not isinstance(self.unpackstatus, int):
            try:
                self.unpackstatus = int(self.unpackstatus)
            except:
                self.unpackstatus = UNPACK_STATUS.SKIPPED

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Enforce system/global variables for script processing
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        self.system['DIRECTORY'] = self.directory
        if self.directory is not None:
            environ['%sDIRECTORY' % POSTPROC_ENVIRO_ID] = \
                self.directory

        self.system['NZBNAME'] = self.nzbname
        if self.nzbname is not None:
            environ['%sNZBNAME' % POSTPROC_ENVIRO_ID] = \
                self.nzbname

        self.system['NZBFILENAME'] = self.nzbfilename
        if self.nzbfilename is not None:
            environ['%sNZBFILENAME' % POSTPROC_ENVIRO_ID] = \
                self.nzbfilename

        self.system['CATEGORY'] = self.category
        if self.category is not None:
            environ['%sCATEGORY' % POSTPROC_ENVIRO_ID] = \
                self.category

        self.system['TOTALSTATUS'] = self.totalstatus
        if self.totalstatus is not None:
            environ['%sTOTALSTATUS' % POSTPROC_ENVIRO_ID] = \
                self.totalstatus

        self.system['STATUS'] = str(self.status)
        if self.status is not None:
            environ['%sSTATUS' % POSTPROC_ENVIRO_ID] = \
                str(self.status)

        self.system['SCRIPTSTATUS'] = self.scriptstatus
        if self.scriptstatus is not None:
            environ['%sSCRIPTSTATUS' % POSTPROC_ENVIRO_ID] = \
                self.scriptstatus

        self.system['PARSTATUS'] = self.parstatus
        if self.parstatus is not None:
            environ['%sPARSTATUS' % POSTPROC_ENVIRO_ID] = \
                str(self.parstatus)

        self.system['UNPACKSTATUS'] = self.unpackstatus
        if self.unpackstatus is not None:
            environ['%sUNPACKSTATUS' % POSTPROC_ENVIRO_ID] = \
                str(self.unpackstatus)

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Create Database for set() and get() operations
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        if use_database:
            # database_key is inherited in the parent class
            # future calls of set() and get() will allow access
            # to the database now
            try:
                self.database_key = \
                        self.get('NZBID', basename(self.nzbfilename))
            except AttributeError:
                pass

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Debug Flag Check
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def postprocess_debug(self, *args, **kwargs):
        """Uses the environment variables to detect if debug mode is set
        """
        return self.parse_bool(
            environ.get('%sDEBUG' % POSTPROC_ENVIRO_ID, NZBGET_BOOL_FALSE),
        )

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Sanity
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def postprocess_sanity_check(self, *args, **kwargs):
        """Sanity checking to ensure this really is a Post-Process Script
        """
        return ('%sDIRECTORY' % POSTPROC_ENVIRO_ID in environ)

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Validatation
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def postprocess_validate(self, keys=None, min_version=11, *args, **kwargs):
        """validate against environment variables
        """
        is_okay = super(PostProcessScript, self)._validate(
            keys=keys,
            min_version=min_version,
            download_okay=True,
        )

        if min_version >= 13:
            required_opts = set((
                'TOTALSTATUS',
                'STATUS',
                'SCRIPTSTATUS',
            ))
            found_opts = set(self.system) & required_opts
            if found_opts != required_opts:
                missing_opts = list(required_opts ^ found_opts)
                self.logger.error(
                    'Validation - (v13) Directives not set: %s' % \
                      missing_opts.join(', ')
                )
                is_okay = False

        return is_okay

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Health Check
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def postprocess_health_check(self, is_unpacked=True, has_archive=False,
                                 *args, **kwargs):
        """Similar to validate, except some scripts don't need to
        out right fail if the download health is bad. Some might just
        return silently, others may try to correct the health
        """

        is_okay = super(PostProcessScript, self)\
                ._health_check(*args, **kwargs)

        if self.version < 13:
            # We need to be sure the download is okay before continuing
            # using depricated values in newer version
            if self.parstatus == PAR_STATUS.FAILURE:
                if is_unpacked:
                    is_okay = False

            if self.unpackstatus == UNPACK_STATUS.FAILURE:
                if is_unpacked:
                    is_okay = False

        else:
            if is_unpacked and not self.status.is_unpacked:
                is_okay = False

            if has_archive and not self.status.has_archive:
                is_okay = False

        return is_okay

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # File Retrieval
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def postprocess_get_files(self, search_dir=None, *args, **kwargs):
        """a wrapper to the get_files() function defined in the inherited class
           the only difference is the search_dir automatically uses the
           defined download `directory` as a default (if not specified).
        """
        if search_dir is None:
            search_dir = self.directory

        return super(PostProcessScript, self)._get_files(
            search_dir=search_dir, *args, **kwargs)

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Retrieve Statistics
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def get_statistics(self, nzbid=None):
        """
        Returns the download statistics (via the API)

        The result is returned in an easy to interpret dictionary like so
        {
            'download_size_mb': 10.00,
            'download_time_sec': 40.0,
            'download_avg': 2.0,
            'download_avg_unit': 'GB/s',

            'par_prepare_time_sec': 10.00,
            'par_repair_time_sec': 20.00,
            'unpack_time_sec': 30.00,
            'postprocess_time': 120.00,
            'par_total_time_sec': 30.00,
            'total_time_sec': 160.00,
        }

        If an error occurs, then 'None' is returned.
        """

        if not self.api_connect():
            return None

        if nzbid is None:
            try:
                nzbid = int(self.get('nzbID'))
            except (AttributeError, TypeError):
                return None

        try:
            group = [ x for x in self.api.listgroups(0) \
                     if x['NZBID'] == nzbid ][0]

        except SocketError, e:
            self.logger.warning('RCP Connection Failure (%d): %s' % (
                e[0], e[1]))
            return None

        except IndexError:
            return None

        try:
            dl_size = float(group['DownloadedSizeMB'])
            dl_time = float(group['DownloadTimeSec'])

        except KeyError:
            # We simply didn't fetch any valid content
            self.logger.warning('RCP Response was invalid.')
            self.logger.debug('RCP Response: %s', str(group))
            return None

        # Calculate statistics based on retrieved results
        dl_avg_speed = 0
        dl_avg_speed_unit = 'MB/s'

        if dl_time > 0.0:
            dl_avg_speed = (dl_size/dl_time)
            if dl_avg_speed < 1.0:
                # Convert to KB/s
                dl_avg_speed_unit = 'KB/s'
                dl_avg_speed *= 1024.0
            elif dl_avg_speed > 1000.0:
                # Convert to GB/s
                dl_avg_speed_unit = 'GB/s'
                dl_avg_speed /= 1024.0

        unpack_time = float(group['UnpackTimeSec'])
        par_prepare_time = float(group['ParTimeSec'])
        par_repair_time = float(group['RepairTimeSec'])
        postprocess_time = float(group['PostTotalTimeSec'])

        return {
            # File Download Size (in MB)
            'download_size_mb': dl_size,
            # File Download Total Time (in seconds)
            'download_time_sec': dl_time,
            # File Download Average Transfer Speed
            'download_avg': dl_avg_speed,
            # File Download Average Transfer Speed Unit
            'download_avg_unit': dl_avg_speed_unit,

            # Time Taken to check integrity of file (in seconds)
            'par_prepare_time_sec': par_prepare_time,
            # Time Taken to repair file if it was damaged (in seconds)
            'par_repair_time_sec': par_repair_time,
            # Time Taken to unpack file from it's compressed archive(s)
            # (in seconds)
            'unpack_time_sec': unpack_time,
            # General time spent post processing download (in seconds)
            'postprocess_time': postprocess_time,
            # General time spent verifying and repairing download (in seconds)
            'par_total_time_sec': par_prepare_time + par_repair_time,
            # Total estimated system time spent handling this download
            'total_time_sec': postprocess_time + float(group['DownloadTimeSec']),
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
            self.logger.debug('Deobfuscate - Stripped filename down to: %s' % new_name)
        else:
            new_name = filename

        parts = split(new_name)
        part_removed = 0
        for x in range(0, len(parts)-1):
            fn = parts[x]
            if OBFUSCATED_PATH_RE.match(fn):
                self.logger.info(
                    'Detected obfuscated directory name %s,' % fn + \
                    ' removing from path',
                )
                parts[x] = None
                part_removed += 1

        if OBFUSCATED_FILE_RE.match(basename(filename)):
            self.logger.info(
                'Detected obfuscated filename %s,' % basename(filename) + \
                ' removing from path')
            parts[len(parts)-1] = '-' + splitext(filename)[1]
            part_removed += 1

        if part_removed < len(parts):
            new_name = ''
            for x in range(0, len(parts)):
                if parts[x] != None:
                    new_name = join(new_name, parts[x])
            return new_name

        # If we reach here, we have a completely deobfuscated file

        # Check out NZB-Filename
        if len(self.nzb_items()):
            self.logger.info(
                'All file path parts are obfuscated, using obfuscated ' + \
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
                new_name = join(ref_dir, '%s%s' %(
                    re.sub('[\s]+','.', nzb_name),
                    splitext(basename(new_name))[1],
                ))

            elif category[0:5] == 'movie' and \
                    self.nzb_get('propername'):
                nzb_name = self.nzb_get('propername')

                if self.nzb_get('movieyear'):
                    nzb_name += '(%s)' % self.nzb_get('movieyear')

                new_name = join(ref_dir, '%s%s' %(
                    re.sub('[\s]+','.', nzb_name),
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

                new_name = join(ref_dir, '%s%s' %(
                    re.sub('[\s]+','.', nzb_name),
                    splitext(basename(new_name))[1],
                ))

            elif self.nzb_get('propername'):
                nzb_name = self.nzb_get('propername')
                new_name = join(ref_dir, '%s%s' %(
                    re.sub('[\s]+','.', nzb_name),
                    splitext(basename(filename))[1],
                ))
            else:
                # No possible
                new_name = ''

        if new_name:
            self.logger.debug('Deobfuscate - Generated filename: %s' % new_name)
            return new_name

        # we're running out of new names :)... try the NZB-FileName
        if ref_nzbfile and not OBFUSCATED_FILE_RE.match(basename(ref_nzbfile)):
            self.logger.info(
                'All file path parts are obfuscated, using NZB-FileName',
            )
            new_name = join(ref_dir, '%s%s' %(
                re.sub('[\s]+','.',
                       splitext(basename(ref_nzbfile))[0]),
                splitext(basename(filename))[1],
            ))

        else:
            self.logger.info('Deobfuscation is not possible')
            return filename

        self.logger.debug('Deobfuscate - Generated filename: %s' % new_name)
        return new_name

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Set/Control Functions (also passes data back to NZBGet)
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def push_directory(self, directory=None, final=False):
        if directory:
            # Update local directory
            self.directory = directory

            # Accomodate other environmental variables
            self.system['DIRECTORY'] = self.directory
            environ['%sDIRECTORY' % POSTPROC_ENVIRO_ID] = self.directory

        # Alert NZBGet of Change
        if not final:
            key = 'DIRECTORY'
        else:
            key = 'FINALDIR'

        return self._push(key=key, value=self.directory)

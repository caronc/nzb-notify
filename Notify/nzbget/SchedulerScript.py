# -*- encoding: utf-8 -*-
#
# A scripting wrapper for NZBGet's Scheduler Scripting
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
Schedule Script Usage/Example
############################################################################

############################################################################
### NZBGET SCHEDULER SCRIPT                                               ###
#
# Describe your Schedule Script here
# Author: Chris Caron <lead2gold@gmail.com>
#

############################################################################
### OPTIONS                                                              ###

#
# Enable NZBGet debug logging (yes, no)
# Debug=no
#

### NZBGET SCHEDULER SCRIPT                                              ###
############################################################################

from nzbget import SchedulerScript

# Now define your class while inheriting the rest
class MySchedulerScript(SchedulerScript):
    def main(self, *args, **kwargs):

        # Version Checking, Environment Variables Present, etc
        if not self.validate():
            # No need to document a failure, validate will do that
            # on the reason it failed anyway
            return False

        # write all of your code here you would have otherwise put in the
        # script

        # All system environment variables (NZBOP_.*) as well as Post
        # Process script specific content (NZBSP_.*)
        # following dictionary (without the NZBOP_ or NZBSP_ prefix):
        print('TEMPDIR (directory is: %s' % self.get('TEMPDIR'))
        print('DESTDIR %s' self.get('DESTDIR'))

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

        # Your script configuration files (NZBNP_.*) are here in this
        # dictionary (again without the NZBNP_ prefix):
        # assume you defined `Debug=no` in the first 10K of your SchedulerScript
        # NZBGet translates this to `NZBNP_DEBUG` which can be retrieved
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
        # from nzbget.ScriptBase import EXIT_CODE

        return True

# Call your script as follows:
if __name__ == "__main__":
    from sys import exit

    # Create an instance of your Script
    myscript = MySchedulerScript()

    # call run() and exit() using it's returned value
    exit(myscript.run())

"""
import re
from os import environ

# Relative Includes
from .ScriptBase import ScriptBase
from .ScriptBase import NZBGET_BOOL_FALSE
from .ScriptBase import SCRIPT_MODE

# Environment variable that prefixes all NZBGET options being passed into
# scripts with respect to the NZB-File (used in Scan Scripts)
SCHEDULER_ENVIRO_ID = 'NZBSP_'
TASK_ENVIRO_ID = 'TASK'

# Precompile Regulare Expression for Speed
SCHEDULER_OPTS_RE = re.compile('^%s([A-Z0-9_]+)$' % SCHEDULER_ENVIRO_ID)

class SchedulerScript(ScriptBase):
    def __init__(self, *args, **kwargs):
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Multi-Script Support
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        if not hasattr(self, 'script_dict'):
            # Only define once
            self.script_dict = {}
        self.script_dict[SCRIPT_MODE.SCHEDULER] = self

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Initialize Parent
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        super(SchedulerScript, self).__init__(*args, **kwargs)

    def scheduler_init(self, *args, **kwargs):
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Fetch Script Specific Arguments
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        taskid = kwargs.get('taskid')

        # Fetch/Load Scan Script Configuration
        script_config = dict([(SCHEDULER_OPTS_RE.match(k).group(1), v.strip()) \
               for (k, v) in environ.items() if SCHEDULER_OPTS_RE.match(k)])

        if self.vvdebug:
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
            # Print Global Script Varables to help debugging process
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
            for k, v in script_config.items():
                self.logger.vvdebug('%s%s=%s' % (SCHEDULER_ENVIRO_ID, k, v))

        # Merge Script Configuration With System Config
        self.system = dict(script_config.items() + self.system.items())

        # self.taskid
        # This is the Task Identifier passed in from NZBGet
        if taskid is None:
            self.taskid = environ.get(
                '%sTASKID' % SCHEDULER_ENVIRO_ID,
            )
        else:
            self.taskid = taskid

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Error Handling
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        try:
            self.taskid = int(self.taskid)
            self.logger.info('Task ID assigned: %d' % self.taskid)
        except (ValueError, TypeError):
            # Default is 0
            self.taskid = 0
            self.logger.warning('No Task ID was assigned')

        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        # Enforce system/global variables for script processing
        # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        self.system['TASKID'] = self.taskid
        if isinstance(self.taskid, int) and self.taskid > 0:
            environ['%sTASKID' % SCHEDULER_ENVIRO_ID] = str(self.taskid)

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Debug Flag Check
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def scheduler_debug(self, *args, **kwargs):
        """Uses the environment variables to detect if debug mode is set
        """
        return self.parse_bool(
            environ.get('%sDEBUG' % SCHEDULER_ENVIRO_ID, NZBGET_BOOL_FALSE),
        )

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Validatation
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def scheduler_validate(self, keys=None, min_version=11, *args, **kargs):
        """validate against environment variables
        """
        is_okay = super(SchedulerScript, self)._validate(
            keys=keys,
            min_version=min_version,
        )

        required_opts = set((
            'TASKID',
        ))

        found_opts = set(self.system) & required_opts
        if found_opts != required_opts:
            missing_opts = list(required_opts ^ found_opts)
            self.logger.error(
                'Validation - (v11) Directives not set: %s' % \
                  missing_opts.join(', ')
            )
            is_okay = False

        return is_okay

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Sanity
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def scheduler_sanity_check(self, *args, **kargs):
        """Sanity checking to ensure this really is a post_process script
        """
        from PostProcessScript import POSTPROC_ENVIRO_ID
        return ('%sDIRECTORY' % POSTPROC_ENVIRO_ID not in environ) and \
               ('%sTASKID' % SCHEDULER_ENVIRO_ID in environ)

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    # Tasks
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    def get_task(self, taskid=None):
        """Returns a dictionary of task details identified by the id
        specified.  If no id is specified, then the current task is
        detected and returned.
        """
        if taskid is None:
            # assume default
            taskid = self.taskid

        if not isinstance(taskid, int):
            try:
                taskid = int(taskid)
            except (ValueError, TypeError):
                # can't be typecasted to an integer
                return {}

        if taskid <= 0:
            # No task defined
            return {}

        # Precompile Regulare Expression for Speed
        task_re = re.compile('^%s%s%d_([A-Z0-9_]+)$' % (
            SCHEDULER_ENVIRO_ID,
            TASK_ENVIRO_ID,
            taskid,
        ))

        self.logger.debug('Looking for %s%s%d_([A-Z0-9_]+)$' % (
            SCHEDULER_ENVIRO_ID,
            TASK_ENVIRO_ID,
            taskid,
        ))

        # Fetch Task related content
        return dict([(task_re.match(k).group(1), v.strip()) \
            for (k, v) in environ.items() if task_re.match(k)])

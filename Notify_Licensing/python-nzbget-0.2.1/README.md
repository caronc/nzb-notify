Description
=================
This provides a python framework to design NZBGet scripts with. The intent
was to greatly simplify the development and debugging process. It was
initially designed to work with NZBGet v13 but was made to be compatible
with versions 12 and 11 as well.

* It contains a built in meta tag parser to extract content from NZB-Files.
   _Note: This can only happen if lxml is installed on your system_.
* It can preform very basic obfuscation support on filenames that can not be
  interpreted.
* It creates a common SQLite database (optionally) to additionally write
  content passed via the set() function.  This allows another script to later
  call get() and retrieve the data set() by another.
* It prepares logging right out of the box for you, there is no setup required
* All return codes have been simplified to None/True/False (you can still
  use the old ones if you want)
* It handles all of the exception handling. By this I mean, your code can throw
  an except and it's traceback will be captured gracefully to logging. Then the
  framework will look after returning a correct failure error code to NZBGet.
* It provides some very useful functions that are always being re-written
  inside of every other NZBGet script such as file scanning.
* It greatly simplifies the handling of environment variables and interaction
  to and from NZBGet

Documentation
=============
For the most up to date information and API, visit the wiki at
* https://github.com/caronc/pynzbget/wiki

The entire framework was based on the information found here:
* NZBGet: http://nzbget.net
* NZBGet: scripting documentation: http://nzbget.net/Extension_scripts

Simplified Development
======================
The following are some of the functionality that is built in for you:

 * validate() - handle environment checking, correct versioning as well
                as if the expected configuration variables you specified
                are present.

 * health_check() - Checks the status of the retrieved content, currently
                this is only useful during Post-Processing

 * push()     - pushes a variables to the NZBGet server


 * set()/get()- Hash table get/set attributes that can be set in one script
                and then later retrieved from another. get() can also
                be used to fetch content that was previously pushed using
                the push() tool. You no longer need to work with environment
                variables. If you enable the SQLite database, set content is
                put here as well so that it can be retrieved by another
                script.

 * unset()    - This allows you to unset values set by set() and get() as well
                as ones set by push()

 * nzb_set()  - Similar to the set() function identified above except it
                is used to build an nzb meta hash table which can be later
                pushed to the server using push_dnzb().

 * nzb_get()  - Retieves NZB Meta information previously stored.

 * nzb_unset()- Removes a variable previously set completely.

 * get_api()  - Retreive a simple API/RPC object built from the global
                variables NZBGet passes into an external program when
                called.

 * get_files()- list all files in a specified directory as well as fetching
                their details such as filesize, modified date, etc in an
                easy to reference dictionary.  You can provide a ton of
                different filters to minimize the content returned. Filters
                can by a regular expression, file prefixes, and/or suffixes.

 * parse_nzbfile() - Parse an NZB-File and extract all of its meta
                     information from it. lxml must be installed on your
                     system for this to work correctly

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

 * push_dnzb() - You can push all nzb meta information onbtained to
                  the NZBGet server as DNZB_ meta tags.

 * pull_dnzb() - Pull all DNZB_ meta tags issued by the server and
                 return their values in a dictionary.
                  if no  DNZB_ (NZB Meta information) was found, then an
                  empty dictionary is returned instead.

 * deobfuscate() - Take a filename and return it in a deobfuscated to the
                   best of its ability. (_PostProcessScript_ only)

How To Use
==========
* Developers are only required to define a class that inherits the NZBGet class
that identifies what they are attempting to write (_ScanScript_,
_PostProcessScript_, etc.).

* Then you write all of your code a the _main()_ you must define.

Post Process Script Example
===========================
```
#############################################################################
### NZBGET POST-PROCESSING SCRIPT                                         ###
#
# Author: Your Name Goes Here <your@email.address>
#
# Describe your Post-Process Script here
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
        # write all of your code here you would have otherwise put in the
        # script

        if not self.validate():
            # No need to document a failure, validate will do that
            # on the reason it failed anyway
            return False

        # All system environment variables (NZBOP_.*) as well as Post
        # Process script specific content (NZBPP_.*)
        # following dictionary (without the NZBOP_ or NZBPP_ prefix):
        print 'DIRECTORY %s' self.get('DIRECTORY')
        print 'NZBNAME %s' self.get('NZBNAME')
        print 'NZBFILENAME %s' self.get('NZBFILENAME')
        print 'CATEGORY %s' self.get('CATEGORY')
        print 'TOTALSTATUS %s' self.get('TOTALSTATUS')
        print 'STATUS %s' self.get('STATUS')
        print 'SCRIPTSTATUS %s' self.get('SCRIPTSTATUS')

        # Set any variable you want by any key.  Note that if you use
        # keys that were defined by the system (such as CATEGORY, DIRECTORY,
        # etc, you may have some undesirable results.  Try to avoid reusing
        # system variables already defined (identified above):
        self.set('MY_KEY', 'MY_VALUE')

        # You can fetch it back; this will also set an entry in  the
        # sqlite database for each hash references that can be pulled from
        # another script that simply calls self.get('MY_VAR')
        print self.get('MY_KEY') # prints MY_VALUE

        # You can also use push() which is similar to set()
        # except that it interacts with the NZBGet Server and does not use
        # the sqlite database. This can only be reached across other
        # scripts if the calling application is NZBGet itself
        self.push('ANOTHER_KEY', 'ANOTHER_VALUE')

        # You can still however locally retrieve what you set using push()
        # with the get() function
        print self.get('ANOTHER_KEY') # prints ANOTHER_VALUE

        # Your script configuration files (NZBPP_.*) are here in this
        # dictionary (again without the NZBPP_ prefix):
        # assume you defined `Debug=no` in the first 10K of your PostProcessScript
        # NZBGet translates this to `NZBPP_DEBUG` which can be retrieved
        # as follows:
        print 'DEBUG %s' self.get('DEBUG')

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
    ppscript = MyPostProcessScript()

    # call run() and exit() using it's returned value
    exit(ppscript.run())
```

Scan Script Example
===================
```
############################################################################
### NZBGET SCAN SCRIPT                                                   ###
#
# Author: Your Name Goes Here <your@email.address>
#
# Describe your Scan Script here
#

############################################################################
### OPTIONS                                                              ###

#
# Enable NZBGet debug logging (yes, no)
# Debug=no
#

### NZBGET SCAN SCRIPT                                                   ###
############################################################################

from nzbget import ScanScript

# Now define your class while inheriting the rest
class MyScanScript(ScanScript):
    def main(self, *args, **kwargs):
        # write all of your code here you would have otherwise put in the
        # script

        if not self.validate():
            # No need to document a failure, validate will do that
            # on the reason it failed anyway
            return False

        # All system environment variables (NZBOP_.*) as well as Post
        # Process script specific content (NZBNP_.*)
        # following dictionary (without the NZBOP_ or NZBNP_ prefix):
        print 'DIRECTORY %s' self.get('DIRECTORY')
        print 'FILENAME %s' self.get('FILENAME')
        print 'NZBNAME %s' self.get('NZBNAME')
        print 'CATEGORY %s' self.get('CATEGORY')
        print 'PRIORITY %s' self.get('PRIORITY')
        print 'TOP %s' self.get('TOP')
        print 'PAUSED %s' self.get('PAUSED')

        return True

# Call your script as follows:
if __name__ == "__main__":
    from sys import exit

    # Create an instance of your Script
    scanscript = MyScanScript()

    # call run() and exit() using it's returned value
    exit(scanscript.run())
```

Scheduler Script Example
=======================
```
############################################################################
### NZBGET SCHEDULER SCRIPT                                               ###
#
# Describe your Schedule Script here
# Author: Your Name Goes Here <your@email.address>
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
        print 'DESTDIR %s' self.get('DESTDIR')

        return True
# Call your script as follows:
if __name__ == "__main__":
    from sys import exit

    # Create an instance of your Script
    myscript = MySchedulerScript()

    # call run() and exit() using it's returned value
    exit(myscript.run())
```

MultiScript Example
=======================
```
############################################################################
### NZBGET POST-PROCESSING/SCHEDULER SCRIPT                              ###
#
# Describe your Multi Script here
#
# Author: Your Name Goes Here <your@email.address>
#

############################################################################
### OPTIONS                                                              ###

#
# Enable NZBGet debug logging (yes, no)
# Debug=no
#

### NZBGET POST-PROCESSING/SCHEDULER SCRIPT                              ###
############################################################################

from nzbget import PostProcessScript
from nzbget import SchedulerScript

# Now define your class while inheriting the rest
class MyMultiScript(PostProcessScript, SchedulerScript):

    def postprocess_main(self, *args, **kwargs):

        # Version Checking, Environment Variables Present, etc
        if not self.validate():
            # No need to document a failure, validate will do that
            # on the reason it failed anyway
            return False

        # write your main function for your Post Processing

        return True

    def scheduler_main(self, *args, **kwargs):

        # Version Checking, Environment Variables Present, etc
        if not self.validate():
            # No need to document a failure, validate will do that
            # on the reason it failed anyway
            return False

        # write your main function for your Post Processing

        return True

# Call your script as follows:
if __name__ == "__main__":
    from sys import exit

    # Create an instance of your Script
    myscript = MyMultiScript()

    # call run() and exit() using it's returned value
    exit(myscript.run())
```

Notify Processing Script
========================
This script was intended to be an [NZBGet](http://nzbget.net) _post-processing_
wrapper to different forms of notification services.

Installation Instructions
=========================
1. Ensure you have at least Python v2.6 or higher installed onto your system.
2. Simply place the __Notify.py__ and __Notify directory together.
   * __NZBGet users__: you'll want to place these inside of your _nzbget/scripts_ directory. Please ensure you are running _(at least)_ NZBGet v11.0 or higher. You can acquire the latest version of of it from [here](http://nzbget.net/download).

The Non-NZBGet users can also use this script from the command line.
See the __Command Line__ section below for more instructions on how to do this.

**Note:** The _Notify_ directory provides all of the nessisary dependencies
in order for this script to work correctly. The directory is only required
if you do not have the packages already available to your global
environment. These dependant packages are all identified under the
_Dependencies_ section below.

Supported Notify Services
=========================
The table below identifies the provider _Notify.py_ supports and the
location that content is retrieved from.

| Service | Service ID | Default Port |
| ------- | ---------- | ------------ |
| Growl   | growl://   | (UDP) 9887   |
| XBMC    | xbmc://    | (TCP) 8080   |

Dependencies
============
The following dependencies are already provided for you within the
_Notify_ directory and no further effort is required by you. However, it
should be known that Notify.py depends on the following packages:

| Name                         | Version | Source                                                                               |
| ---------------------------- |:------- |:------------------------------------------------------------------------------------ |
| backports-ssl_match_hostname | 3.4.0.2 | https://pypi.python.org/pypi/backports.ssl_match_hostname/3.4.0.2                    |
| chardet                      | 2.2.1   | https://pypi.python.org/pypi/chardet/2.2.1                                           |
| ndg-httpsclient              | 0.3.2   | https://pypi.python.org/pypi/ndg-httpsclient/0.3.2                                   |
| ordereddict                  | 1.1     | https://pypi.python.org/pypi/ordereddict/1.1                                         |
| pynzbget                     | 0.2.1   | https://pypi.python.org/pypi/pynzbget/0.2.1                                          |
| requests **[P]**             | 2.3.0   | https://pypi.python.org/pypi/requests/2.3.0                                          |
| six                          | 1.6.1   | https://pypi.python.org/pypi/six/1.6.1                                               |
| pyasn1                       | 0.1.7   | https://pypi.python.org/pypi/pyasn1/0.1.7                                            |
| pyOpenSSL                    | 0.14    | https://pypi.python.org/pypi/pyOpenSSL/0.14                                          |
| netgrowl                     | 0.6.3   | http://the.taoofmac.com      pyOpenSSL/0.14                                          |
| urllib3 **[P]**              | 1.9     | https://pypi.python.org/pypi/urllib3/1.9                                             |

**Note:** The items above denoted with a **[P]** were patched in efforts to:
- Make their libaries compatible with Python v2.6.
- Fix bugs to add stability to the overall functionality.
- Add the nessesary enhancments that benifit this wrapper tool.

To be as transparent as possible, all patches have been provided in the
[_/patches_](https://github.com/caronc/nzbget-notify/tree/master/patches) directory.

Command Line
============
Notify.py has a built in command line interface that can be easily tied
to a cron entry or can be easilly called from the command line to automate
the fetching of subtitles.

Here are the switches available to you:
```
Usage: Notify.py [options]

Options:
  -h, --help            show this help message and exit
  -s URL(s), --servers=URL(s)
                        Specify 1 or more servers in their URL format ie:
                        growl://mypass@localhostthe command line.
  -t TITLE, --title=TITLE
                        Specify the title of the notification message.
  -b BODY, --body=BODY  Specify the body of the notification message.
  -L FILE, --logfile=FILE
                        Send output to the specified logfile instead of
                        stdout.
  -D, --debug           Debug Mode

```

Here is simple example:
```bash
# Send a notification to XBMC (assuming its listening on
# port 8080 at the ip 192.168.0.2 with respect to the example
# below:
python Notify.py -s xbmc://192.168.0.2
```

You can scan multiple directories with the following command:
```bash
# Scan a single directory (recursively) for english subtitles
python Notify.py -s -f -S "/usr/share/TVShows, /usr/share/Movies"
```

Another nice feature this tool offers is the ability to _expire_ the
need to check certain content over and over again.  Considering that most of
us keep all our videos in one common location.  It would be excessive overkill
to poll the internet each and every time for each and every file we have (for
subtitles) over and over again.  We can assume, that if there are no subtitles for
a given video within the _last 24 hours_ of it's existance on our system, then there
simply aren't going to be any later. _I realize this isn't always the case; but
for most situations it will be._

In the above examples, I provided a __--force__ (__-f__) switch which bypasses
this feature. But if you want to set up a cron entry to scan your library on
a regular basis, this feature can save you time and effort. A cron could be
easily configured to scan your library every hour as so:
```bash
# $> crontab -e
0 * * * * /path/to/Notify.py -s -S "/usr/share/TVShows, /usr/share/Movies"
```
If 24 hours seems to short of a window for you, then just specify the
__--age__ (__-a__) switch and adjust the time to your needs. Remember: it's
value is represented in hours.

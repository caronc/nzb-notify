Notify Processing Script
========================
This script was intended to be an [NZBGet](http://nzbget.net) _post-processing_
wrapper to different forms of notification services. But the script works fine as standalone tool for anyone else too!

NZBGet users can be notified on supported devices of the status of a download
they made.  Non-NZBGet users can also use this tool as a standalone app that
can message their devices as they please.

Installation Instructions
=========================
1. Ensure you have at least Python v2.6 or higher installed onto your system.
2. Simply place the __Notify.py__ and __Notify__ directory together.
   * __NZBGet users__: you'll want to place these inside of your _nzbget/scripts_ directory. Please ensure you are running _(at least)_ NZBGet v11.0 or higher. You can acquire the latest version of of it from [here](http://nzbget.net/download).
   * __NZBGet users__: As one additional note; this script makes use of the RPC feature of NZBGet in order to retrive all of the status information it will notify you with.  Its very important that this is configured correctly (in the 'Settings -> Security' area). The out of the box settings should work fine; but worth noting here should experience any issues.

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

| Notification Service | Service ID | Default Port | Example Syntax |
| -------------------- | ---------- | ------------ | -------------- |
| [Boxcar](https://boxcar.io/)  | boxcar://   | (TCP) 443   | boxcar://hostname<br />boxcar://hostname/@tag<br/>boxcar://hostname/device_token<br />boxcar://hostname/device_token1/device_token2/device_tokenN<br />boxcar://hostname/alias<br />boxcar://hostname/@tag/@tag2/alias/device_token
| [Growl](http://growl.info/)  | growl://   | (UDP) 23053   | growl://hostname<br />growl://hostname:portno
| [Faast](http://faast.io/) | faast://    | (TCP) 443    | faast://authorizationtoken
| JSON (Simple)        | json:// or jsons://   | (TCP) 80 or 443 | json://hostname<br />json://user@hostname<br />json://user:password@hostname:port<br />json://hostname/a/path/to/post/to
| [KODI](http://kodi.tv/) | kodi:// or kodis://    | (TCP) 8080 or 443   | kodi://hostname<br />kodi://user@hostname<br />kodi://user:password@hostname:port
| [Notify My Android](http://www.notifymyandroid.com/) | nma://   | (TCP) 443    | nma://apikey
| [Prowl](http://www.prowlapp.com/) | prowl://   | (TCP) 443    | prowl://apikey<br />prowl://apikey/providerkey
| [Pushalot](https://pushalot.com/) | palot://    | (TCP) 443    | palot://authorizationtoken
| [PushBullet](https://www.pushbullet.com/) | pbul://    | (TCP) 443    | pbul://accesstoken<br />pbul://accesstoken/#channel<br/>pbul://accesstoken/A_DEVICE_ID<br />pbul://accesstoken/email@address.com<br />pbul://accesstoken/#channel/#channel2/email@address.net/DEVICE
| [Pushover](https://pushover.net/)  | pover://   | (TCP) 443   | pover://user@token<br />pover://user@token/DEVICE<br />pover://user@token/DEVICE1/DEVICE2/DEVICEN<br />_Note: you must specify both your user_id and token_
| [Toasty](http://api.supertoasty.com/)  | toasty://   | (TCP) 80   | toasty://user@DEVICE<br />toasty://user@DEVICE1/DEVICE2/DEVICEN<br />_Note: you must specify both your user_id and at least 1 device!_
| [XBMC](http://kodi.tv/) | xbmc:// or xbmcs://    | (TCP) 8080 or 443   | xbmc://hostname<br />xbmc://user@hostname<br />xbmc://user:password@hostname:port
| XML (Simple)        | xml:// or xmls://   | (TCP) 80 or 443 | xml://hostname<br />xml://user@hostname<br />xml://user:password@hostname:port<br />xml://hostname/a/path/to/post/to

It also just supports straight forward emailing too:

| Service ID | Default Port | Example Syntax |
| ---------- | ------------ | -------------- |
| mailto://  |  (TCP) 25    | mailto://userid:pass@domain.com<br />mailto://domain.com?user=userid&pass=password<br/>mailto://domain.com:2525?user=userid&pass=password<br />mailto://user@gmail.com&pass=password<br />mailto://userid:password@example.com?smtp=mail.example.com&from=noreply@example.com&name=no%20reply
| mailtos:// |  (TCP) 587   | mailtos://userid:pass@domain.com<br />mailtos://domain.com?user=userid&pass=password<br/>mailtos://domain.com:465?user=userid&pass=password<br />mailtos://user@hotmail.com&pass=password<br />mailtos://userid:password@example.com?smtp=mail.example.com&from=noreply@example.com&name=no%20reply

Common supported services where the smtp port, server, userid structure, and security is already known are as follows:
* Google - __mailtos://userid:pass@gmail.com__  knows to use a secure connection (even if you specify mailto://) and to use the smtp server (mail.google.com) and appropriate secure port (587).  It also automatically constructs your userid as being userid@gmail.com. __Note:__ If you're using 2 way authentication, you'll need to [generate an app password](https://security.google.com/settings/security/apppasswords)
* Hotmail - __mailtos://userid:pass@hotmail.com__ or __mailtos://userid:pass@live.com__ knows to use a secure connection (even if you specify mailto://) and to use the smtp server smtp.live.com and appropriate secure port (465).  It also automatically constructs your userid as being userid@live.com or userid@hotmail.com depending on what you identified.
* Yahoo - __mailtos://userid:pass@yahoo.com__ knows to use a secure connection (even if you specify mailto://) and to use the smtp server smtp.live.com and appropriate secure port (587).  It also automatically constructs your userid as being userid@yahoo.com or userid@yahoo.ca depending on what you identified.

To eliminate any confusion, any url parameter (key=value) specified will over-ride what was detected in the url; hence:
* mailto://usera:pass123@domain.com?user=foobar@domain.com: the userid of _foobar_ would over-ride the userid _usera_ specified.  However since the password was not over-ridden, the password of _pass123_ would be used still.

Dependencies
============
The following dependencies are already provided for you within the
_Notify_ directory and no further effort is required by you. However, it
should be known that Notify.py depends on the following packages:

| Name                         | Version | Source                                                                               |
| ---------------------------- |:------- |:------------------------------------------------------------------------------------ |
| backports-ssl_match_hostname | 3.4.0.2 | https://pypi.python.org/pypi/backports.ssl_match_hostname/3.4.0.2                    |
| chardet                      | 2.2.1   | https://pypi.python.org/pypi/chardet/2.2.1                                           |
| importlib                    | 1.0.1   | https://pypi.python.org/pypi/importlib/1.0.1                                         |
| *markdown                    | 2.5.1   | https://github.com/EnTeQuAk/Python-Markdown/tree/feature/py26                        |
| ndg-httpsclient              | 0.3.2   | https://pypi.python.org/pypi/ndg-httpsclient/0.3.2                                   |
| ordereddict                  | 1.1     | https://pypi.python.org/pypi/ordereddict/1.1                                         |
| pynzbget                     | 0.2.3   | https://pypi.python.org/pypi/pynzbget/0.2.3                                          |
| requests **[P]**             | 2.3.0   | https://pypi.python.org/pypi/requests/2.3.0                                          |
| six                          | 1.6.1   | https://pypi.python.org/pypi/six/1.6.1                                               |
| pyasn1                       | 0.1.7   | https://pypi.python.org/pypi/pyasn1/0.1.7                                            |
| pyOpenSSL **[P]**            | 0.14    | https://pypi.python.org/pypi/pyOpenSSL/0.14                                          |
| gntp                         | 1.0.2   | https://pypi.python.org/pypi/gntp/1.0.2                                              |
| urllib3 **[P]**              | 1.9     | https://pypi.python.org/pypi/urllib3/1.9                                             |

**Note:** The items above denoted with a **[P]** were patched in efforts to:
- Make their libaries compatible with Python v2.6.
- Fix bugs to add stability to the overall functionality.
- Add the nessesary enhancments that benifit this wrapper tool.

John Gruber's python _markdown_ is officially available [here](https://github.com/waylan/Python-Markdown), but I chose to use [this fork](https://github.com/EnTeQuAk/Python-Markdown/tree/feature/py26) (by [EnTeQuAk](https://github.com/EnTeQuAk) instead because it was backported to work with Python v2.6. The ticket [here](https://github.com/waylan/Python-Markdown/issues/345) explains the reasoning.

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
                        growl://mypass@localhost
  -t TITLE, --title=TITLE
                        Specify the title of the notification message.
  -b BODY, --body=BODY  Specify the body of the notification message.
  -i, --include_image   Include image in message if the protocol supports it.
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
python Notify.py -s xbmc://192.168.0.2 -t "Hello" -b "World!"

# you can also use it's new name (kodi) to achive the same
# results:
python Notify.py -s kodi://192.168.0.2 -t "Hello" -b "World!"
```

You can also mix and match as many servers as you want by separating
your urls with a comma and/or space.
```bash
# Send a notification to XBMC and a Growl Server
python Notify.py \
    -s growl://192.168.0.10,xbmc://user:pass@192.168.0.2 \
    -t "Hello" -b "World!"
```

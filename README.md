__Note:__ This script was originally written to be an [NZBGet](http://nzbget.net) _post-processing_ script notifying you of retrieved content through a variety of different notification services. But will work for SABnzbd users (starting at v1.1.0+) as well. The script additionally works fine as standalone tool for anyone else too! See the _Command Line_ section below for details how you can easily use this on it's own (without NZBGet).

SABnzbd users can reference sabnzbd-notify.py to gain support of the tool as well.

[![Paypal](http://repo.nuxref.com/pub/img/paypaldonate.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=MHANV39UZNQ5E)

## Built on Apprise

This guts of this script have been recently extracted into it's own project called [Apprise](https://github.com/caronc/apprise) which allows others to build Notifications into their applications as well.

## Notify Processing Script

Send notifications to all of the popular notification services (PushBullet, NotifyMyAndroid, XBMC, Email etc). NZBGet (and/or SABnzbd) will automatically notify you of anything it downloads. You can chain as many notification services as you want and support most of the advance features each service offers you too.

You can even run the tool from the command line for your own custom use. Notify.py was written in such a way that there wouldn't be a lot of effort to add more notification services either.  Feel free to contact me if one you would like to use is missing.

## Installation Instructions

1. Ensure you have Python v2.7 or later installed onto your system.
```bash
# Pull in dependencies:
pip install -r requirements.txt
```
2. Simply place the __Notify.py__ and __Notify__ directory together.
   * __NZBGet users__: you'll want to place these inside of your _nzbget/scripts_ directory. Please ensure you are running _(at least)_ NZBGet v11.0 or higher. You can acquire the latest version of of it from [here](http://nzbget.net/download).
   * __NZBGet users__: As one additional note; this script makes use of the RPC feature of NZBGet in order to retrive all of the status information it will notify you with.  Its very important that this is configured correctly (in the 'Settings -> Security' area). The out of the box settings should work fine; but worth noting here should experience any issues.
   * __SABnzbd users__: You'll point your SABnzbd configuration to reference sabnzbd-notify.py via the _Script_ entry and _not_ Notify.py. However, please note that the Notify.py script is still required (as sabnzbd-notify.py is a wrapper to it).  You will use the _Parameters_ section to provide the services you wish to notify (see below how they are constructed).

The Non-NZBGet/SABnzbd users can also use this script from the command line.
See the __Command Line__ section below for more instructions on how to do this.

## Supported Notifications

**For a complete list of supported notification services and examples on how to build their URLs [click here](https://github.com/caronc/apprise/wiki#notification-services)**. 

## Command Line

**Notify.py** has a built in command line interface that can be easily tied
to a cron entry or can be easily called from the command line to automate
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
  -u IMAGE_URL, --image_url=IMAGE_URL
                        Provide url to image; should be either http://,
                        https://, or file://. This option implies that
                        --include_image (-i) is set automatically
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

## SABnzbd Users
SABnzbd users can test that their script is working okay manually as well if they're having issues with it through their application.  This is also a great way to test out that you've created the correct URL string.
```bash
# Send a notification to XBMC (assuming its listening on
# port 8080 at the ip 192.168.0.2 with respect to the example
# below:
python sabnzbd-notify.py complete 'Hello' 'World' xbmc://192.168.0.2
```
The syntax is very similar except SABnzbd expects 4 distinct arguments.

| Arg # | Description |
| ----- |:----------- |
|   1   | The type of notification we are sending.  This has an impact on the icon (for those that support it) that you will pass along with the message.
|   2   | The title of the notification message.  If this is an empty string, then there is enough information based on the notification type you passed in (argument 1) to generate a title. |
|   3   | The message body. |
|   4   | Comma delimited URL strings just like the ones already discussed above.

### SABnzbd Configuration
First, make sure you've placed __sabnzb-notify.py__, __Notify.py__, and the __Notify__ inside of the _/path/to/SABnzbd/scripts/_ directory or the instructions below will not work.

Once you know the _URL_(s) that work for you, you can set SABnzbd to automatically notify setting it up as follows. From within SABnzbd's web interface:

- Click on __Settings__
- Click on __Notifications__
- Place a checkbox in the __Enable notification script__ option.
- Choose __sabnzb-notify.py__ from the Script dropdown menu.
- Specify the URL such as kodi://192.168.0.2 in the _Parameters_ section. You can specify more then one URL here by simply using a _comma_ (,) as a delimiter.

CentOS/RedHat users can also refer to a [blog entry I prepared](http://nuxref.com/2016/10/20/sabnzbd-installation-centos-7/) for this which includes RPM packaging for both [SABnzbd](http://repo.nuxref.com/centos/7/en/x86_64/custom/repoview/sabnzbd.html) and [NZB-Notify](http://repo.nuxref.com/centos/7/en/x86_64/custom/repoview/sabnzbd-script-notify.html). These can be easily installed (with all required dependencies by just getting yourself set up with my repository [here](http://nuxref.com/nuxref-repository/).

## Donations
If you like this script and feel like donating, you can do so through either [PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=MHANV39UZNQ5E) or [sponsor me](https://github.com/sponsors/caronc)! Thank you so much to everyone who has donated in the past!

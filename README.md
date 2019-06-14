__Note:__ This script was originally written to be an [NZBGet](http://nzbget.net) _post-processing_ script notifying you of retrieved content through a variety of different notification services. But will work for SABnzbd users (starting at v1.1.0+) as well. The script additionally works fine as standalone tool for anyone else too! See the _Command Line_ section below for details how you can easily use this on it's own (without NZBGet).

SABnzbd users can reference sabnzbd-notify.py to gain support of the tool as well.

[![Paypal](http://repo.nuxref.com/pub/img/paypaldonate.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=MHANV39UZNQ5E)
[![Patreon](http://repo.nuxref.com/pub/img/patreondonate.svg)](https://www.patreon.com/caronc)

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
The section identifies all of the services supported by this script.

### Popular Notification Services
The table below identifies the provider _Notify.py_ supports and the
location that content is retrieved from.

| Notification Service | Service ID | Default Port | Example Syntax |
| -------------------- | ---------- | ------------ | -------------- |
| [AWS SNS](https://github.com/caronc/apprise/wiki/Notify_sns)  | sns://   | (TCP) 443   | sns://AccessKeyID/AccessSecretKey/RegionName/+PhoneNo<br/>sns://AccessKeyID/AccessSecretKey/RegionName/+PhoneNo1/+PhoneNo2/+PhoneNoN<br/>sns://AccessKeyID/AccessSecretKey/RegionName/Topic<br/>sns://AccessKeyID/AccessSecretKey/RegionName/Topic1/Topic2/TopicN
| [Boxcar](https://github.com/caronc/apprise/wiki/Notify_boxcar)  | boxcar://   | (TCP) 443   | boxcar://hostname<br />boxcar://hostname/@tag<br/>boxcar://hostname/device_token<br />boxcar://hostname/device_token1/device_token2/device_tokenN<br />boxcar://hostname/@tag/@tag2/device_token
| [Discord](https://github.com/caronc/apprise/wiki/Notify_discord)  | discord://   | (TCP) 443   | discord://webhook_id/webhook_token<br />discord://avatar@webhook_id/webhook_token
| [Dbus](https://github.com/caronc/apprise/wiki/Notify_dbus)  | dbus://<br />qt://<br />glib://<br />kde://  | n/a  | dbus://<br />qt://<br />glib://<br />kde://
| [Emby](https://github.com/caronc/apprise/wiki/Notify_emby)  | emby:// or embys:// | (TCP) 8096 | emby://user@hostname/<br />emby://user:password@hostname
| [Faast](https://github.com/caronc/apprise/wiki/Notify_faast) | faast://    | (TCP) 443    | faast://authorizationtoken
| [Gnome](https://github.com/caronc/apprise/wiki/Notify_gnome) | gnome://    |        n/a          | gnome://
| [Growl](https://github.com/caronc/apprise/wiki/Notify_growl)  | growl://   | (UDP) 23053   | growl://hostname<br />growl://hostname:portno<br />growl://password@hostname<br />growl://password@hostname:port</br>**Note**: you can also use the get parameter _version_ which can allow the growl request to behave using the older v1.x protocol. An example would look like: growl://hostname?version=1
| [IFTTT](https://github.com/caronc/apprise/wiki/Notify_ifttt) | ifttt://    | (TCP) 443    | ifttt://webhooksID/EventToTrigger<br />ifttt://webhooksID/EventToTrigger/Value1/Value2/Value3<br />ifttt://webhooksID/EventToTrigger/?Value3=NewEntry&Value2=AnotherValue
| [Join](https://github.com/caronc/apprise/wiki/Notify_join) | join://   | (TCP) 443    | join://apikey/device<br />join://apikey/device1/device2/deviceN/<br />join://apikey/group<br />join://apikey/groupA/groupB/groupN<br />join://apikey/DeviceA/groupA/groupN/DeviceN/
| [KODI](https://github.com/caronc/apprise/wiki/Notify_kodi) | kodi:// or kodis://    | (TCP) 8080 or 443   | kodi://hostname<br />kodi://user@hostname<br />kodi://user:password@hostname:port
| [Matrix](https://github.com/caronc/apprise/wiki/Notify_matrix) | matrix:// or matrixs://  | (TCP) 80 or 443 | matrix://token<br />matrix://user@token<br />matrixs://token?mode=slack<br />matrixs://user@token
| [Mattermost](https://github.com/caronc/apprise/wiki/Notify_mattermost) | mmost://  | (TCP) 8065 | mmost://hostname/authkey<br />mmost://hostname:80/authkey<br />mmost://user@hostname:80/authkey<br />mmost://hostname/authkey?channel=channel<br />mmosts://hostname/authkey<br />mmosts://user@hostname/authkey<br />
| [Prowl](https://github.com/caronc/apprise/wiki/Notify_prowl) | prowl://   | (TCP) 443    | prowl://apikey<br />prowl://apikey/providerkey
| [PushBullet](https://github.com/caronc/apprise/wiki/Notify_pushbullet) | pbul://    | (TCP) 443    | pbul://accesstoken<br />pbul://accesstoken/#channel<br/>pbul://accesstoken/A_DEVICE_ID<br />pbul://accesstoken/email@address.com<br />pbul://accesstoken/#channel/#channel2/email@address.net/DEVICE
| [Pushjet](https://github.com/caronc/apprise/wiki/Notify_pushjet) | pjet:// or pjets:// | (TCP) 80 or 443 | pjet://secret@hostname<br />pjet://secret@hostname:port<br />pjets://secret@hostname<br />pjets://secret@hostname:port
| [Pushed](https://github.com/caronc/apprise/wiki/Notify_pushed) | pushed://    | (TCP) 443    | pushed://appkey/appsecret/<br/>pushed://appkey/appsecret/#ChannelAlias<br/>pushed://appkey/appsecret/#ChannelAlias1/#ChannelAlias2/#ChannelAliasN<br/>pushed://appkey/appsecret/@UserPushedID<br/>pushed://appkey/appsecret/@UserPushedID1/@UserPushedID2/@UserPushedIDN
| [Pushover](https://github.com/caronc/apprise/wiki/Notify_pushover)  | pover://   | (TCP) 443   | pover://user@token<br />pover://user@token/DEVICE<br />pover://user@token/DEVICE1/DEVICE2/DEVICEN<br />_Note: you must specify both your user_id and token_
| [Rocket.Chat](https://github.com/caronc/apprise/wiki/Notify_rocketchat) | rocket:// or rockets://  | (TCP) 80 or 443   | rocket://user:password@hostname/RoomID/Channel<br />rockets://user:password@hostname:443/Channel1/Channel1/RoomID<br />rocket://user:password@hostname/Channel
| [Ryver](https://github.com/caronc/apprise/wiki/Notify_ryver) | ryver://  | (TCP) 443   | ryver://Organization/Token<br />ryver://botname@Organization/Token
| [Slack](https://github.com/caronc/apprise/wiki/Notify_slack) | slack://  | (TCP) 443   | slack://TokenA/TokenB/TokenC/Channel<br />slack://botname@TokenA/TokenB/TokenC/Channel<br />slack://user@TokenA/TokenB/TokenC/Channel1/Channel2/ChannelN
| [Telegram](https://github.com/caronc/apprise/wiki/Notify_telegram) | tgram://  | (TCP) 443   | tgram://bottoken/ChatID<br />tgram://bottoken/ChatID1/ChatID2/ChatIDN
| [Twitter](https://github.com/caronc/apprise/wiki/Notify_twitter) | tweet://  | (TCP) 443   | tweet://user@CKey/CSecret/AKey/ASecret
| [XBMC](https://github.com/caronc/apprise/wiki/Notify_xbmc) | xbmc:// or xbmcs://    | (TCP) 8080 or 443   | xbmc://hostname<br />xbmc://user@hostname<br />xbmc://user:password@hostname:port
| [Windows Notification](https://github.com/caronc/apprise/wiki/Notify_windows) | windows://    |        n/a          | windows://


### Email Support
| Service ID | Default Port | Example Syntax |
| ---------- | ------------ | -------------- |
| [mailto://](https://github.com/caronc/apprise/wiki/Notify_email)  |  (TCP) 25    | mailto://userid:pass@domain.com<br />mailto://domain.com?user=userid&pass=password<br/>mailto://domain.com:2525?user=userid&pass=password<br />mailto://user@gmail.com&pass=password<br />mailto://mySendingUsername:mySendingPassword@example.com?to=receivingAddress@example.com<br />mailto://userid:password@example.com?smtp=mail.example.com&from=noreply@example.com&name=no%20reply
| [mailtos://](https://github.com/caronc/apprise/wiki/Notify_email) |  (TCP) 587   | mailtos://userid:pass@domain.com<br />mailtos://domain.com?user=userid&pass=password<br/>mailtos://domain.com:465?user=userid&pass=password<br />mailtos://user@hotmail.com&pass=password<br />mailtos://mySendingUsername:mySendingPassword@example.com?to=receivingAddress@example.com<br />mailtos://userid:password@example.com?smtp=mail.example.com&from=noreply@example.com&name=no%20reply

Apprise have some email services built right into it (such as yahoo, fastmail, hotmail, gmail, etc) that greatly simplify the mailto:// service.  See more details [here](https://github.com/caronc/apprise/wiki/Notify_email).

### Custom Notifications
| Post Method          | Service ID | Default Port | Example Syntax |
| -------------------- | ---------- | ------------ | -------------- |
| [JSON](https://github.com/caronc/apprise/wiki/Notify_Custom_JSON)       | json:// or jsons://   | (TCP) 80 or 443 | json://hostname<br />json://user@hostname<br />json://user:password@hostname:port<br />json://hostname/a/path/to/post/to
| [XML](https://github.com/caronc/apprise/wiki/Notify_Custom_XML)         | xml:// or xmls://   | (TCP) 80 or 443 | xml://hostname<br />xml://user@hostname<br />xml://user:password@hostname:port<br />xml://hostname/a/path/to/post/to

**For a complete list of supported notification services, check out what is listed for [Apprise](https://github.com/caronc/apprise/).

## Command Line
Notify.py has a built in command line interface that can be easily tied
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
If you like this script and feel like donating, you can do so through either [PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=MHANV39UZNQ5E) or [Patreon](https://www.patreon.com/lead2gold)! Thank you so much to everyone who has donated in the past!

## Patching
Please note that all of the patches identified here have already been applied
to the libraries included with nzbget-notify (this repository).  Hence If you
are (or have already) downloading nzbget-notify, then you do not need to keep
this directory at all.

The only reason this __patches__ directory exists for developer transparency.
The content in this directory is just a means of sharing changes I made with other
developers who may be otherwise interested.

There were several libraries patched for various reasons:
* To allow systems running Python v2.6 to still take advantage of the libraries. Previously most of these python libraries only worked with Python v2.7 or higher. This grants us access to a larger audience.
* To add enhancements and/or to address outstanding bugfixes that I felt were nessisary to apply.

The patches identified are exclusive the version they were created against and
will most likely not work if applied against anything else.

### Requests v2.3.0
Requests greatly simplifies webpage interaction and content extraction in
python. The actual retreival of subtitles is through this library itself.

| Patch | Description |
| ----- | ----------- |
| [requests-use.global.deps.patch](https://github.com/caronc/nzbget-notify/blob/master/patches/requests-use.global.deps.patch) | A patch put in place to eliminate reference to the extra libraries this package includes. This way we can use the ones we're already providing and maintaining instead.

| Request v2.3.0 Source |
| --------------------- |
| https://pypi.python.org/packages/source/r/requests/requests-2.3.0.tar.gz |

You can apply the patch as follows (Linux example):
```bash
# Assuming you have our dependencies fullfilled
# - RedHat/CentOS/Fedora: yum install -y curl tar patch
# - Ubuntu/Debian: sudo apt-get install curl tar patch
#
# Retrieve the package
curl -L -O https://pypi.python.org/packages/source/r/requests/requests-2.3.0.tar.gz

# Retrieve the patch
curl -L -O https://raw.githubusercontent.com/caronc/nzbget-notify/master/patches/requests-use.global.deps.patch

# Extract our downloaded archive
tar xvfz requests-2.3.0.tar.gz

# Apply our patch
patch -d requests-2.3.0 -p1 < requests-use.global.deps.patch

# You're done!
```

### Urllib3 v1.9
Urllib3 is a dependency of Requests (identified above).  It provides web page
interaction simplifying some common steps (which requests then further takes
to another level).

| Patch | Description |
| ----- | ----------- |
| [urllib3-use.global.deps.patch](https://github.com/caronc/nzbget-notify/blob/master/patches/urllib3-use.global.deps.patch) | A patch put in place to eliminate reference to the extra libraries this package includes. This way we can use the ones we're already providing and maintaining instead.

| Request v1.9 Source |
| --------------------- |
| https://pypi.python.org/packages/source/u/urllib3/url.ib3-1.9.tar.gz |

You can apply the patch as follows (Linux example):
```bash
# Assuming you have our dependencies fullfilled
# - RedHat/CentOS/Fedora: yum install -y curl tar patch
# - Ubuntu/Debian: sudo apt-get install curl tar patch
#
# Retrieve the package
curl -L -O https://pypi.python.org/packages/source/u/urllib3/urllib3-1.9.tar.gz

# Retrieve the patch
curl -L -O https://raw.githubusercontent.com/caronc/nzbget-notify/master/patches/urllib3-use.global.deps.patch

# Extract our downloaded archive
tar xvfz urllib3-1.9.tar.gz

# Apply our patch
patch -d urllib3-1.9 -p1 < urllib3-use.global.deps.patch

# You're done!
```

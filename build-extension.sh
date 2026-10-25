#!/usr/bin/env bash
#
# Prepares Notify for NZBGet v23+ (the Extension Manager):
# - build/Notify/ can be copied straight into NZBGet's scripts folder
# - build/notify-<version>-dist.zip is the same thing, ready for a release
#
set -euo pipefail

# Always work from the folder this script lives in
cd "$(dirname "$0")"

# Defines the name of the plugin:
NAME=Notify
OUT="build/${NAME}"
VERSION=$(python3 -c "import json; print(json.load(open('manifest.json'))['version'])")
# Our output file
ZIP="notify-${VERSION}-dist.zip"

# Start fresh
rm -rf build
mkdir -p "${OUT}"

# Copy in the script, its images, the manifest, docs and the locales
cp -r Notify.py Notify manifest.json README.md LICENSE _locales "${OUT}/"

# Install every package Notify needs into lib/, picking versions that
# still work on Python 3.9 (the oldest Python Apprise v2 supports)
python3 -m pip install --quiet --disable-pip-version-check --no-compile \
    --target "${OUT}/lib" --python-version 3.9 --only-binary :all: \
    -r requirements.txt

# Remove what Notify doesn't need to run:
# - lxml only works on the platform that built it (pynzbget doesn't need it)
# - setuptools is an install tool
# - bin/ holds command line tools made for this machine
(
    cd "${OUT}/lib"
    rm -rf bin lxml lxml-*.dist-info \
        setuptools setuptools-*.dist-info pkg_resources \
        _distutils_hack distutils-precedence.pth
)
find "${OUT}" -name __pycache__ -prune -exec rm -rf {} +

# Remove compiled speedups (PyYAML, charset_normalizer). They only work on
# the platform that built them, and both packages run fine without them.
# This keeps the extension working on ARM (Raspberry Pi, most NAS boxes).
find "${OUT}/lib" \( -name '*.so' -o -name '*.pyd' \) -delete

# Zip it up the same way the official extensions are
(cd build && zip -qr "${ZIP}" "${NAME}")

# Write a checksum so people can make sure their download isn't damaged
# (sha256sum on Linux, shasum on macOS)
(
    cd build
    if command -v sha256sum >/dev/null; then
        sha256sum "${ZIP}" > "${ZIP}.sha256"
    else
        shasum -a 256 "${ZIP}" > "${ZIP}.sha256"
    fi
)

echo "Folder:   ${OUT}"
echo "Zip:      build/${ZIP}"
echo "Checksum: build/${ZIP}.sha256"

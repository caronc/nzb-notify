#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import re

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

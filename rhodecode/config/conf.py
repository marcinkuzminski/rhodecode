# -*- coding: utf-8 -*-
"""
    package.rhodecode.config.conf
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Various config settings for RhodeCode

    :created_on: Mar 7, 2012
    :author: marcink
    :copyright: (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
    :license: <name>, see LICENSE_FILE for more details.
"""
from rhodecode import EXTENSIONS

from rhodecode.lib.utils2 import __get_lem


# language map is also used by whoosh indexer, which for those specified
# extensions will index it's content
LANGUAGES_EXTENSIONS_MAP = __get_lem()

#==============================================================================
# WHOOSH INDEX EXTENSIONS
#==============================================================================
# EXTENSIONS WE WANT TO INDEX CONTENT OFF USING WHOOSH
INDEX_EXTENSIONS = LANGUAGES_EXTENSIONS_MAP.keys()

# list of readme files to search in file tree and display in summary
# attached weights defines the search  order lower is first
ALL_READMES = [
    ('readme', 0), ('README', 0), ('Readme', 0),
    ('doc/readme', 1), ('doc/README', 1), ('doc/Readme', 1),
    ('Docs/readme', 2), ('Docs/README', 2), ('Docs/Readme', 2),
    ('DOCS/readme', 2), ('DOCS/README', 2), ('DOCS/Readme', 2),
    ('docs/readme', 2), ('docs/README', 2), ('docs/Readme', 2),
]

# extension together with weights to search lower is first
RST_EXTS = [
    ('', 0), ('.rst', 1), ('.rest', 1),
    ('.RST', 2), ('.REST', 2),
    ('.txt', 3), ('.TXT', 3)
]

MARKDOWN_EXTS = [
    ('.md', 1), ('.MD', 1),
    ('.mkdn', 2), ('.MKDN', 2),
    ('.mdown', 3), ('.MDOWN', 3),
    ('.markdown', 4), ('.MARKDOWN', 4)
]

PLAIN_EXTS = [('.text', 2), ('.TEXT', 2)]

ALL_EXTS = MARKDOWN_EXTS + RST_EXTS + PLAIN_EXTS

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

DATE_FORMAT = "%Y-%m-%d"

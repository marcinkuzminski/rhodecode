.. _backup:

Backing up RhodeCode
====================


Settings
--------

Just copy your .ini file, it contains all RhodeCode settings.

Whoosh index
------------

Whoosh index is located in **/data/index** directory where you installed
RhodeCode ie. the same place where the ini file is located


Database
--------

When using sqlite just copy rhodecode.db.
Any other database engine requires a manual backup operation.

Database backup will contain all gathered statistics
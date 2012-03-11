.. _debugging:

===================
DEBUGGING RHODECODE
===================

If you encountered problems with RhodeCode here are some instructions how to
possibly debug them.

** First make sure you're using the latest version available.**

enable detailed debug
---------------------

RhodeCode uses standard python logging modules to log it's output.
By default only loggers with INFO level are displayed. To enable full output
change `level = DEBUG` for all logging handlers in currently used .ini file. 
After this you can check much more detailed output of actions happening on 
RhodeCode system.


enable interactive debug mode
-----------------------------

To enable interactive debug mode simply 

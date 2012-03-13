.. _debugging:

===================
Debugging RhodeCode
===================

If you encountered problems with RhodeCode here are some instructions how to
possibly debug them.

** First make sure you're using the latest version available.**

enable detailed debug
---------------------

RhodeCode uses standard python logging modules to log it's output.
By default only loggers with INFO level are displayed. To enable full output
change `level = DEBUG` for all logging handlers in currently used .ini file. 
This change will allow to see much more detailed output in the logfile or
console. This generally helps a lot to track issues.


enable interactive debug mode
-----------------------------

To enable interactive debug mode simply comment out `set debug = false` in
.ini file, this will trigger and interactive debugger each time there an
error in browser, or send a http link if error occured in the backend. This
is a great tool for fast debugging as you get a handy python console right
in the web view. ** NEVER ENABLE THIS ON PRODUCTION ** the interactive console
can be a serious security threat to you system.

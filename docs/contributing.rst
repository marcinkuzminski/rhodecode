.. _contributing:

=========================
Contributing to RhodeCode
=========================

If you would like to contribute to RhodeCode, please contact me, any help is
greatly appreciated!

Could I request that you make your source contributions by first forking the
RhodeCode repository on bitbucket_
https://bitbucket.org/marcinkuzminski/rhodecode and then make your changes to
your forked repository. Please post all fixes into **BETA** branch since your 
fix might be already fixed there and i try to merge all fixes from beta into
stable, and not the other way. Finally, when you are finished making a change, 
please send me a pull request.

To run RhodeCode in a development version you always need to install the latest
required libs from `requires.txt` file.

after downloading/pulling RhodeCode make sure you run::

    python setup.py develop

command to install/verify all required packages, and prepare development 
enviroment.


After finishing your changes make sure all tests passes ok. You can run
the testsuite running ``nosetest`` from the project root, or if you use tox
run tox for python2.5-2.7 with multiple database test.

| Thank you for any contributions!
|  Marcin



.. _bitbucket: http://bitbucket.org/

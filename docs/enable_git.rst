.. _enable_git:

Enabling GIT support (beta)
===========================


Git support in RhodeCode 1.1 was disabled due to some instability issues, but
If You would like to test it fell free to re-enable it. To enable GIT just
uncomment git line in rhodecode/__init__.py file

.. code-block:: python
 
   BACKENDS = {
       'hg': 'Mercurial repository',
       #'git': 'Git repository',
   }

.. note::
   Please note that it's not fully stable and it might crash (that's why it 
   was disabled), so be careful about enabling git support. Don't use it in 
   production !
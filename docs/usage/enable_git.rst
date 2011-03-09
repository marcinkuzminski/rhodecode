.. _enable_git:

Enabling GIT support (beta)
===========================


Git support in RhodeCode 1.1 was disabled due to current instability issues. 
However,if you would like to test git support please feel free to re-enable it. 
To re-enable GIT support just uncomment the git line in the 
file **rhodecode/__init__.py**

.. code-block:: python
 
   BACKENDS = {
       'hg': 'Mercurial repository',
       #'git': 'Git repository',
   }

.. note::
   Please note that the git support provided by RhodeCode is not yet fully
   stable and RhodeCode might crash while using git repositories. (That is why
   it is currently disabled.) Thus be careful about enabling git support, and
   certainly don't use it in a production setting!
   
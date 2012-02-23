.. _git_support:

GIT support
===========


Git support in RhodeCode 1.3 was enabled by default. 
Although There are some limitations on git usage.

- No hooks are runned for git push/pull actions.
- logs in action journals don't have git operations
- large pushes needs http server with chunked encoding support.
 
if you plan to use git you need to run RhodeCode with some
http server that supports chunked encoding which git http protocol uses, 
i recommend using waitress_ or gunicorn_ (linux only) for `paste` wsgi app 
replacement.

To use waitress simply change::

    use = egg:Paste#main

To::
    
    use = egg:waitress#main

In you .ini file, then you can simply run `paster serve` as usual.


  
You can always disable git/hg support by editing a 
file **rhodecode/__init__.py** and commenting out backends

.. code-block:: python
 
   BACKENDS = {
       'hg': 'Mercurial repository',
       #'git': 'Git repository',
   }

.. _waitress: http://pypi.python.org/pypi/waitress
.. _gunicorn: http://pypi.python.org/pypi/gunicorn
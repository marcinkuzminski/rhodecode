.. _git_support:

===========
GIT support
===========


Git support in RhodeCode 1.3 was enabled by default. You need to have a git
client installed on the machine to make git fully work.

Although There are some limitations on git usage.

- hooks that are executed on pull/push are not *real* hooks, they are 
  just emulating the behavior, and are executed **BEFORE** action takes place.
- large pushes needs http server with chunked encoding support.
 
if you plan to use git you need to run RhodeCode with some
http server that supports chunked encoding which git http protocol uses, 
i recommend using waitress_ or gunicorn_ (linux only) for `paste` wsgi app 
replacement.

To use, simply change change the following in the .ini file::

    use = egg:Paste#http

to::
    
    use = egg:waitress#main

or::

    use = egg:gunicorn#main
    
    
And comment out bellow options::

    threadpool_workers = 
    threadpool_max_requests = 
    use_threadpool = 
    

You can simply run `paster serve` as usual.

  
You can always disable git/hg support by editing a 
file **rhodecode/__init__.py** and commenting out backends

.. code-block:: python
 
   BACKENDS = {
       'hg': 'Mercurial repository',
       #'git': 'Git repository',
   }

.. _waitress: http://pypi.python.org/pypi/waitress
.. _gunicorn: http://pypi.python.org/pypi/gunicorn
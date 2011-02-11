.. _statistics:


Statistics
==========

RhodeCode statistics system is heavy on resources, so in order to keep a 
balance between the usability and performance statistics are cached inside db
and are gathered incrementally, this is how RhodeCode does this:

With Celery disabled
++++++++++++++++++++

- on each first visit on summary page a set of 250 commits are parsed and
  updates statistics cache
- this happens on each single visit of statistics page until all commits are
  fetched. Statistics are kept cached until some more commits are added to
  repository, in such case RhodeCode will fetch only the ones added and will
  update it's cache.


With Celery enabled
+++++++++++++++++++

- on first visit on summary page RhodeCode will create task that will execute
  on celery workers, that will gather all stats until all commits are parsed,
  each task will parse 250 commits, and run next task to parse next 250 
  commits, until all are parsed.

.. note::
   In any time You can disable statistics on each repository in repository edit
   form in admin panel, just uncheck the statistics checkbox.
.. _statistics:


Statistics
==========

The RhodeCode statistics system makes heavy demands of the server resources, so
in order to keep a balance between usability and performance, the statistics are
cached inside db and are gathered incrementally, this is how RhodeCode does
this:

With Celery disabled
--------------------

- On each first visit to the summary page a set of 250 commits are parsed and
  updates statistics cache.
- This happens on each single visit to the statistics page until all commits are
  fetched. Statistics are kept cached until additional commits are added to the
  repository. In such a case RhodeCode will only fetch the new commits when
  updating it's cache.


With Celery enabled
-------------------

- On the first visit to the summary page RhodeCode will create tasks that will
  execute on celery workers. This task will gather all of the stats until all
  commits are parsed, each task will parse 250 commits, and run the next task to
  parse next 250 commits, until all of the commits are parsed.

.. note::
   At any time you can disable statistics on each repository via the repository
   edit form in the admin panel. To do this just uncheck the statistics checkbox.

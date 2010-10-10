.. _setup:

Setup
=====


- All needed configs are inside rhodecode sources ie. celeryconfig.py, 
  development.ini, production.ini You can configure the email, ports, loggers, 
  workers from there.
- For full text search You can either put crontab entry for 
  `python /var/www/rhodecode/rhodecode/lib/indexers/daemon.py incremental <path_to_repos>`
  or run indexer from admin panel. This will scann the repos given in the 
  application setup or given path for daemon.py and each scann in incremental 
  mode will scan only changed files.
  
TODO: write that !
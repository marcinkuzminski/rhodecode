.. _locking:

===================================
RhodeCode repository locking system
===================================


| Repos with **locking function=disabled** is the default, that's how repos work 
  today.
| Repos with **locking function=enabled** behaves like follows:

Repos have a state called `locked` that can be true or false.
The hg/git commands `hg/git clone`, `hg/git pull`, and `hg/git push` 
influence this state:

- The command `hg/git pull <repo>` will lock that repo (locked=true) 
  if the user has write/admin permissions on this repo

- The command `hg/git clone <repo>` will lock that repo (locked=true) if the 
  user has write/admin permissions on this repo


RhodeCode will remember the user id who locked the repo
only this specific user can unlock the repo (locked=false) by calling 

- `hg/git push <repo>` 

every other command on that repo from this user and 
every command from any other user will result in http return code 423 (locked)


additionally the http error includes the <user> that locked the repo 
(e.g. “repository <repo> locked by user <user>”)


So the scenario of use for repos with `locking function` enabled is that 
every initial clone and every pull gives users (with write permission)
the exclusive right to do a push.


Each repo can be manually unlocked by admin from the repo settings menu.
.. _installation_win:


Step by step Installation for Windows
=====================================


RhodeCode step-by-step install Guide for Windows  

Target OS: Windows XP SP3 English (Clean installation) 
+ All Windows Updates until 24-may-2012 

Step1 - Install Visual Studio 2008 Express
------------------------------------------

 
Optional: You can also install MingW, but VS2008 installation is easier 

Download "Visual C++ 2008 Express Edition with SP1" from: 
http://www.microsoft.com/visualstudio/en-us/products/2008-editions/express 
(if not found or relocated, google for "visual studio 2008 express" for 
updated link) 

You can also download full ISO file for offline installation, just 
choose "All - Offline Install ISO image file" in the previous page and 
choose "Visual C++ 2008 Express" when installing. 


.. note::

  Silverlight Runtime and SQL Server 2008 Express Edition are not 
  required, you can uncheck them 


Step2 - Install Python
----------------------

Install Python 2.x.y (x >= 5) x86 version (32bit). DO NOT USE A 3.x version.
Download Python 2.x.y from: 
http://www.python.org/download/ 

Choose "Windows Installer" (32bit version) not "Windows X86-64 
Installer". While writing this guide, the latest version was v2.7.3. 
Remember the specific major and minor version installed, because it will 
be needed in the next step. In this case, it is "2.7". 


Step3 - Install Win32py extensions
----------------------------------
 
Download pywin32 from: 
http://sourceforge.net/projects/pywin32/files/ 

- Click on "pywin32" folder 
- Click on the first folder (in this case, Build 217, maybe newer when you try) 
- Choose the file ending with ".win32-py2.x.exe" -> x being the minor 
  version of Python you installed (in this case, 7) 
  When writing this guide, the file was: 
  http://sourceforge.net/projects/pywin32/files/pywin32/Build%20217/pywin32-217.win32-py2.7.exe/download 


Step4 - Python BIN
------------------

Add Python BIN folder to the path 

You have to add the Python folder to the path, you can do it manually 
(editing "PATH" environment variable) or using Windows Support Tools 
that came preinstalled in Vista/7 and can be installed in Windows XP. 

- Using support tools on WINDOWS XP: 
  If you use Windows XP you can install them using Windows XP CD and 
  navigating to \SUPPORT\TOOLS. There, execute Setup.EXE (not MSI). 
  Afterwards, open a CMD and type::
 
    SETX PATH "%PATH%;[your-python-path]" -M 

  Close CMD (the path variable will be updated then) 

- Using support tools on WINDOWS Vista/7: 

  Open a CMD and type::

    SETX PATH "%PATH%;[your-python-path]" /M 

  Please substitute [your-python-path] with your Python installation path. 
  Typically: C:\\Python27 


Step5 - RhodeCode folder structure
----------------------------------

Create a RhodeCode folder structure 

This is only a example to install RhodeCode, you can of course change 
it. However, this guide will follow the proposed structure, so please 
later adapt the paths if you change them. My recommendation is to use 
folders with NO SPACES. But you can try if you are brave... 

Create the following folder structure::

  C:\RhodeCode 
  C:\RhodeCode\Bin 
  C:\RhodeCode\Env 
  C:\RhodeCode\Repos 


Step6 - Install virtualenv
---------------------------

Install Virtual Env for Python 

Navigate to: http://www.virtualenv.org/en/latest/index.html#installation 
Right click on "virtualenv.py" file and choose "Save link as...". 
Download to C:\\RhodeCode (or whatever you want) 
(the file is located at 
https://raw.github.com/pypa/virtualenv/master/virtualenv.py) 

Create a virtual Python environment in C:\\RhodeCode\\Env (or similar). To 
do so, open a CMD (Python Path should be included in Step3), navigate 
where you downloaded "virtualenv.py", and write:: 

 python virtualenv.py C:\RhodeCode\Env 

(--no-site-packages is now the default behaviour of virtualenv, no need 
to include it) 


Step7 - Install RhodeCode
-------------------------

Finally, install RhodeCode 

Close previously opened command prompt/s, and open a Visual Studio 2008 
Command Prompt (**IMPORTANT!!**). To do so, go to Start Menu, and then open 
"Microsoft Visual C++ 2008 Express Edition" -> "Visual Studio Tools" -> 
"Visual Studio 2008 Command Prompt" 

In that CMD (loaded with VS2008 PATHs) type::
 
  cd C:\RhodeCode\Env\Scripts (or similar) 
  activate 

The prompt will change into "(Env) C:\\RhodeCode\\Env\\Scripts" or similar 
(depending of your folder structure). Then type:: 

 pip install rhodecode 

(long step, please wait until fully complete) 

Some warnings will appear, don't worry as they are normal.


Step8 - Configuring RhodeCode
-----------------------------


steps taken from http://packages.python.org/RhodeCode/setup.html 

You have to use the same Visual Studio 2008 command prompt as Step7, so 
if you closed it reopen it following the same commands (including the 
"activate" one). When ready, just type::
 
  cd C:\RhodeCode\Bin 
  paster make-config RhodeCode production.ini 

Then, you must edit production.ini to fit your needs (ip address, ip 
port, mail settings, database, whatever). I recommend using NotePad++ 
(free) or similar text editor, as it handles well the EndOfLine 
character differences between Unix and Windows 
(http://notepad-plus-plus.org/) 

For the sake of simplicity lets run it with the default settings. After 
your edits (if any), in the previous Command Prompt, type:: 
 
 paster setup-rhodecode production.ini 

(this time a NEW database will be installed, you must follow a different 
step to later UPGRADE to a newer RhodeCode version) 

The script will ask you for confirmation about creating a NEW database, 
answer yes (y) 
The script will ask you for repository path, answer C:\\RhodeCode\\Repos 
(or similar) 
The script will ask you for admin username and password, answer "admin" 
+ "123456" (or whatever you want) 
The script will ask you for admin mail, answer "admin@xxxx.com" (or 
whatever you want) 

If you make some mistake and the script does not end, don't worry, start 
it again. 


Step9 - Running RhodeCode
-------------------------


In the previous command prompt, being in the C:\\RhodeCode\\Bin folder, 
just type::
 
 paster serve production.ini 

Open yout web server, and go to http://127.0.0.1:5000 

It works!! :-) 

Remark: 
If it does not work first time, just Ctrl-C the CMD process and start it 
again. Don't forget the "http://" in Internet Explorer 



What this Guide does not cover:

- Installing Celery 
- Running RhodeCode as Windows Service. You can investigate here:
 
  - http://pypi.python.org/pypi/wsgisvc 
  - http://ryrobes.com/python/running-python-scripts-as-a-windows-service/     
  - http://wiki.pylonshq.com/display/pylonscookbook/How+to+run+Pylons+as+a+Windows+service 

- Using Apache. You can investigate here:

  - https://groups.google.com/group/rhodecode/msg/c433074e813ffdc4 


Upgrading
=========
 
Stop running RhodeCode 
Open a CommandPrompt like in Step7 (VS2008 path + activate) and type::
 
 easy_install -U rhodecode 
 cd \RhodeCode\Bin 

{ backup your production.ini file now} :: 

 paster make-config RhodeCode production.ini 

(check changes and update your production.ini accordingly) ::
 
 paster upgrade-db production.ini (update database)

Full steps in http://packages.python.org/RhodeCode/upgrade.html 
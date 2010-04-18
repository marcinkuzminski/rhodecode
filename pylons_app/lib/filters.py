from mercurial import util
from mercurial.templatefilters import age as _age, person as _person

age = lambda  x:_age(x)
capitalize = lambda x: x.capitalize()
date = lambda x: util.datestr(x)
email = util.email
person = lambda x: _person(x)
hgdate = lambda  x: "%d %d" % x
isodate = lambda  x: util.datestr(x, '%Y-%m-%d %H:%M %1%2')
isodatesec = lambda  x: util.datestr(x, '%Y-%m-%d %H:%M:%S %1%2')
localdate = lambda  x: (x[0], util.makedate()[1])
rfc822date = lambda  x: util.datestr(x, "%a, %d %b %Y %H:%M:%S %1%2")
rfc3339date = lambda  x: util.datestr(x, "%Y-%m-%dT%H:%M:%S%1:%2")
time_ago = lambda x: util.datestr(_age(x), "%a, %d %b %Y %H:%M:%S %1%2")

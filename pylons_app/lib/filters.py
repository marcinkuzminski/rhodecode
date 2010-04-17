from mercurial import util
from mercurial.templatefilters import age as _age

age = lambda context, x:_age(x)
capitalize = lambda x: x.capitalize()
date = lambda x: util.datestr(x)
email = util.email
hgdate = lambda context, x: "%d %d" % x
isodate = lambda context, x: util.datestr(x, '%Y-%m-%d %H:%M %1%2')
isodatesec = lambda context, x: util.datestr(x, '%Y-%m-%d %H:%M:%S %1%2')
localdate = lambda context, x: (x[0], util.makedate()[1])
rfc822date = lambda context, x: util.datestr(x, "%a, %d %b %Y %H:%M:%S %1%2")
rfc3339date = lambda context, x: util.datestr(x, "%Y-%m-%dT%H:%M:%S%1:%2")
time_ago = lambda context, x: util.datestr(_age(x), "%a, %d %b %Y %H:%M:%S %1%2")

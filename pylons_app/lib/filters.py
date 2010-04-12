from mercurial import util

capitalize = lambda x: x.capitalize()
date = lambda x: util.datestr(x)
email = util.email
hgdate = lambda x: "%d %d" % x
isodate = lambda x: util.datestr(x, '%Y-%m-%d %H:%M %1%2')
isodatesec = lambda x: util.datestr(x, '%Y-%m-%d %H:%M:%S %1%2')
localdate = lambda x: (x[0], util.makedate()[1])
rfc822date = lambda context, x: util.datestr(x, "%a, %d %b %Y %H:%M:%S %1%2")
rfc3339date = lambda x: util.datestr(x, "%Y-%m-%dT%H:%M:%S%1:%2")

import datetime
import functools
import decimal
import imp

__all__ = ['json', 'simplejson', 'stdlibjson']


def _is_aware(value):
    """
    Determines if a given datetime.time is aware.

    The logic is described in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo
    """
    return (value.tzinfo is not None
            and value.tzinfo.utcoffset(value) is not None)


def _obj_dump(obj):
    """
    Custom function for dumping objects to JSON, if obj has __json__ attribute
    or method defined it will be used for serialization

    :param obj:
    """

    if isinstance(obj, complex):
        return [obj.real, obj.imag]
    # See "Date Time String Format" in the ECMA-262 specification.
    # some code borrowed from django 1.4
    elif isinstance(obj, datetime.datetime):
        r = obj.isoformat()
        if obj.microsecond:
            r = r[:23] + r[26:]
        if r.endswith('+00:00'):
            r = r[:-6] + 'Z'
        return r
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return str(obj)
    elif isinstance(obj, datetime.time):
        if _is_aware(obj):
            raise ValueError("JSON can't represent timezone-aware times.")
        r = obj.isoformat()
        if obj.microsecond:
            r = r[:12]
        return r
    elif isinstance(obj, set):
        return list(obj)
    elif hasattr(obj, '__json__'):
        if callable(obj.__json__):
            return obj.__json__()
        else:
            return obj.__json__
    else:
        raise NotImplementedError


# Import simplejson
try:
    # import simplejson initially
    _sj = imp.load_module('_sj', *imp.find_module('simplejson'))

    def extended_encode(obj):
        try:
            return _obj_dump(obj)
        except NotImplementedError:
            pass
        raise TypeError("%r is not JSON serializable" % (obj,))
    # we handle decimals our own it makes unified behavior of json vs
    # simplejson
    sj_version = [int(x) for x in _sj.__version__.split('.')]
    major, minor = sj_version[0], sj_version[1]
    if major < 2 or (major == 2 and minor < 1):
        # simplejson < 2.1 doesnt support use_decimal
        _sj.dumps = functools.partial(_sj.dumps,
                                             default=extended_encode)
        _sj.dump = functools.partial(_sj.dump,
                                            default=extended_encode)
    else:
        _sj.dumps = functools.partial(_sj.dumps,
                                             default=extended_encode,
                                             use_decimal=False)
        _sj.dump = functools.partial(_sj.dump,
                                            default=extended_encode,
                                            use_decimal=False)
    simplejson = _sj

except ImportError:
    # no simplejson set it to None
    simplejson = None


try:
    # simplejson not found try out regular json module
    _json = imp.load_module('_json', *imp.find_module('json'))

    # extended JSON encoder for json
    class ExtendedEncoder(_json.JSONEncoder):
        def default(self, obj):
            try:
                return _obj_dump(obj)
            except NotImplementedError:
                pass
            raise TypeError("%r is not JSON serializable" % (obj,))
    # monkey-patch JSON encoder to use extended version
    _json.dumps = functools.partial(_json.dumps, cls=ExtendedEncoder)
    _json.dump = functools.partial(_json.dump, cls=ExtendedEncoder)

    stdlibjson = _json
except ImportError:
    stdlibjson = None

# set all available json modules
if simplejson:
    json = _sj
elif stdlibjson:
    json = _json
else:
    raise ImportError('Could not find any json modules')
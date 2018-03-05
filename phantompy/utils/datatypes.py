from datetime import datetime
from calendar import timegm
from json import dumps, loads
try:
    from bson.objectid import ObjectId
except ImportError:
    class ObjectId: pass


class DataObject(dict):

    def __init__(self, *args, **kwargs):
	super(DataObject, self).__init__(*args, **kwargs)
        for k, v in self.iteritems():
            self.__setitem__(k, v)

    def __setitem__(self, k, v):
        super(DataObject, self).__setitem__(k, self.__patch__(v))

    __setattr__ = __setitem__
    __getattr__ = dict.__getitem__
    __delattr__ = dict.__delitem__

    def __patch__(self, obj):
        if not isinstance(obj, DataObject):
            if isinstance(obj, dict):
                obj = DataObject(obj)
            elif (
                    not isinstance(obj, basestring) and
                    hasattr(obj, '__iter__')
                ):
                obj = obj.__class__(self.__patch__(i) for i in obj)
        return obj

    def get_nested_item(self, *keys, **kwargs):
	try:
	    return reduce(dict.__getitem__, keys, self)
	except (KeyError, TypeError):
	    for kw in ('default', 'd'):
		if kw in kwargs:
		    return kwargs[kw]
	    else:
		raise KeyError(str(keys))

    def copy(self):
        return self.__class__(self)

    def setdefault(self, k, d=None):
	if k not in self:
	    self[k] = d
	return self[k]

    def update(self, data=None, **kwargs):
        upd = {}
        if data is not None:
            upd.update(data)
        upd.update(kwargs)
        for k, v in upd.iteritems():
            self[k] = v

    @classmethod
    def from_json(cls, json):
	data = loads(json)
	if not isinstance(data, dict):
	    raise TypeError(
		'JSON object must be deserializable into Python dict'
	    )
	return cls(loads(json))

    def to_json(self):
        return dumps(self, default=self._serialize_json)

    @staticmethod
    def _serialize_json(obj):
        # ObjectID
        if isinstance(obj, ObjectId):
            return str(obj)
        # Datetime
        elif isinstance(obj, datetime):
            if obj.utcoffset() is not None:
                obj = obj - obj.utcoffset()
            millisec = int(
                timegm(obj.timetuple()) * 1000 +
                obj.microsecond / 1000
            )
            return millisec
	# Unknown type
	else:
	    raise TypeError('%r is not JSON serializable' % obj)



import os
from datetime import datetime
from dateutil.tz import gettz
from geoip2.database import Reader
from ..misc import silent
from ..regex import RE


__all__ = ['GeoIPError', 'GeoIP']


package_dir = os.path.abspath(os.path.dirname(__file__))
geodb_reader = Reader(os.path.join(package_dir, 'data/geoip.mmdb'))


class GeoIPError(Exception):
    """geoip::GeoIPError"""


class GeoIP(object):
    """geoip::GeoIP"""

    @staticmethod
    def validate_ip(ip):
        if not isinstance(ip, basestring):
            raise TypeError('IP address must be string')
        if RE.IPv4.match(ip):
            return True
        else:
            raise ValueError('Invalid IPv4 address: %s' % ip)

    def api_call(func):
        @silent(GeoIPError, default=True)
        def wrapper(self, *args, **kwargs):
            self.validate_ip(args[0])
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                raise GeoIPError(e)
        return wrapper

    @api_call
    def get_timezone_offset_by_ip(self, ip):
        iana_tz = geodb_reader.city(ip).location.time_zone
        tz_file = gettz(iana_tz)
        tz_offset = datetime.now(tz_file).strftime('%z')
        hours = tz_offset[1:3]
        minutes = tz_offset[3:]
        return int(tz_offset[0] + '1') * (int(hours) * 60 + int(minutes))

    @api_call
    def get_country_by_ip(self, ip):
        country = geodb_reader.city(ip).country
        return {
            'code': country.iso_code,
            'name': country.name,
        }

    @api_call
    def get_city_by_ip(self, ip):
        city = geodb_reader.city(ip).city
        return city.name

    @api_call
    def get_postal_code__by_ip(self, ip):
        postal = geodb_reader.city(ip).postal
        return postal.code


GeoIP = GeoIP()



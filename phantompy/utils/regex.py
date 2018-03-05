import re
from .datatypes import DataObject


__all__ = ['RE']


# IPv4
IPv4 = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
# Port
PORT = re.compile(r'^\d{2,5}$')
# Socks4/5 port
PORT_SOCKS = re.compile(r'^108\d{1,2}$')
# IPv4 + port
IPv4_PORT = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}$')

# Proxy URL
PROXY_URL = re.compile(
    r'^(?:(?P<type>(http|http_tunnel|socks4|socks5))://)?'
    r'(?:(?P<user>\w+):(?P<passwd>\w+)@)?'
    r'(?P<host>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(?P<port>\d{2,5})/?$',
    re.I
)
# Proxy type
PROXY_TYPE = re.compile(r'^(http|http_tunnel|socks4|socks5)$', re.I)

# HTTP status code
HTTP_STATUS_CODE = re.compile(r'^HTTP/1.[01] (\d{3})')



_re_type = type(re.compile(''))

RE = DataObject(
    filter(
        lambda _: (
            isinstance(_[1], _re_type) or
            (isinstance(_[1], basestring) and not _[0].startswith('_'))
        ),
        globals().items()
    )
)



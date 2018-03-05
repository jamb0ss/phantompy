import os
import re
import urlparse
from urllib import urlencode
from tldextract import extract as extract_tld
from tldextract.tldextract import TLD_EXTRACTOR
from .regex import RE


__all__ = ['URL', 'URLError', 'TLDS']


# Top-level domains
TLDS = set([tld.encode('idna') for tld in TLD_EXTRACTOR.tlds])

SCHEMES = set(['http', 'https'])
#SCHEMES = set(filter(None, urlparse.uses_netloc))

RE_URL_SCHEME = re.compile(r'^(https?:)?//', re.I)

URL_COMPONENTS = set(['scheme', 'netloc', 'username', 'password', 'subdomain',
                      'domain', 'tld', 'port', 'path', 'query', 'query_dict',
                      'fragment'])

URL_LOWER_CASE_COMPONENTS = set(['scheme', 'netloc', 'subdomain', 'domain', 'tld'])

URL_NETLOC_COMPONENTS = set(['username', 'password', 'subdomain', 'domain', 'tld',
                             'port'])


class URLError(Exception):
    """url::URLError"""


class URL(object):
    """url::URL"""

    def __init__(self, url, strict_validation=False, **kwargs):
        self.strict_validation = strict_validation
        self.full = url
        for k, v in kwargs.items():
            if k not in URL_COMPONENTS:
                raise URLError('Unsupported URL component: %s' % k)
            self.__setattr__(k, v)

    def clone(self):
        return self.__class__(self.full, strict_validation=self.strict_validation)

    def validate(self, strict=None):
        strict = self.strict_validation if strict is None else strict

        try:
            # scheme
            if not self.scheme:
                raise URLError('No scheme')
            elif not self.scheme in SCHEMES:
                raise URLError('Unsupported scheme: %s' % self.scheme)
            # domain
            if not self.domain:
                raise URLError('No domain')
            # tld
            if not self.tld:
                if not (
                    self.domain == 'localhost' or
                    RE.IPv4.match(self.domain)
                ):
                    raise URLError('No TLD')
            elif self.tld not in TLDS:
                raise URLError('Unsupported TLD: %s' % self.tld)

            self.is_valid = True
            self._validation_error = None
            return True

        except URLError as e:
            if strict:
                raise URLError('Validation error :: %s' % str(e))
            else:
                self.is_valid = False
                self._validation_error = str(e)
                return False

    def join(self, url):
        if not isinstance(url, basestring):
            raise TypeError(':url must be string')
        self.full = urlparse.urljoin(self.full, url)
        return self

    def update_query(self, query_dict=None, **kwargs):
        upd = dict(self.query_dict)
        if query_dict is not None:
            if not isinstance(query_dict, dict):
                raise TypeError(':query_dict must be dict')
            upd.update(query_dict)
        upd.update(kwargs)
        self.query_dict = upd
        return self

    @staticmethod
    def urlencode(url=None, query_dict=None, **kwargs):
        url = URL(url, strict_validation=False)
        url.update_query(query_dict, **kwargs)
        return url.full

    @staticmethod
    def parse_netloc(netloc):
        if not isinstance(netloc, basestring):
            raise TypeError(':netloc must be string')

        username, password, port = None, None, None
        if '@' in netloc:
            auth, netloc = netloc.split('@', 1)
            auth = auth.split(':')
            if len(auth) == 2 and all(auth):
                username, password = auth
        if ':' in netloc:
            netloc, port = netloc.rsplit(':', 1)
            if port.isdigit():
                port = int(port)

        r = extract_tld(netloc.lower())

        return {
            'username': username,
            'password': password,
            'subdomain': r.subdomain,
            'domain': r.domain,
            'tld': r.suffix,
            'port': port,
        }

    def __setattr__(self, name, value):
        if name == 'full':
            self.__seturl__('' if value is None else value)

        elif name in URL_COMPONENTS:

            if name == 'query_dict':
                if value is None:
                    value = {}
                elif not isinstance(value, dict):
                    raise TypeError(':query_dict must be dict')
                else:
                    for k, v in value.items():
                        if v is None:
                            value.pop(k)
                        elif isinstance(v, (list, tuple, set)):
                            value[k] = filter(lambda _: _ is not None, v)

            else:
                if value is None:
                    value = ''
                elif name == 'port':
                    if not isinstance(value, int):
                        raise TypeError(':port must be int')
                elif not isinstance(value, basestring):
                    raise TypeError(':%s must be string' % name)

            if name in URL_LOWER_CASE_COMPONENTS:
                value = value.lower()
            self.__safesetattr__(name, value)

            if name == 'netloc':
                for component, val in self.parse_netloc(value).items():
                    self.__safesetattr__(component, val)

            elif name in URL_NETLOC_COMPONENTS:
                self.__safesetattr__(
                    'netloc',
                    '.'.join(
                        filter(None, [self.subdomain, self.domain, self.tld])
                    )
                )

            elif name == 'query':
                self.__safesetattr__(
                    'query_dict',
                    urlparse.parse_qs(value, keep_blank_values=True)
                )

            elif name == 'query_dict':
                self.__safesetattr__('query', urlencode(value, doseq=True))

            self.__safesetattr__(
                'full',
                urlparse.urlunsplit((
                    self.scheme, self.netloc, self.path,
                    self.query, self.fragment,
                ))
            )

            self.validate()

        else:
            self.__safesetattr__(name, value)

    def __seturl__(self, url):
        if not isinstance(url, basestring):
            raise TypeError(':url must be string')
        elif not RE_URL_SCHEME.match(url):
            url = '//' + url

        url_parsed = urlparse.urlsplit(url, scheme='http')

        self.__safesetattr__('scheme', url_parsed.scheme.lower())
        self.__safesetattr__('netloc', url_parsed.netloc.lower())

        for component, val in self.parse_netloc(self.netloc).items():
            self.__safesetattr__(component, val)

        self.__safesetattr__('path', url_parsed.path)
        self.__safesetattr__('query', url_parsed.query)
        self.__safesetattr__(
            'query_dict',
            urlparse.parse_qs(self.query, keep_blank_values=True)
        )
        self.fragment = url_parsed.fragment # trigger .full calculation

        self.username = url_parsed.username
        self.password = url_parsed.password
        self.port = url_parsed.port

    def __safesetattr__(self, name, value):
        super(URL, self).__setattr__(name, value)

    def __repr__(self):
        return self.full




# -*- coding: utf-8 -*-

import os
import re
from tempfile import gettempdir
from contextlib import contextmanager
from functools import wraps
from json import dumps, loads
from random import choice, randint
from time import time, sleep
from uuid import uuid4
from shutil import rmtree
from distutils.spawn import find_executable
from urlparse import urljoin

try:
    from selenium.webdriver import PhantomJS
    from selenium.webdriver import DesiredCapabilities
    # from selenium.webdriver.support.ui import WebDriverWait
    # from selenium.webdriver.common.by import By
    # from selenium.webdriver.common.keys import Keys
    # from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.common.exceptions import (
        NoSuchElementException, TimeoutException, NoSuchWindowException,
        StaleElementReferenceException, NoAlertPresentException,
    )
except ImportError as e:
    raise ImportError(
        'Selenium WebDriver is required '
        '(https://pypi.python.org/pypi/selenium) :: %s'
        % str(e)
    )

from .utils import weighted_choice, custom_value
from .utils.user_agent import generate_navigator
from .utils.url import URL, URLError
from .utils.geoip import GeoIP
from .utils import regex


__all__ = ['Phantom', 'PhantomError']


PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))
JS_DIR = os.path.join(PACKAGE_DIR, 'js')
BIN_DIR = os.path.join(PACKAGE_DIR, 'bin')
SESSIONS_DIR = os.path.join(gettempdir(), 'phantompy')

DRIVER_BINARY = os.path.join(BIN_DIR, 'phantomjs')
if not os.path.isfile(DRIVER_BINARY):
    DRIVER_BINARY = find_executable('phantomjs')


# JavaScripts
JS = {
    'base': 'base.js',
    'date': 'date.js',
}

for script, filename in JS.items():
    filepath = os.path.join(JS_DIR, filename)
    if not os.path.isfile(filepath):
        raise Exception('Missing "%s" JS script' % filename)
    JS[script] = open(filepath).read()


# Screen resolution (width, height) / popularity (%)
# http://www.w3schools.com/browsers/browsers_display.asp
SCREEN_RESOLUTION = [
    ((1024, 768), 4),
    ((1280, 800), 5),
    ((1280, 1024), 7),
    ((1360, 768), 2),
    ((1366, 768), 33),
    ((1440, 900), 7),
    ((1600, 900), 6),
    ((1680, 1050), 4),
    ((1920, 1080), 16),
    ((1920, 1200), 3),
]

SCREEN_COLOR_DEPTH = 24

OS_TASKBAR_HEIGHT = (30, 32, 40)

BROWSER_TASKBAR_HEIGHT = (90, 100, 105)

BROWSER_SCROOLBAR_WIDTH = (17, 20)


# TODO: replace with case insensitive dictionary
DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate',
}

# TODO: https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation
# ACCEPT_HEADER


# the default Phantom configuration
DEFAULT_CONFIG = {

    # default HTTP headers for all requests
    'default_headers': None,

    # the size of the headless screen
    'screen_size': None,

    # page load timeout
    # * also applied by default to navigation clicks and meta refresh
    'page_load_timeout': 60,
    'page_load_attempts': 1,

    # XPATH selector timeout (implicitly_wait)
    'xpath_timeout': 0,

    # the max timeout applied to all requests after which
    # any resource requested will stop trying and proceed with other parts of the page
    'resource_timeout': 60, # in seconds

    # features
    'cookies_enabled': True,
    'javascript_enabled': True,
    'load_images': True,
    'load_stylesheets': True,
    'spoof_java_plugin': False,
    'spoof_flash_plugin': False,
    'spoof_html5_media':False,

    # UTC/GMT timezone offset (in minutes)
    # auto: the offset will be set according to the proxy's location or not set at all
    # 'timezone_offset': 'auto',

}


# the default driver's (PhantomJS) configuration
# TODO: why this shit makes driver to stuck? wtf
DEFAULT_DRIVER_PROFILE = {
    #'cookies_enabled': True, # controls whether the CookieJar is enabled or not
    #'cookies_file': None, # path to persistent cookies file
    #'disk_cache': False, # enables disk cache
    'ignore_ssl_errors': True, # ignores SSL errors
    #'local_storage_path': None, # path to save LocalStorage & WebSQL content
    #'local_storage_quota': None, # maximum size to allow for data
    'local_to_remote_url_access': True, # allows local content to access remote URL
    #'max_disk_cache_size': None, # limits the size of disk cache (in KB)
    #'output_encoding': 'utf8', # sets the encoding used for terminal output
    #'script_encoding': 'utf8', # sets the encoding used for the starting script
    'ssl_protocol': 'any', # sets the SSL protocol for secure connections
    #'ssl_certificates_path': None, # Sets the location for custom CA certificates
    'web_security': False, # enables web security and forbids cross-domain XHR
}


# TODO: different browsers?
# TODO: version?
FLASH_PLUGIN = {
    'win': {
        'version': 'WIN 20,0,0,185',
        'description': 'Shockwave Flash 20.0 r0',
        'filename': 'NPSWF32.dll',
    },
    'linux': {
        'version': 'LNX 20,0,0,185',
        'description': 'Shockwave Flash 20.0 r0',
        'filename': 'libpepflashplayer.so',
    },
    'mac': {
        'version': 'MAC 20,0,0,185',
        'description': 'Shockwave Flash 20.0 r0',
        'filename': 'Shockwave Flash.Plugin',
    },
}


BLANK_URL = 'about:blank'


RE = {
    'meta_refresh': re.compile(r'(?P<timeout>\d+);?\s*(url=(?P<url>.+))?'),
}

XPATH = {
    'meta_refresh': '//meta[@http-equiv="refresh" and @content]',
}



class PhantomError(Exception):
    """phantompy::PhantomError"""


# TODO: wrap all parent's methods to throw PhantomError
# TODO: start with existing session, save/load cookies file
class Phantom(PhantomJS):
    """phantompy::Phantom"""

    def __init__(self, binary=DRIVER_BINARY, driver_profile=DEFAULT_DRIVER_PROFILE,
                 config=DEFAULT_CONFIG, navigator=None, proxy=None,
                 sessions_dir=SESSIONS_DIR, screenshots_dir=None):

        if not binary:
            raise ValueError('PhantomJS :binary path must be set')
        elif not isinstance(binary, basestring):
            raise TypeError('PhantomJS :binary path must be non-empty string')
        elif driver_profile and not isinstance(driver_profile, dict):
            raise TypeError(':driver_profile must be dict')
        elif sessions_dir and not isinstance(sessions_dir, basestring):
            raise TypeError(':sessions_dir must be string')
        elif screenshots_dir and not isinstance(screenshots_dir, basestring):
            raise TypeError(':screenshots_dir must be string')

        # session uid (differs from .session_id)
        self._id = str(uuid4())

        self._started = False

        self.binary = os.path.realpath(binary)
        if not os.path.isfile(self.binary):
            raise PhantomError(
                'PhantomJS :binary cannot be found by path: %s' % self.binary
            )

        self.session_dir = os.path.join(sessions_dir or SESSIONS_DIR, self._id)
        # wtf?
        if os.path.isdir(self.session_dir):
            raise PhantomError(
                "The unique session's dir is already exists: %s" % self.session_dir
            )
        else:
            os.makedirs(self.session_dir)

        self.screenshots_dir = screenshots_dir

        self.driver_profile = dict(DEFAULT_DRIVER_PROFILE)
        if driver_profile:
            for k, v in driver_profile.items():
                if k in self.driver_profile:
                    self.driver_profile[k] = v

        self.driver_profile['local_storage_path'] = os.path.join(
            self.session_dir, 'local_storage'
        )
        os.makedirs(self.driver_profile['local_storage_path'])

        # TODO: it'll be always empty, see: https://github.com/SeleniumHQ/selenium/issues/1911
        self.driver_profile['cookies_file'] = os.path.join(self.session_dir, 'cookies.txt')

        self.driver_log_path = os.path.join(self.session_dir, 'driver.log')

        try:
            self._start_driver()
        except Exception as e:
            try:
                rmtree(self.session_dir, ignore_errors=True)
            except OSError:
                pass
            raise PhantomError('Unable to start the driver :: %s' % str(e))

        self.new_session(config, navigator=navigator, proxy=proxy)

        self._started = True


    def _start_driver(self):
        if self._started:
            raise PhantomError('The driver is already started')

        service_args = []
        for k, v in self.driver_profile.items():
            if v is None:
                continue
            service_args.append(self.get_service_arg(k, v))

        desired_capabilities = dict(DesiredCapabilities.PHANTOMJS)

        super(Phantom, self).__init__(
            executable_path=self.binary,
            # port=0,
            desired_capabilities=desired_capabilities,
            service_args=service_args,
            service_log_path=self.driver_log_path,
        )

        sleep(1) # wait a sec, damn

        self.command_executor._commands['executePhantomScript'] = (
            'POST',
            '/session/$sessionId/phantom/execute'
        )

        self.pid = self.service.process.pid
        with open(os.path.join(self.session_dir, 'driver.pid'), 'w') as f:
            f.write(str(self.pid))


    _quit = PhantomJS.quit

    def quit(self):
        try:
            self._quit()
            # self.clear_session()
            self._started = False
        except Exception as e:
            raise PhantomError('Unable to stop the driver :: %s' % str(e))
        finally:
            try:
                rmtree(self.session_dir, ignore_errors=True)
            except OSError:
                pass


    @staticmethod
    def get_service_arg(key, value):
        if not isinstance(key, basestring):
            raise TypeError('Service arg name must be string')
        if not isinstance(value, basestring):
            try:
                value = dumps(value)
            except Exception as e:
                raise PhantomError(
                    'Unsupported service arg "%s" value: %s'
                    % (key, str(value))
                )
        return '--%s=%s' % (key.replace('_', '-'), value.strip())

    # ************************************************************************
    # :: sessions ::
    # ************************************************************************

    # TODO: save/load session

    config = None

    def new_session(self, config=None, navigator=None, proxy=None):
        if self._started:
            self._cleanup_session()
            self.start_session(self.desired_capabilities)

        self.config = dict(DEFAULT_CONFIG)
        if config:
            if not isinstance(config, dict):
                raise TypeError(':config must be dict')
            for k, v in config.items():
                if k in self.config:
                    self.config[k] = v

        self._navigator = self.get_navigator(navigator)

        self.default_headers = None

        if proxy:
            proxy = self.get_proxy(proxy)
            self.timezone_offset = GeoIP.get_timezone_offset_by_ip(
                proxy['host'], silent=True
            )
        else:
            self.timezone_offset = None

        self._screen = self.get_screen(
            self.config['screen_size'] or weighted_choice(SCREEN_RESOLUTION)
        )
        self.execute_phantomjs_script(
            'page.viewportSize = %s' %
            dumps({
                'width': self._screen['window']['innerWidth'],
                'height': self._screen['window']['innerHeight'],
            })
        )

        if self.config['spoof_flash_plugin']:
            if self._navigator['__platform__'] not in FLASH_PLUGIN:
                raise ValueError('Unsupported :navigator for Flash plugin')
            flash_plugin = FLASH_PLUGIN[self._navigator['__platform__']]
        else:
            flash_plugin = None

        session_config = {
            '__config__': dumps({
                'javascript_enabled': self.config['javascript_enabled'],
                'load_images': self.config['load_images'],
                'resource_timeout': self.config['resource_timeout'] * 1000,
                'navigator': dict(
                    filter(
                        lambda _: not _[0].startswith('_'),
                        self._navigator.items()
                    )
                ),
                'screen': self._screen,
                'spoof_flash_plugin': self.config['spoof_flash_plugin'],
                'flash_plugin': flash_plugin,
                'spoof_java_plugin': self.config['spoof_java_plugin'],
                'spoof_html5_media': self.config['spoof_html5_media'],
                'timezone_offset': self.timezone_offset,
            }),
            '__getMockDate__': JS['date'],
        }

        self.execute_phantomjs_script(JS['base'] % session_config)

        if proxy:
            self._set_proxy(proxy, set_timezone=False)
        elif self._started:
            self._reset_proxy(reset_timezone=False)

        self.cookies_enabled = self.config['cookies_enabled']
        self.load_stylesheets = self.config['load_stylesheets']

        self.page_load_timeout = self.config['page_load_timeout']
        self.page_load_attempts = self.config['page_load_attempts']
        self.xpath_timeout = self.config['xpath_timeout']

        self.history = []


    def _cleanup_session(self):
        self.clear_http_cache()
        #self.clear_local_storage()

        # TODO: what?
        try:
            self.execute_phantomjs_script('page.close()')
        except Exception as e:
            raise PhantomError('Unable to close the web page :: %s' % str(e))

        # open(self.driver_profile['cookies_file'], 'w') # ???
        open(self.driver_log_path, 'w')

        rmtree(self.driver_profile['local_storage_path'], ignore_errors=True)
        os.makedirs(self.driver_profile['local_storage_path'])

    # def save_session(self, path):
    #     pass

    # def load_session(self, path):
    #     pass

    def clear_http_cache(self):
        try:
            self.execute_phantomjs_script('page.clearMemoryCache()')
        except Exception as e:
            raise PhantomError('Unable to clear the HTTP cache :: %s' % str(e))

    # TODO: why this shit doesn't work wtf
    # def clear_local_storage(self):
    #     try:
    #         self.execute_phantomjs_script(
    #             'page.evaluate(function() { localStorage.clear() })'
    #         )
    #     except Exception as e:
    #         raise PhantomError('Unable to clear the localStorage :: %s' % str(e))

    # ************************************************************************
    # :: HTTP headers ::
    # ************************************************************************

    # TODO: case insensitive!

    _default_headers = dict(DEFAULT_HEADERS)

    @property
    def default_headers(self):
        return dict(self._default_headers)

    @default_headers.setter
    def default_headers(self, headers):
        if headers is None:
            headers = {}
        elif not isinstance(headers, dict):
            raise TypeError(':headers must be dict')
        upd = dict(
            map(
                lambda _: (_[0], None),
                self._default_headers.items()
            )
        )
        upd.update(DEFAULT_HEADERS)
        upd.update(self.config.get('default_headers') or {})
        upd['User-Agent'] = self.user_agent
        upd.update(headers)
        self.update_default_headers(upd)


    def set_default_header(self, name, value):
        if not isinstance(name, basestring):
            raise TypeError("HTTP header's :name must be string")
        self.update_default_headers({name: value})


    def update_default_headers(self, headers):
        if not headers:
            return
        elif not isinstance(headers, dict):
            raise TypeError(':headers must be dict')
        elif not all([isinstance(_, basestring) for _ in headers.keys()]):
            raise ValueError('Unsupported :headers')

        upd = dict(self._default_headers)
        for k, v in headers.items():
            if v in (False, None):
                upd.pop(k, None)
            else:
                upd[k] = v

        try:
            self.execute_phantomjs_script('page.customHeaders = %s' % dumps(upd))
            self._default_headers = upd
        except Exception as e:
            raise PhantomError('Unable to update HTTP headers :: %s' % str(e))

    # ************************************************************************
    # :: navigator ::
    # ************************************************************************

    # TODO: set user-agent
    # TODO: os, browser etc.
    # TODO: cookieEnabled?

    _navigator = None

    @property
    def navigator(self):
        return self._navigator

    @navigator.setter
    def navigator(self, config):
        navigator = self.get_navigator(config)

        try:
            self.execute_phantomjs_script(
                'page.setNavigator(%s)' %
                dumps(
                    dict(
                        filter(
                            lambda _: not _[0].startswith('_'),
                            navigator.items()
                        )
                    )
                )
            )
        except Exception as e:
            raise PhantomError('Unable to set the navigator :: %s' % str(e))

        self._navigator = navigator
        self.set_default_header('User-Agent', self._navigator['userAgent'])


    def get_navigator(self, config=None):
        if config is None:
            config = self.generate_navigator()

        elif isinstance(config, dict):
            for key in ('platform', 'userAgent', '__name__', '__platform__'):
                if not config.get(key):
                    raise ValueError(
                        "No '%s' value in the :navigator's config" % key
                    )

        else:
            raise TypeError(":navigator's config must be dict")

        return dict(config)


    def generate_navigator(self, platform=None, navigator=None):
        return generate_navigator(platform=platform, navigator=navigator)


    # TODO: setter
    @property
    def user_agent(self):
        return self.navigator['userAgent'] if self.navigator else None

    # ************************************************************************
    # :: proxy ::
    # ************************************************************************

    # TODO: property
    timezone_offset = None

    _proxy = None

    @property
    def proxy(self):
        return self._proxy

    @proxy.setter
    def proxy(self, config):
        if config:
            self._set_proxy(config)
        else:
            self._reset_proxy()


    def _set_proxy(self, config, set_timezone=True):
        proxy = self.get_proxy(config)

        try:
            self.execute_phantomjs_script('page._setProxy(%s)' % dumps(proxy))
            self._proxy = proxy
        except Exception as e:
            raise PhantomError('Unable to set the proxy :: %s' % str(e))

        # only works for IPv4 hosts
        if set_timezone and proxy['host'] != 'localhost':
            timezone_offset = GeoIP.get_timezone_offset_by_ip(proxy['host'], silent=True)
            if timezone_offset is not None:
                try:
                    self.execute_phantomjs_script('page.setTimezone(%s)' % timezone_offset)
                    self.timezone_offset = timezone_offset
                except Exception as e:
                    raise PhantomError('Unable to set the timezone :: %s' % str(e))


    def _reset_proxy(self, reset_timezone=True):
        try:
            self.execute_phantomjs_script('page._resetProxy()')
            self._proxy = None
        except Exception as e:
            raise PhantomError('Unable to reset the proxy :: %s' % str(e))
        if reset_timezone:
            try:
                self.execute_phantomjs_script('page.resetTimezone()')
                self.timezone_offset = None
            except Exception as e:
                raise PhantomError('Unable to reset the timezone :: %s' % str(e))


    def get_proxy(self, config=None):
        if config is None:
            return

        elif isinstance(config, basestring):
            proxy_url = regex.RE.PROXY_URL.match(config)
            if not proxy_url:
                raise ValueError('Unsupported proxy URL: %s' % config)
            proxy = proxy_url.groupdict()
            proxy['type'] = proxy['type'] or 'http'

        elif isinstance(config, dict):
            proxy = {}

            proxy['type'] = config.get('type') or config.get('proxy_type')

            if not proxy['type']:
                proxy['type'] = 'http'
            elif not isinstance(proxy['type'], basestring):
                raise TypeError('Proxy :type must be string')
            elif not regex.RE.PROXY_TYPE.match(proxy['type']):
                raise ValueError('Unsupported proxy type: %s' % proxy['type'])

            proxy['host'] = config.get('host') or config.get('ip') or config.get('server')

            if not isinstance(proxy['host'], basestring):
                raise TypeError('Proxy :host must be string')
            elif not (proxy['host'] == 'localhost' or regex.RE.IPv4.match(proxy['host'])):
                raise ValueError('Unsupported proxy host: %s' % proxy['host'])

            proxy['port'] = config.get('port')

            if isinstance(proxy['port'], int):
                proxy['port'] = str(proxy['port'])
            elif not isinstance(proxy['port'], basestring):
                raise TypeError('Proxy :port must be string or int')
            if not regex.RE.PORT.match(proxy['port']):
                raise ValueError('Unsupported proxy port: %s' % proxy['port'])

            proxy_user = config.get('user') or config.get('login')
            proxy_passwd = config.get('passwd') or config.get('password')

            if proxy_user is not None and proxy_passwd is not None:
                if not (isinstance(proxy_user, basestring) and proxy_user):
                    raise TypeError('Proxy :user must be non-empty string')
                elif not (isinstance(proxy_passwd, basestring) and proxy_passwd):
                    raise TypeError('Proxy :password must be non-empty string')
                proxy['user'] = proxy_user
                proxy['passwd'] = proxy_passwd

        else:
            raise TypeError('Proxy must be set by URL or dict config')

        proxy_type = proxy['type'].lower()
        if proxy_type.startswith('http'):
            proxy_type = 'http'
        elif proxy_type == 'socks':
            proxy_type = 'socks5'
        proxy['type'] = proxy_type

        return proxy

    # ************************************************************************
    # :: cookies ::
    # ************************************************************************

    # TODO: fix

    _cookies_enabled = None

    @property
    def cookies_enabled(self):
        return bool(self._cookies_enabled)

    @cookies_enabled.setter
    def cookies_enabled(self, value):
        value = bool(value)
        if value != self._cookies_enabled:
            try:
                # TODO: patch navigator!
                self.execute_phantomjs_script('phantom.cookiesEnabled = %s' % dumps(value))
                self._cookies_enabled = value
            except Exception as e:
                raise PhantomError('Unable to change cookies settings :: %s' % str(e))


    @property
    def cookies(self):
        return self.get_cookies()


    # _add_cookie = PhantomJS.add_cookie

    # def add_cookie(self, name, value, domain=None, path='/',
    #                httponly=False, secure=False, expires=None):

    #     if not isinstance(name, basestring):
    #         raise TypeError("Cookie's :name must be string")
    #     elif domain is not None and not isinstance(domain, basestring):
    #         raise TypeError("Cookie's :domain must be string")
    #     elif not isinstance(path, basestring):
    #         raise TypeError("Cookie's :path must be string")
    #     elif expires is not None and not isinstance(expires, int):
    #         raise TypeError("Cookie's :expires must be int")

    #     cookie = {
    #         'name': name,
    #         'value': value,
    #     }

    #     if domain is not None:
    #         cookie['domain'] = domain
    #     else:
    #         url = self.url
    #         if url is not None and url.domain:
    #             cookie['domain'] = url.domain
    #             if url.tld:
    #                 cookie['domain'] += '.' + url.tld
    #         else:
    #             raise PhantomError("Cookie's :domain must be set")

    #     cookie['path'] = path
    #     cookie['httponly'] = bool(httponly)
    #     cookie['secure'] = bool(secure)

    #     if expires is None:
    #         expires = int(time()) + 60 * 60 * 24 * 7 # ?
    #     cookie['expires'] = expires * 1000

    #     try:
    #         result = self.execute_phantomjs_script(
    #             'return page.addCookie(%s)' % dumps(cookie) # phantom.addCookie ?
    #         )
    #         # always returns False, wtf?
    #         # if not result:
    #         #     raise Exception
    #         return result
    #     except Exception:
    #         raise PhantomError('Unable to add a cookie')


    # def delete_domain_cookie(self, name):
    #     if not isinstance(name, basestring):
    #         raise TypeError("Cookie's :name must be string")
    #     try:
    #         return self.execute_phantomjs_script('page.deleteCookie(%s)' % name)
    #     except Exception as e:
    #         raise PhantomError('Unable to delete a cookie :: %s' % str(e))

    # def delete_domain_cookies(self):
    #     try:
    #         self.execute_phantomjs_script('page.clearCookies()')
    #     except Exception as e:
    #         raise PhantomError('Unable to clear domain cookies :: %s' % str(e))

    # _delete_all_cookies = PhantomJS.delete_all_cookies

    # def delete_all_cookies(self):
    #     try:
    #         self.execute_phantomjs_script('phantom.clearCookies()')
    #     except Exception as e:
    #         raise PhantomError('Unable to clear all cookies :: %s' % str(e))

    # TODO: remove
    # def delete_all_cookies(self):
    #     self.open_blank_page()
    #     self.delete_all_cookies()

    # def save_cookies(self):
    #     pass

    # def load_cookies(self):
    #     pass

    # ************************************************************************
    # :: CSS stylesheets ::
    # ************************************************************************

    _load_stylesheets = None

    @property
    def load_stylesheets(self):
        return bool(self._load_stylesheets)

    @load_stylesheets.setter
    def load_stylesheets(self, value):
        value = bool(value)
        if value != self._load_stylesheets:
            try:
                self.execute_phantomjs_script(
                    'page.%sCallback(page.onResourceRequestedCallbacks, page.skipCSS)' %
                    ('remove' if value else 'add')
                )
                self._load_stylesheets = value
            except Exception as e:
                raise PhantomError('Unable to change CSS settings :: %s' % str(e))

    # ************************************************************************
    # :: screen ::
    # ************************************************************************

    # TODO: test

    _screen = None

    @property
    def screen(self):
        return self._screen['width'], self._screen['height']

    @screen.setter
    def screen(self, size):
        self._screen = self.get_screen(size)

        try:
            self.execute_phantomjs_script(
                'page.viewportSize = %s' %
                dumps({
                    'width': self._screen['window']['innerWidth'],
                    'height': self._screen['window']['innerHeight'],
                })
            )

            # self.set_window_size(
            #     self._screen['window']['innerWidth'],
            #     self._screen['window']['innerHeight'],
            # )

            self.execute_phantomjs_script(
                'page.setScreen(%s)' % dumps(self._screen)
            )
        except Exception as e:
            raise PhantomError('Unable to set the viewport size :: %s' % str(e))


    def get_screen(self, size=None):
        if size is None:
            size = weighted_choice(SCREEN_RESOLUTION)
        elif not (
            isinstance(size, (list, tuple)) and len(size) == 2 and
            isinstance(size[0], int) and isinstance(size[1], int)
        ):
            raise TypeError('Screen size must be tuple (int:width, int:height)')

        width = max(300, size[0]) # ?
        height = max(300, size[1]) # ?

        screen = {}
        screen['width'] = width
        screen['height'] = height
        screen['color_depth'] = SCREEN_COLOR_DEPTH
        screen['os_taskbar_height'] = choice(OS_TASKBAR_HEIGHT)
        screen['browser_taskbar_height'] = choice(BROWSER_TASKBAR_HEIGHT)
        screen['window.screen'] = {}
        screen['window.screen']['width'] = screen['width']
        screen['window.screen']['height'] = screen['height']
        screen['window.screen']['availWidth'] = screen['window.screen']['width']
        screen['window.screen']['availHeight'] = (
            screen['window.screen']['height'] - screen['os_taskbar_height']
        )
        screen['window.screen']['availLeft'] = 0
        screen['window.screen']['availTop'] = screen['os_taskbar_height']
        screen['window.screen']['colorDepth'] = screen['color_depth']
        screen['window.screen']['pixelDepth'] = screen['color_depth']
        screen['window'] = {}
        screen['window']['outerWidth'] = screen['window.screen']['availWidth']
        screen['window']['outerHeight'] = screen['window.screen']['availHeight']
        screen['window']['innerWidth'] = (
            screen['window']['outerWidth'] - choice(BROWSER_SCROOLBAR_WIDTH)
        )
        screen['window']['innerHeight'] = (
            screen['window']['outerHeight'] - screen['browser_taskbar_height']
        )
        screen['window']['screenX'] = 0
        screen['window']['screenY'] = screen['window.screen']['availTop']
        return screen

    # ************************************************************************
    # :: selectors ::
    # ************************************************************************

    def xpath(self, xpath, timeout=None):
        if not isinstance(xpath, basestring):
            raise TypeError(':xpath must be string')

        with custom_value(self, 'xpath_timeout', timeout):
            try:
                return self.find_elements_by_xpath(xpath)
            except Exception as e:
                raise PhantomError(
                    'Unable to find elements by xpath "%s" :: %s'
                    % (xpath, str(e))
                )

    def validate_elem(self, elem):
        if not isinstance(elem, WebElement):
            raise TypeError(':elem must be an instance of WebElement')

    # ************************************************************************
    # :: windows/popus/alers ::
    # ************************************************************************

    # def close_alert(self):
    #     try:
    #         self.switch_to.alert.dismiss()
    #     except NoAlertPresentException:
    #         pass

    def close_popups(self):
        try:
            if len(self.windows) > 1:

                for window in self.windows[:][1:]:
                    try:
                        self.switch_to_window(window)
                        #self.close_alert()
                        self.close()
                    except NoSuchWindowException:
                        continue

                self.switch_to_window(0)

        except Exception as e:
            raise PhantomError('Unable to close popup windows :: %s' % str(e))

    def switch_to_window(self, window=None):
        try:
            if window is None:
                window = self.windows[0]
            elif isinstance(window, int):
                window = self.windows[window]
            self.switch_to.window(window)
        except Exception as e:
            raise PhantomError(
                'Unable to switch to %s window :: %s' % (window, str(e))
            )

    @property
    def windows(self):
        return self.window_handles

    @property
    def current_window(self):
        return self.current_window_handle


    # ************************************************************************
    # :: driver timeouts ::
    # ************************************************************************

    # page load timeout
    # * also applied by default to navigation clicks and meta refresh
    _page_load_timeout = None

    @property
    def page_load_timeout(self):
        return self._page_load_timeout

    @page_load_timeout.setter
    def page_load_timeout(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(':page_load_timeout must be int or float')
        elif value <= 0:
            raise ValueError(':page_load_timeout must be > 0')
        if value != self._page_load_timeout:
            try:
                self.set_page_load_timeout(value)
                self._page_load_timeout = value
            except Exception as e:
                raise PhantomError('Unable to set :page_load_timeout :: %s' % str(e))


    # XPATH selector timeout (implicitly_wait)
    _xpath_timeout = None

    @property
    def xpath_timeout(self):
        return self._xpath_timeout

    @xpath_timeout.setter
    def xpath_timeout(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(':xpath_timeout must be int or float')
        elif value < 0:
            raise ValueError(':xpath_timeout must be >= 0')
        if value != self._xpath_timeout:
            try:
                self.implicitly_wait(value)
                self._xpath_timeout = value
            except Exception as e:
                raise PhantomError('Unable to set :xpath_timeout :: %s' % str(e))

    # ************************************************************************
    # :: navigation ::
    # ************************************************************************

    _history = None

    @property
    def history(self):
        return self._history

    @history.setter # ?
    def history(self, value):
        if not value:
            self._history = []
        elif not isinstance(value, list):
            raise TypeError(':history must be list')
        else:
            self._history = value


    @property
    def url(self):
        return URL(self.current_url) if not self.blank_state() else None


    # 1 + max page load retries
    _page_load_attempts = None

    @property
    def page_load_attempts(self):
        return self._page_load_attempts

    @page_load_attempts.setter
    def page_load_attempts(self, value):
        if not isinstance(value, int):
            raise TypeError(':page_load_attempts must be int')
        elif value < 1:
            raise ValueError(':page_load_attempts must be > 0')
        self._page_load_attempts = value


    # TODO: SPA clicks
    @contextmanager
    def _wait_for_page_load(self, timeout, poll_timeout=0.1):
        old_page_html = self.xpath('html', timeout=0)
        if not old_page_html:
            raise PhantomError('<html> element cannot be found on the page')

        timestamp = time() + timeout
        # | ?
        yield

        while time() < timestamp:
            sleep(poll_timeout)

            page_html = self.xpath('html', timeout=0)
            if (
                page_html and
                page_html[0].id != old_page_html[0].id and
                self.ready_state() # rly?
                ):
                return

        raise PhantomError('Page load timeout after %s seconds' % timeout)


    def _network_request(func):

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            request_url = func(self, *args, **kwargs)
            if not request_url:
                return
            elif request_url == BLANK_URL:
                # self.history.append(BLANK_URL)
                return

            http_meta = self.execute_phantomjs_script('return page.httpMeta')
            # TODO: 304?
            if not (http_meta and http_meta.get('response')):
                raise PhantomError('Unable to load URL: %s' % request_url)

            http_meta['request']['url'] = request_url

            self.history.append(http_meta['response']['url'])

            for r in http_meta:
                # TODO: ordered dict
                http_meta[r]['headers'] = dict(
                    [(h['name'], h['value']) for h in http_meta[r]['headers']]
                )

            # i don't give a shit about the trailing slash
            if http_meta['response']['url'].rstrip('/') != request_url.rstrip('/'):
                http_meta['response']['redirect'] = True
            else:
                http_meta['response']['redirect'] = False

            return http_meta

        return wrapper


    # shown in history if "content:url" is set
    @_network_request
    def wait_for_meta_refresh(self, timeout=None):
        if timeout is None:
            timeout = self.page_load_timeout
        elif not isinstance(timeout, (int, float)):
            raise TypeError(':timeout must be int, float or None')
        elif timeout <= 0:
            raise ValueError(':timeout must be > 0')

        try:
            meta_elem = self.xpath(XPATH['meta_refresh'], timeout=0)
            if not meta_elem:
                return
            refresh_content = meta_elem[0].get_attribute('content')
            meta_refresh_match = RE['meta_refresh'].match(refresh_content)
            if not meta_refresh_match:
                return
            meta_refresh = meta_refresh_match.groupdict()
            if meta_refresh.get('url'):
                target_url = urljoin(self.current_url, meta_refresh['url'])
            else:
                target_url = self.current_url
                # target_url = self.current_url.split('#')[0] # ?
            with self._wait_for_page_load(timeout + int(meta_refresh['timeout'])):
                return target_url

        except Exception as e:
            raise PhantomError(
                'Failed on waiting for meta refresh :: %s' % str(e)
            )


    @_network_request
    def open(self, url, timeout=None, attempts=None, headers=None):
        if not isinstance(url, basestring):
            raise TypeError(':url must be string')

        with custom_value(self, 'default_headers', headers):
            with custom_value(self, 'page_load_timeout', timeout):
                with custom_value(self, 'page_load_attempts', attempts):
                    attempts = self.page_load_attempts
                    try:
                        while attempts:
                            attempts -= 1
                            try:
                                self.get(url)
                                return url
                            except Exception:
                                if attempts > 0:
                                    continue
                                raise
                    except Exception as e:
                        raise PhantomError(
                            'Unable to load URL: %s :: %s' % (url, str(e))
                        )


    def open_blank_page(self, timeout=1.0):
        try:
            with custom_value(self, 'page_load_timeout', timeout):
                self.get(BLANK_URL)
            if not self.blank_state():
                raise Exception
            # self.history.append(BLANK_URL)
        except Exception as e:
            raise PhantomError(
                'Unable to load the blank page: %s' % str(e)
            )


    _forward = PhantomJS.forward

    @_network_request
    def forward(self, timeout=None, attempts=None):
        with custom_value(self, 'page_load_timeout', timeout):
            with custom_value(self, 'page_load_attempts', attempts):
                attempts = self.page_load_attempts
                try:
                    while attempts:
                        attempts -= 1
                        try:
                            url_before = self.current_url
                            self._forward()
                            if self.current_url != url_before:
                                return self.current_url # ?
                        except Exception:
                            if attempts > 0:
                                continue
                            raise
                except Exception as e:
                    raise PhantomError('Unable to go forward :: %s' % str(e))

    _back = PhantomJS.back

    @_network_request
    def back(self, timeout=None, attempts=None):
        with custom_value(self, 'page_load_timeout', timeout):
            with custom_value(self, 'page_load_attempts', attempts):
                attempts = self.page_load_attempts
                try:
                    while attempts:
                        attempts -= 1
                        try:
                            url_before = self.current_url
                            self._back()
                            if self.current_url != url_before:
                                return self.current_url # ?
                        except Exception:
                            if attempts > 0:
                                continue
                            raise
                except Exception as e:
                    raise PhantomError('Unable to go backward :: %s' % str(e))

    _refresh = PhantomJS.refresh

    @_network_request
    def refresh(self, timeout=None, attempts=None):
        with custom_value(self, 'page_load_timeout', timeout):
            with custom_value(self, 'page_load_attempts', attempts):
                attempts = self.page_load_attempts
                try:
                    while attempts:
                        attempts -= 1
                        try:
                            url_before = self.current_url
                            self._refresh()
                            return url_before # ?
                        except Exception:
                            if attempts > 0:
                                continue
                            raise
                except Exception as e:
                    raise PhantomError('Unable to refresh the current page :: %s' % str(e))


    # TODO: a:scope; if elem isn't specified, check if there is an elem under the cursor
    @_network_request
    def click(self, elem=None, timeout=None, wait=True, if_visible=True, if_enabled=True):
        url = None

        if elem:
            self.validate_elem(elem)

            if elem.tag_name == 'a':
                href = elem.get_attribute('href')
                if href:
                    url = urljoin(self.current_url, href)

            elif elem.get_attribute('type') == 'submit':
                with custom_value(self, 'xpath_timeout', 0):
                    form = elem.find_elements_by_xpath('.//ancestor::form[@action]')
                    if form:
                        action = form.get_attribute('action')
                        if action:
                            url = urljoin(self.current_url, action)

        with custom_value(self, 'page_load_timeout', timeout):
            try:
                if elem:
                    if if_visible and not self.element_visible(elem):
                        raise PhantomError('element is not visible to user')
                    elif if_enabled and not elem.is_enabled():
                        raise PhantomError('element is not enabled')
                    self.move_mouse_to_element(elem)

                ac = ActionChains(self).click(elem)
                if elem is None or not wait:
                    ac.perform()
                else:
                    with self._wait_for_page_load(timeout):
                        ac.perform()

                return url

            except Exception as e:
                raise PhantomError(
                    'Unable to click on %s :: %s' %
                    (
                        (
                            '<%s> element' % elem.tag_name
                            if elem is not None else 'the page'
                        ),
                        str(e)
                    )
                )

    # ************************************************************************
    # :: mouse ::
    # ************************************************************************

    # TODO: refactor

    # TODO: ensure position in viewport
    def move_mouse_by_offset(self, x, y):
        if not (isinstance(x, int) and isinstance(y, int)):
            raise TypeError('"x" and "y" offsets must be int')
        try:
            ActionChains(self).move_by_offset(x, y).perform()
        except Exception as e:
            raise PhantomError(
                'Unable to move the mouse by an offset %s :: %s'
                % (str((x, y)), str(e))
            )

    def move_mouse_to_element(self, elem):
        self.validate_elem(elem)
        try:
            # location = elem.location
            # size = elem.size
            # if self.position_in_viewport(
            #     location['x'] + size['width'] / 2,
            #     location['y'] + size['height'] / 2,
            # )
            ActionChains(self).move_to_element(elem).perform()
        except Exception as e:
            raise PhantomError(
                'Unable to move the mouse to <%s> element :: %s'
                % (elem.tag_name, str(e))
            )

    def move_mouse_to_element_by_offset(self, elem, x, y):
        self.validate_elem(elem)
        if not (isinstance(x, int) and isinstance(y, int)):
            raise TypeError('"x" and "y" offsets must be int')
        try:
            # location = elem.location
            # if self.position_in_viewport(
            #     location['x'] + x,
            #     location['y'] + y,
            # )
            ActionChains(self).move_to_element_with_offset(elem, x, y).perform()
        except Exception as e:
            raise PhantomError(
                'Unable to move the mouse by an offset %s of <%s> element :: %s'
                % (str((x, y)), elem.tag_name, str(e))
            )

    # TODO: ensure the position in the viewport
    def move_mouse_to_position(self, x=None, y=None):
        if x is not None and not isinstance(x, int):
            raise TypeError('"x" offset must be int or None')
        elif y is not None and not isinstance(y, int):
            raise TypeError('"y" offset must be int or None')
        try:
            if x is None or y is None:
                view_width, view_height = self.view_size
                x_offset, y_offset = self.page_offset
            if x is None:
                x = randint(x_offset + 5, x_offset + view_width - 5)
            else:
                x = abs(x)
            if y is None:
                y = randint(y_offset + 5, y_offset + view_height - 5)
            else:
                y = abs(y)
            html_elem = self.xpath('html', timeout=0)
            if not html_elem:
                raise PhantomError(
                    '<html> element cannot be found on the page'
                )
            # is <html> node always(!) in (0, 0) position?
            # i have no fucking idea, really
            self.move_mouse_to_element_by_offset(html_elem[0], x, y)
        except Exception as e:
            raise PhantomError(
                'Unable to move the mouse to %s position :: %s'
                % (str((x, y)), str(e))
            )

    # ************************************************************************
    # :: scrolling ::
    # ************************************************************************

    # TODO: refactor

    def scroll_down(self, y=None):
        if y is not None and not isinstance(y, int):
            raise TypeError('"y" offset must be int or None')
        try:
            if y is None:
                self.execute_script('window.scrollBy(0, document.body.scrollHeight)')
            else:
                self.execute_script('window.scrollBy(0, %s)' % abs(y))
        except Exception as e:
            raise PhantomError('Unable to scroll down :: %s' % str(e))

    def scroll_up(self, y=None):
        if y is not None and not isinstance(y, int):
            raise TypeError('"y" offset must be int or None')
        try:
            if y is None:
                self.execute_script(
                    'window.scrollBy(0, -document.body.scrollHeight)'
                )
            else:
                self.execute_script('window.scrollBy(0, -%s)' % abs(y))
        except Exception as e:
            raise PhantomError('Unable to scroll up :: %s' % str(e))

    def scroll_right(self, x=None):
        if x is not None and not isinstance(x, int):
            raise TypeError('"x" offset must be int or None')
        try:
            if x is None:
                self.execute_script(
                    'window.scrollBy(document.body.scrollWidth, 0)'
                )
            else:
                self.execute_script('window.scrollBy(%s, 0)' % abs(x))
        except Exception as e:
            raise PhantomError('Unable to scroll right :: %s' % str(e))

    def scroll_left(self, x=None):
        if x is not None and not isinstance(x, int):
            raise TypeError('"x" offset must be int or None')
        try:
            if x is None:
                self.execute_script(
                    'window.scrollBy(-document.body.scrollWidth, 0)'
                )
            else:
                self.execute_script('window.scrollBy(-%s, 0)' % abs(x))
        except Exception as e:
            raise PhantomError('Unable to scroll left :: %s' % str(e))

    def scroll_by_offset(self, x, y):
        if not (isinstance(x, int) and isinstance(y, int)):
            raise TypeError('"x" and "y" offsets must be int')
        try:
            self.execute_script('window.scrollBy(%s, %s)' % (x, y))
        except Exception as e:
            raise PhantomError(
                'Unable to scroll by an offset %s :: %s'
                % (str((x, y)), str(e))
            )

    def scroll_to_element(self, elem):
        self.validate_elem(elem)
        try:
            location = elem.location
            self.execute_script(
                'window.scrollTo(%s, %s)' % (location['x'], location['y'])
            )
        except Exception as e:
            raise PhantomError(
                'Unable to scroll to <%s> element :: %s'
                % (elem.tag_name, str(e))
            )

    # ************************************************************************
    # :: internal states ::
    # ************************************************************************

    def blank_state(self):
        if (
            not self.current_url or
            self.current_url == BLANK_URL
        ):
            return True
        else:
            return False

    def ready_state(self):
        return self.execute_script('return document.readyState') == 'complete'


    # TODO: fully/half visible
    def element_visible(self, elem):
        self.validate_elem(elem)
        try:
            if not elem.is_displayed():
                return False
            location = elem.location
            size = elem.size
            view_width, view_height = self.view_size
            x_offset, y_offset = self.page_offset
            return (
                (location['x'] + size['width']) > x_offset and
                (location['y'] + size['height']) > y_offset and
                location['x'] < (x_offset + view_width) and
                location['y'] < (y_offset + view_height)
            )
        except Exception as e:
            raise PhantomError(
                "Unable to detect <%s> element's visibility :: %s"
                % (elem.tag_name, str(e))
            )

    def position_in_viewport(self, x, y):
        if not (isinstance(x, int) and isinstance(y, int)):
            raise TypeError('"x" and "y" coordinates must be int')

        view_width, view_height = self.view_size
        x_offset, y_offset = self.page_offset
        if (
            x >= x_offset and
            y >= y_offset and
            x < (x_offset + view_width) and
            y < (y_offset + view_height)
        ):
            return True
        else:
            return False


    @property
    def view_size(self):
        try:
            # view_width = self.execute_script('return window.innerWidth')
            # view_height = self.execute_script('return window.innerHeight')
            view_width = self._screen['window']['innerWidth']
            view_height = self._screen['window']['innerHeight']
            return view_width, view_height
        except Exception as e:
            raise PhantomError('Unable to get the view size :: %s' % str(e))

    @property
    def page_offset(self):
        try:
            page_x_offset = self.execute_script('return window.pageXOffset')
            page_y_offset = self.execute_script('return window.pageYOffset')
            return page_x_offset, page_y_offset
        except Exception as e:
            raise PhantomError('Unable to get the page offset :: %s' % str(e))

    @property
    def scroll_size(self):
        try:
            scroll_width = self.execute_script('return document.body.scrollWidth')
            scroll_height = self.execute_script('return document.body.scrollHeight')
            return scroll_width, scroll_height
        except Exception as e:
            raise PhantomError('Unable to get the scroll size :: %s' % str(e))

    # ************************************************************************
    # :: screenshots ::
    # ************************************************************************

    def save_screenshot(self, filename=None, dir=None):
        if not filename:
            filename = str(int(time())) + '-' + self._id
        elif not isinstance(filename, basestring):
            raise TypeError(':filename must be string')

        if not dir:
            dir = self.screenshots_dir or '.'
        elif not isinstance(dir, basestring):
            raise TypeError(':dir must be string')

        filepath = os.path.realpath(os.path.join(dir, filename))
        if not filepath.endswith('.png'):
            filepath += '.png'

        dirpath = os.path.dirname(filepath)

        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)

        try:
            self.get_screenshot_as_file(filepath)
        except Exception as e:
            raise PhantomError(
                'Unable to save a screenshot "%s" :: %s'
                % (filepath, str(e))
            )

    # ************************************************************************
    # :: PhantomJS scripts executor ::
    # ************************************************************************

    def execute_phantomjs_script(self, script):
        if not isinstance(script, basestring):
            raise TypeError(':script must be string')
        elif not script.strip():
            raise ValueError(':script must be non-empty string')

        script = script.strip()
        if not script[-1] == ';':
            script += ';'

        try:
            result = self.execute(
                'executePhantomScript',
                {
                    'script': 'var page = this; %s' % script,
                    'args': [],
                }
            )['value']
        except Exception as e:
            raise PhantomError(
                'Unable to execute the phantomjs script :: %s' % str(e)
            )

        if isinstance(result, dict) and 'stack' in result:
            raise PhantomError('PhantomJS traceback :: ' + str(result['stack']))

        return result

    # ************************************************************************

    # def wait_element_clickable_by_xpath(self, xpath):
    #     WebDriverWait(self, self.config['xpath_timeout']).until(
    #         EC.element_to_be_clickable((By.XPATH, xpath))
    #     )

    # ************************************************************************


    # does this shit really work?
    # who knows...




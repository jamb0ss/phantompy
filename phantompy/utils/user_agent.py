# -*- coding: utf-8 -*-

from random import choice, randint
from . import weighted_choice
from .datatypes import DataObject


__all__ = ['generate_user_agent', 'generate_navigator', 'UserAgentError']


# TODO: popularity
PLATFORM = {
    'win': (
        'Windows NT 5.1', # Windows XP
        'Windows NT 6.1', # Windows 7
        'Windows NT 6.2', # Windows 8
        'Windows NT 6.3', # Windows 8.1
        'Windows NT 10.0', # Windows 10
    ),
    'mac': (
        'Macintosh; Intel Mac OS X 10.8',
        'Macintosh; Intel Mac OS X 10.9',
        'Macintosh; Intel Mac OS X 10.10',
        'Macintosh; Intel Mac OS X 10.11',
    ),
    'linux': (
        'X11; Linux',
        'X11; Ubuntu; Linux',
    ),
}

SUBPLATFORM = {
    'win': (
        ('', 'Win32'), # 32bit
        ('Win64; x64', 'Win32'), # 64bit
        ('WOW64', 'Win32'), # 32bit process / 64bit system
    ),
    'linux': (
        ('i686', 'Linux i686'), # 32bit
        ('x86_64', 'Linux x86_64'), # 64bit
        ('i686 on x86_64', 'Linux i686 on x86_64'), # 32bit process / 64bit system
    ),
    'mac': 'MacIntel', # 32bit, 64bit
}

NAVIGATOR = {
    'chrome': ('win', 'linux', 'mac'),
    'firefox': ('win', 'linux', 'mac'),
    # 'ie': ('win', ),
}

COMMON_NAVIGATOR_PROPERTIES = {
    'vendorSub': '',
    'appCodeName': 'Mozilla',
    'appName': 'Netscape',
    'appVersion': '5.0', # TODO: no no no!
    'product': 'Gecko',
    'language': 'en-US',
    'languages': 'en-US,en',
    'onLine': True,
    'cookieEnabled': True, # rly?
    #geolocation
}

SPECIFIC_NAVIGATOR_PROPERTIES = {
    'chrome': {
        'vendor': 'Google Inc.',
        'productSub': '20030107',
    },
    'firefox': {
        'vendor': '',
        'productSub': '20100101',
    },
    'ie': {
        'vendor': '',
    },
}

USERAGENT_TEMPLATE = {
    'firefox': (
        'Mozilla/5.0 (%(platform)s; rv:%(version)s) '
        'Gecko/%(geckotrail)s Firefox/%(version)s'
    ),
    'chrome': (
        'Mozilla/5.0 (%(platform)s) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/%(version)s Safari/537.36'
    ),
    'ie': {
        'v<11': 'Mozilla/5.0 (compatible; MSIE %(version)s; %(platform)s; Trident/5.0)',
        'v=11': 'Mozilla/5.0 (%(platform)s; Trident/7.0; rv:11.0) like Gecko',
    }
}

GECKOTRAIL_DESKTOP = '20100101'

# TODO: popularity
FIREFOX_VERSION = (
    '31.0',
    '33.0',
    '34.0',
    '35.0',
    '36.0',
    '37.0',
    '38.0',
    '39.0',
    '40.0',
    '41.0',
    '42.0',
    '43.0',
    '44.0',
    '45.0',
    '46.0',
)

# TODO: popularity
CHROME_BUILD = (
    (34, 1847, 1915),
    (35, 1916, 1984),
    (36, 1985, 2061),
    (37, 2062, 2124),
    (38, 2125, 2170),
    (39, 2171, 2213),
    (40, 2214, 2271),
    (41, 2272, 2310),
    (42, 2311, 2356),
    (43, 2357, 2402),
    (44, 2403, 2453),
    (45, 2454, 2489),
    (46, 2490, 2525),
    (47, 2526, 2563),
    (48, 2564, 2565),
)

MAC_CHROME_BUILD_RANGE = {
    '10.8': (0, 8),
    '10.9': (0, 5),
    '10.10': (0, 5),
    '10.11': (0, 1),
}

# IE_VERSION = (
#     '11.0',
#     '10.0',
#     '9.0',
# )

# Navigators popularity (%)
NAVIGATOR_POPULARITY = {
    'chrome': 58,
    'firefox': 34,
    'ie': 8,
}

# Platform popularity (%)
PLATFORM_POPULARITY = {
    'win': 76,
    'mac': 18,
    'linux': 6,
}


class UserAgentError(Exception):
    """user_agent::UserAgentError"""


def build_navigator_version(navigator, platform):
    if navigator == 'firefox':
        return choice(FIREFOX_VERSION)
    elif navigator == 'ie':
        if platform.startswith('Windows NT 5.1'): # XP
            return choice(['9.0', '10.0'])
        else:
            return '11.0'
    elif navigator == 'chrome':
        build = choice(CHROME_BUILD)
        return '%d.0.%d.%d' % (
            build[0],
            randint(build[1], build[2]),
            randint(0, 99),
        )


def fix_chrome_mac_platform(platform):
    old_ver = platform.split('OS X ')[1]
    build = choice(MAC_CHROME_BUILD_RANGE[old_ver])
    new_ver = old_ver.replace('.', '_') + '_' + str(build)
    return 'Macintosh; Intel Mac OS X %s' % new_ver


def generate_navigator(platform=None, navigator=None, silent=True):
    """
    Generates web navigator's config

    :param platform: limit a list of platforms
    :type platform: string or list/tuple or None
    :param navigator: limit a list of web-browsers
    :type navigator: string or list/tuple or None
    :return: navigator's config (dict)
    """
    if isinstance(platform, basestring):
        if platform in PLATFORM:
            platform_choices = [platform]
        else:
            raise UserAgentError('Unsupported platform: %s' % platform)
    elif isinstance(platform, (list, tuple, set)):
        platform_choices = []
        for p in platform:
            if p in PLATFORM:
                platform_choices.append(p)
            elif not silent:
                raise UserAgentError('Unsupported platform: %s' % p)
    elif platform is None:
        platform_choices = PLATFORM.keys()
    else:
        raise TypeError(':platform must be string or list/tuple/set')

    if isinstance(navigator, basestring):
        if navigator in NAVIGATOR:
            navigator_choices = [navigator]
        else:
            raise UserAgentError('Unsupported navigator: %s' % navigator)
    elif isinstance(navigator, (list, tuple, set)):
        navigator_choices = []
        for n in navigator:
            if n in NAVIGATOR:
                navigator_choices.append(n)
            elif not silent:
                raise UserAgentError('Unsupported navigator: %s' % n)
    elif navigator is None:
        navigator_choices = NAVIGATOR.keys()
    else:
        raise TypeError(':navigator must be string or list/tuple/set')

    aviable_choices = []
    for navigator in navigator_choices:
        for platform in platform_choices:
            if platform in NAVIGATOR[navigator]:
                aviable_choices.append([
                    (navigator, platform),
                    (
                        NAVIGATOR_POPULARITY[navigator] *
                        PLATFORM_POPULARITY[platform]
                    )
                ])

    if aviable_choices:
        navigator_name, platform_name = weighted_choice(aviable_choices)
    else:
        raise UserAgentError(
            "Unable to generate navigator's config from a given "
            "combination of aviable platforms and navigators"
        )

    if platform_name == 'win':
        subplatform, navigator_platform = choice(SUBPLATFORM['win'])
        win_platform = choice(PLATFORM['win'])
        if subplatform:
            platform = win_platform + '; ' + subplatform
        else:
            platform = win_platform
        oscpu = platform
    elif platform_name == 'linux':
        subplatform, navigator_platform = choice(SUBPLATFORM['linux'])
        platform = choice(PLATFORM['linux']) + ' ' + subplatform
        oscpu = navigator_platform
    elif platform_name == 'mac':
        navigator_platform = SUBPLATFORM['mac']
        platform = choice(PLATFORM['mac'])
        if navigator_name == 'chrome':
            platform = fix_chrome_mac_platform(platform)
        oscpu = platform[11:]

    navigator_version = build_navigator_version(navigator_name, platform)

    if navigator_name == 'firefox':
        user_agent = USERAGENT_TEMPLATE['firefox'] % {
            'platform': platform,
            'version': navigator_version,
            'geckotrail': GECKOTRAIL_DESKTOP,
        }
    elif navigator_name == 'chrome':
        user_agent = USERAGENT_TEMPLATE['chrome'] % {
            'platform': platform,
            'version': navigator_version,
        }
    elif navigator_name == 'ie':
        if navigator_version == '11.0':
            user_agent = USERAGENT_TEMPLATE['ie']['v=11'] % {
                'platform': platform
            }
        else:
            user_agent = USERAGENT_TEMPLATE['ie']['v<11'] % {
                'platform': platform,
                'version': navigator_version
            }

    navigator = DataObject(COMMON_NAVIGATOR_PROPERTIES)
    navigator.update(SPECIFIC_NAVIGATOR_PROPERTIES[navigator_name])
    navigator['platform'] = navigator_platform
    navigator['__name__'] = navigator_name
    navigator['__version__'] = navigator_version
    navigator['__platform__'] = platform_name
    navigator['userAgent'] = user_agent
    if navigator_name == 'firefox':
        navigator['oscpu'] = oscpu
    if navigator_name == 'ie' and navigator_version != '11.0':
        navigator['appName'] = 'Microsoft Internet Explorer'

    return navigator


def generate_user_agent(platform=None, navigator=None):
    """
    Generates HTTP User-Agent header

    :param platform: limit list of platforms for generation
    :type platform: string or list/tuple or None
    :param navigator: limit list of browser engines for generation
    :type navigator: string or list/tuple or None
    :return: User-Agent string
    :return type: string
    """
    return generate_navigator(platform=platform, navigator=navigator)['userAgent']



import sys
defaults = {'which_notifier': 'mqtt',
            'host': '127.0.0.1',
            'mqtt_user': 'mqtt',
            'mqtt_pass': 'mqtt_password',
            'mqtt_port': 1883,
            'mqtt_clientid': 'rpi-remote-lr',
            'mqtt_path': 'homeassistant/remote/livingroom',
            'mqtt_retain': False,
            'mqtt_qos': 0,
            'mqtt_version': 'v5',
            'logbackups': 1,
            'debug': False}

try:
    import data.settings as overrides
    has_overrides = True
except ImportError:
    has_overrides = False
if sys.version_info < (3, 0):
    _reload = reload
elif sys.version_info >= (3, 4):
    from importlib import reload as _reload
else:
    from imp import reload as _reload


def Reload():
    if has_overrides:
        _reload(overrides)


def Get(name):
    setting = None
    if has_overrides:
        setting = getattr(overrides, name, None)
    if not setting:
        setting = defaults.get(name, None)
    return setting

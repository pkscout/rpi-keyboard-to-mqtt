import resources.config as config
import os

import re
import time
import traceback
import threading
import uuid
from datetime import datetime
import keyboard
from resources.lib.notifiers import MqttNotifier, NoNotifier
from resources.lib.xlogger import Logger
try:
    import psutil
    has_psutil = True
except ImportError:
    has_psutil = False


def pick_notifier(whichnotifier, lw):
    lw.log(['setting up %s notifier' % str(whichnotifier)])
    if not whichnotifier:
        return NoNotifier(config=config)
    if whichnotifier.lower() == 'mqtt':
        return MqttNotifier(config=config)
    else:
        lw.log(['invalid notifier specified'])
        return None


class OtherSensors(threading.Thread):

    def __init__(self, lw):
        super(OtherSensors, self).__init__()
        self.LW = lw
        self.UPDATE_INTERVAL = config.Get('sensor_update_interval')
        self.KEEPRUNNING = True
        self.RUNNING = True
        self.NOTIFIER = pick_notifier(config.Get('which_notifier'), lw)
        self.STARTUPTIME = datetime.now()
        self.LW.log(self.NOTIFIER.Send(
            ':'.join(re.findall('..', '%012x' %
                     uuid.getnode())), 'Mac address',
            category='diagnostic',
            icon='mdi:ethernet'))
        if has_psutil:
            self.LW.log(self.NOTIFIER.Send(
                psutil.cpu_percent(), 'CPU Load',
                unit='%',
                category='diagnostic',
                icon='mdi:cpu-32-bit'))
            self.LW.log(self.NOTIFIER.Send(
                psutil.cpu_percent(), 'Memory Used',
                unit='%',
                category='diagnostic',
                icon='mdi:memory'))
        self.LW.log(self.NOTIFIER.Send(
            '0s', 'Uptime',
            category='diagnostic',
            icon='mdi:clock-check-outline'))

    def Stop(self):
        self.KEEPRUNNING = False

    def Running(self):
        return self.RUNNING

    def _get_uptime(self):
        up_time = datetime.now() - self.STARTUPTIME
        fmt = ""
        d = {"days": up_time.days}
        d["hours"], rem = divmod(up_time.seconds, 3600)
        d["minutes"], d["seconds"] = divmod(rem, 60)
        if d['days'] > 0:
            fmt = fmt + "{days}d "
        if d['hours'] > 0:
            fmt = fmt + "{hours}h "
        if d['minutes'] > 0:
            fmt = fmt + "{minutes}m "
        if d['seconds'] > 0:
            fmt = fmt + "{seconds}s"
        return fmt.format(**d)

    def run(self):
        while self.KEEPRUNNING:
            time.sleep(self.UPDATE_INTERVAL)
            self.LW.log(self.NOTIFIER.Send(
                self._get_uptime(), 'Uptime',
                category='diagnostic',
                icon='mdi:clock-check-outline',
                log=False))
        self.RUNNING = False


class RemoteForward:

    def __init__(self, lw):
        self.LW = lw
        self.KEEPRUNNING = True
        self.NOTIFIER = pick_notifier(config.Get('which_notifier'), lw)
        self.HOLDMIN = config.Get('holdmin')
        self.LW.log(self.NOTIFIER.Send(
            '-1', 'Key Press',
            force_update=True,
            icon='mdi:button-pointer'))

    def Start(self):
        self.LW.log(['starting up RemoteForward'], 'info')
        try:
            down_time = None
            last_update = datetime.now()
            while self.KEEPRUNNING:
                e = keyboard.read_event()
                if e.event_type == 'down' and not down_time:
                    down_time = datetime.now()
                    self.LW.log(["key down at " + str(down_time)])
                if e.event_type == 'up':
                    up_time = datetime.now()
                    hold_time = (up_time - down_time).total_seconds() * 1000
                    down_time = None
                    self.LW.log(["recieved code: " + str(e.scan_code)])
                    self.LW.log(["held for %sms" % str(hold_time)])
                    if hold_time < self.HOLDMIN:
                        code = str(e.scan_code)
                    else:
                        code = str(e.scan_code) + '-L'
                    self.LW.log(self.NOTIFIER.Send(
                        code, 'Key Press',
                        force_update=True,
                        icon='mdi:button-pointer',
                        log=False))
        except KeyboardInterrupt:
            self.KEEPRUNNING = False
        except Exception as e:
            self.KEEPRUNNING = False
            self.LW.log([traceback.format_exc()], 'error')
            print(traceback.format_exc())


class Main:

    def __init__(self, thepath):
        lw = Logger(logfile=os.path.join(os.path.dirname(thepath), 'data', 'logs', 'logfile.log'),
                    numbackups=config.Get('logbackups'), logdebug=config.Get('debug'))
        lw.log(['script started, debug set to %s' %
                str(config.Get('debug'))], 'info')
        othersensors = OtherSensors(lw)
        othersensors.setDaemon(True)
        othersensors.start()
        remoteforward = RemoteForward(lw)
        remoteforward.Start()
        othersensors.Stop()
        while othersensors.Running():
            time.sleep(0.5)
        othersensors.join()
        lw.log(['closing down RemoteForward'], 'info')

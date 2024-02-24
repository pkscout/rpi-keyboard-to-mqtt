import resources.config as config
import os
import traceback
from datetime import datetime
import keyboard
from resources.lib.notifiers import MqttNotifier, NoNotifier
from resources.lib.xlogger import Logger


class RemoteForward:

    def __init__(self, lw):
        self.LW = lw
        self.KEEPRUNNING = True
        self.NOTIFIER = self._pick_notifier(config.Get('which_notifier'))
        self.HOLDMIN = config.Get('holdmin')
        self.STARTUPTIME = datetime.now()

    def Start(self):
        self.LW.log(['starting up RemoteForward'], 'info')
        try:
            down_time = None
            last_update = datetime.now()
            while self.KEEPRUNNING:
                if (datetime.now() - last_update).seconds > 2:
                    last_update = datetime.now()
                    self.LW.log(self.NOTIFIER.Send(
                        self._get_uptime(), 'Uptime',
                        category='diagnostic',
                        icon='mdi:clock-check-outline'))
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
                        icon='mdi:button-pointer'))
        except KeyboardInterrupt:
            self.KEEPRUNNING = False
        except Exception as e:
            self.KEEPRUNNING = False
            self.LW.log([traceback.format_exc()], 'error')
            print(traceback.format_exc())

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

    def _pick_notifier(self, whichnotifier):
        self.LW.log(['setting up %s notifier' % str(whichnotifier)])
        if not whichnotifier:
            return NoNotifier(config=config)
        if whichnotifier.lower() == 'mqtt':
            return MqttNotifier(config=config)
        else:
            self.LW.log(['invalid notifier specified'])
            return None


class Main:

    def __init__(self, thepath):
        self.LW = Logger(logfile=os.path.join(os.path.dirname(thepath), 'data', 'logs', 'logfile.log'),
                         numbackups=config.Get('logbackups'), logdebug=config.Get('debug'))
        self.LW.log(['script started, debug set to %s' %
                    str(config.Get('debug'))], 'info')
        self.REMOTEFORWARD = RemoteForward(self.LW)
        self.REMOTEFORWARD.Start()
        self.LW.log(['closing down RemoteForward'], 'info')

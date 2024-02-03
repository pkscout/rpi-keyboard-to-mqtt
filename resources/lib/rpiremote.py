import resources.config as config
import os
import keyboard
from resources.lib.notifiers import MqttNotifier, NoNotifier
from resources.lib.xlogger import Logger


class RemoteForward:

    def __init__(self, lw):
        self.LW = lw
        self.KEEPRUNNING = True
        self.NOTIFIER = self._pick_notifier(config.Get('which_notifier'))

    def Start(self):
        self.LW.log(['starting up RemoteForward'], 'info')
        try:
            while self.KEEPRUNNING:
                e = keyboard.read_event()
                if e.event_type == 'up':
                    self.LW.log(["recieved code: " + str(e.scan_code)])
                    loglines = self.NOTIFIER.Send(str(e.scan_code))
                    self.LW.log(loglines)
        except KeyboardInterrupt:
            self.KEEPRUNNING = False
        except Exception as e:
            self.KEEPRUNNING = False
            self.LW.log([traceback.format_exc()], 'error')
            print(traceback.format_exc())

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

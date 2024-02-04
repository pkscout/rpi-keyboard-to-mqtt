try:
    import paho.mqtt.publish as publish
    import paho.mqtt.client as mqtt
    import os
    has_mqtt = True
except ImportError:
    has_mqtt = False


class MqttNotifier:
    def __init__(self, config):
        self.MQTTAUTH = {'username': config.Get('mqtt_user'),
                         'password': config.Get('mqtt_pass')}
        self.MQTTHOST = config.Get('host')
        self.MQTTPORT = config.Get('mqtt_port')
        client = config.Get('mqtt_clientid')
        if not client:
            client = os.uname()[1]
        self.MQTTCLIENT = client
        path = config.Get('mqtt_path')
        if path[-1] != '/':
            path = path + '/'
        self.MQTTPATH = path + client
        self.MQTTRETAIN = config.Get('mqtt_retain')
        self.MQTTQOS = config.Get('mqtt_qos')
        version = config.Get('mqtt_version')
        if version == 'v5':
            self.MQTTVERSION = mqtt.MQTTv5
        elif version == 'v311':
            self.MQTTVERSION = mqtt.MQTTv311
        else:
            self.MQTTVERSION = mqtt.MQTTv31

    def Send(self, payload):
        loglines = []
        loglines.append('sending %s to mqtt' % payload)
        if has_mqtt:
            try:
                publish.single(self.MQTTPATH,
                               payload=payload,
                               retain=self.MQTTRETAIN,
                               qos=self.MQTTQOS,
                               hostname=self.MQTTHOST,
                               auth=self.MQTTAUTH,
                               client_id=self.MQTTCLIENT,
                               port=self.MQTTPORT,
                               protocol=self.MQTTVERSION)
            except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, ConnectionError, OSError) as e:
                loglines.append('MQTT connection problem: ' + str(e))
        else:
            loglines.append(
                'MQTT python libraries are not installed, no message sent')
        return loglines


class NoNotifier:
    def __init__(self, config):
        pass

    def Send(self, device, device_state):
        return []

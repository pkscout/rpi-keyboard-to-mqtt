import json
import os
import re
import uuid
try:
    import paho.mqtt.publish as publish
    import paho.mqtt.client as mqtt
    has_mqtt = True
except ImportError:
    has_mqtt = False


def _cleanup(item):
    if item:
        return re.sub(r'[^\w]', '_', item.lower())
    return item


class MqttNotifier:
    def __init__(self, config):
        self.MQTTAUTH = {'username': config.Get('mqtt_user'),
                         'password': config.Get('mqtt_pass')}
        self.MQTTHOST = config.Get('host')
        self.MQTTPORT = config.Get('mqtt_port')
        self.MQTTDISCOVER = config.Get('mqtt_discover')
        self.MQTTCLIENT = config.Get('mqtt_clientid')
        if not self.MQTTCLIENT:
            self.MQTTCLIENT = os.uname()[1]
        self.DEVICEID = _cleanup(config.Get('device_identifier'))
        if not self.DEVICEID:
            self.DEVICEID = hex(uuid.getnode())
        self.DEVICE_NAME = config.Get('device_name')
        if not self.DEVICE_NAME:
            self.DEVICE_NAME = self.MQTTCLIENT
        self.MQTTPATH = self._fix_mqtt_path(config.Get('mqtt_path'))
        self.MQTTRETAIN = config.Get('mqtt_retain')
        self.MQTTQOS = config.Get('mqtt_qos')
        version = config.Get('mqtt_version')
        if version == 'v5':
            self.MQTTVERSION = mqtt.MQTTv5
        elif version == 'v311':
            self.MQTTVERSION = mqtt.MQTTv311
        else:
            self.MQTTVERSION = mqtt.MQTTv31
        self.DEVICE = {'identifiers': [self.DEVICEID],
                       'name': self.DEVICE_NAME,
                       'manufacturer': config.Get('device_manufacturer'),
                       'model': config.Get('device_model'),
                       'sw_version': config.Get('device_version'),
                       'configuration_url': config.Get('device_config_url')}
        a_path = self._fix_mqtt_path(config.Get('availability_path'))
        self.AVAILABILITY_TOPIC = '%s/%s/%s' % (
            self.MQTTPATH, a_path, self.DEVICE_NAME)

    def _fix_mqtt_path(self, path):
        if path[-1] == '/':
            return path[:-1]
        else:
            return path

    def _mqtt_send(self, topic, payload):
        loglines = []
        loglines.append('topic: %s' % topic)
        loglines.append('payload: %s' % payload)
        if has_mqtt:
            try:
                publish.single(topic,
                               payload=payload,
                               retain=self.MQTTRETAIN,
                               qos=self.MQTTQOS,
                               hostname=self.MQTTHOST,
                               auth=self.MQTTAUTH,
                               client_id=self.MQTTCLIENT,
                               port=self.MQTTPORT,
                               protocol=self.MQTTVERSION)
            except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, ConnectionError, OSError) as e:
                loglines.append('MQTT connection problem: ' + str(e), 'error')
        else:
            loglines.append(
                'MQTT python libraries are not installed, no message sent', 'critical')
        return loglines

    def Send(self, sensor_type, payload, friendly_name, config_opts={}, send_config=False):
        loglines = []
        entity_id = _cleanup(friendly_name)
        topic = '%s/%s/%s/%s' % (self.MQTTPATH, sensor_type,
                                 self.DEVICE_NAME, entity_id)
        if self.MQTTDISCOVER and (config_opts or send_config):
            config_payload = {}
            mqtt_config = '%s/%s' % (topic, 'config')
            config_payload['name'] = friendly_name
            config_payload['unique_id'] = '%s_%s' % (self.DEVICEID, entity_id)
            config_payload['state_topic'] = '%s/%s' % (topic, 'state')
            config_payload['device'] = self.DEVICE
            config_payload['availability_topic'] = self.AVAILABILITY_TOPIC
            config_payload.update(config_opts)
            loglines = loglines + self._mqtt_send(
                mqtt_config, json.dumps(config_payload))
        mqtt_state = '%s/%s' % (topic, 'state')
        loglines = loglines + self._mqtt_send(mqtt_state, payload)
        return loglines

    def SendAvailability(self, status):
        return self._mqtt_send(self.AVAILABILITY_TOPIC, status)


class NoNotifier:
    def __init__(self, config):
        pass

    def Send(self, device, device_state):
        return []

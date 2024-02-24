try:
    import paho.mqtt.publish as publish
    import paho.mqtt.client as mqtt
    import json
    import os
    import re
    import uuid
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
        device_id = _cleanup(config.Get('device_identifier'))
        if not device_id:
            device_id = hex(uuid.getnode())
        device_name = config.Get('device_name')
        if not device_name:
            device_name = self.MQTTCLIENT
        path = config.Get('mqtt_path')
        if path[-1] != '/':
            path = path + '/'
        self.MQTTPATH = path + self.MQTTCLIENT
        self.MQTTRETAIN = config.Get('mqtt_retain')
        self.MQTTQOS = config.Get('mqtt_qos')
        version = config.Get('mqtt_version')
        if version == 'v5':
            self.MQTTVERSION = mqtt.MQTTv5
        elif version == 'v311':
            self.MQTTVERSION = mqtt.MQTTv311
        else:
            self.MQTTVERSION = mqtt.MQTTv31
        self.DEVICE = {'identifiers': [device_id],
                       'name': device_name,
                       'manufacturer': config.Get('device_manufacturer'),
                       'model': config.Get('device_model'),
                       'sw_version': config.Get('device_version'),
                       'configuration_url': config.Get('device_config_url')}

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
                loglines.append('MQTT connection problem: ' + str(e))
        else:
            loglines.append(
                'MQTT python libraries are not installed, no message sent')
        return loglines

    def Send(self, payload, friendly_name, force_update=False, category=None, icon=None):
        loglines = []
        entity_id = _cleanup(friendly_name)
        topic = '%s/%s/' % (self.MQTTPATH, entity_id)
        if self.MQTTDISCOVER:
            config_payload = {}
            mqtt_config = topic + 'config'
            config_payload['name'] = friendly_name
            config_payload['unique_id'] = 'LsBeEFYQBzTn4wZzxjq9_' + entity_id
            config_payload['state_topic'] = topic + 'state'
            config_payload['device'] = self.DEVICE
            if force_update:
                config_payload['force_update'] = force_update
            if category:
                config_payload['entity_category '] = category
            if icon:
                config_payload['icon'] = icon
            loglines = loglines + self._mqtt_send(
                mqtt_config, json.dumps(config_payload))
        loglines = loglines + self._mqtt_send(topic + 'state', payload)
        return loglines


class NoNotifier:
    def __init__(self, config):
        pass

    def Send(self, device, device_state):
        return []

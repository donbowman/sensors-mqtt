#!/usr/bin/env python3
# Copyright 2017 Don Bowman
# Released under Apache 2.0 License (https://www.apache.org/licenses/LICENSE-2.0)

import paho.mqtt.client as mqtt
import argparse
import socket
import sensors
import re
import time
import json

parser = argparse.ArgumentParser(description='Publish sensors to MQTT')
parser.add_argument('--username', metavar='username', type=str, nargs=1,
                    help='username for mqtt broker')
parser.add_argument('--password', metavar='password', type=str, nargs=1,
                    help='password for mqtt broker')
parser.add_argument('--port', metavar='Port', type=int, nargs=1,
                    help='Port for MQTT broker')
parser.add_argument('--host', metavar='Host', type=str, nargs=1,
                    help='Hostname for MQTT broker')
parser.add_argument('--delay', metavar='Delay', type=int, nargs=1,
                    help='Delay between publish', default=30)

args = parser.parse_args()
#import pdb; pdb.set_trace()

sensors.init()
cname = socket.gethostname()

client = mqtt.Client(cname)
client.username_pw_set(username=args.username[0],password=args.password[0])
client.tls_set()
client.connect(args.host[0],args.port[0])

client.loop_start()

for chip in sensors.ChipIterator("coretemp-*"):
    rname = re.sub("-","_", sensors.chip_snprintf_name(chip))
    for feature in sensors.FeatureIterator(chip):
        label = sensors.get_label(chip, feature)
        label = re.sub("Package id ","pkg_", label)
        label = re.sub("Core ","core_", label)
        path = "%s_%s" % (rname, label)
        s = {"device_class": "sensor",
             "name": "%s %s Temperature" % (cname, path),
             "state_topic": "sensor/%s/%s/state" % (cname, path),
             "unit_of_measurement": "°C",
             "value_template": "{{ value_json.temperature}}" }
        #print("homeassistant/sensor/%s/%s/config" % (cname, path) + "-->"+ json.dumps(s))
        client.publish("homeassistant/sensor/%s/%s/config" % (cname, path), json.dumps(s))

while True:
    time.sleep(args.delay)
    for chip in sensors.ChipIterator("coretemp-*"):
        rname = re.sub("-","_", sensors.chip_snprintf_name(chip))
        for feature in sensors.FeatureIterator(chip):
            label = sensors.get_label(chip, feature)
            label = re.sub("Package id ","pkg_", label)
            label = re.sub("Core ","core_", label)
            sfi = sensors.SubFeatureIterator(chip, feature)
            vals = [sensors.get_value(chip, sf.number) for sf in sfi]
            s = { "temperature": vals[0] }
            client.publish("sensor/%s/%s_%s/state" % (cname, rname, label), json.dumps(s))


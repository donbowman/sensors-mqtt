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
import pydbus
import subprocess
import os
import sys


parser = argparse.ArgumentParser(description='Publish sensors to MQTT')
parser.add_argument('--username', metavar='username', type=str, nargs=1,
                    help='username for mqtt broker')
parser.add_argument('--password', metavar='password', type=str, nargs=1,
                    help='password for mqtt broker')
parser.add_argument('--port', metavar='Port', type=int, nargs=1,
                    help='Port for MQTT broker', default=8883)
parser.add_argument('--host', metavar='Host', type=str, nargs=1,
                    help='Hostname for MQTT broker')
parser.add_argument('--verbose', help='Enable Verbose', action="store_true")
parser.add_argument('--delay', metavar='Delay', type=int, nargs=1,
                    help='Delay between publish', default=[30])

args = parser.parse_args()

os.environ['DISPLAY'] = ':0'

#import pdb; pdb.set_trace()
def on_message(mqttc, obj, msg):
    global args
    if (args.verbose):
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    if msg.topic == "cmnd/office/lock" and msg.payload.decode('ascii') == 'ON':
        subprocess.run(["/usr/bin/xdg-screensaver","lock"])
        subprocess.run(["/usr/bin/xset","dpms","force","off"])
        time.sleep(2)
        subprocess.run(["/usr/bin/xset","dpms","force","off"])


def on_connect(client, userdata, flags, rc):
    print("Connected <<%s>>" % str(rc))
    client.subscribe("cmnd/%s/lock" % cname)

def on_publish(mqttc, obj, mid):
    if (args.verbose):
        print("mid: " + str(obj) + str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    if (args.verbose):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

sensors.init()
cname = socket.gethostname().split(".")[0]

client = mqtt.Client("")
client.username_pw_set(username=args.username[0],password=args.password[0])
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message
#client.on_publish = on_publish
#client.on_subscribe = on_subscribe
connected = False
# Since this starts as the host comes up, we might not have IP/DNS/route
# If it connects, and later fails, systemd will restart for us.
while connected == False:
    try:
        client.connect(args.host[0],args.port[0])
        connected = True
    except socket.gaierror as e:
        print("Error connecting... sleep(1)/retry")
        time.sleep(1)

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
        if (args.verbose):
            print("homeassistant/sensor/%s/%s/config" % (cname, path) + "-->"+ json.dumps(s))
        client.publish("homeassistant/sensor/%s/%s/config" % (cname, path), json.dumps(s))

while True:
    time.sleep(args.delay[0])

    try:
        dbus = pydbus.SessionBus()
        ss = dbus.get("org.kde.screensaver", "/ScreenSaver")
        active = ss.GetActive()
        if (args.verbose):
            print("publish sensor/%s/lock ==> %s" % (cname, "ON" if active else "OFF"))
        client.publish("sensor/%s/lock" % cname, "ON" if active else "OFF")
# qdbus org.kde.screensaver /ScreenSaver org.freedesktop.ScreenSaver.GetActive

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
    except:
        pass

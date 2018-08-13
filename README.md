# sensors-mqtt

This is a very simple script/daemon that will take
your local sensors and publish them to HomeAssistant
over MQTT.

The pre-requisits are paho-mqtt and sensors.py:

    pip3 install paho-mqtt sensors.py pydbus

After that, just run it.

    python3 ./sensors-pub.py --username MQTTUSER --password MQTTPASS --port MQTTPORT --host MQTTHOST

You may wish to enable it with systemd, create a file sensors-pub.service as :

    [Unit]
    Description=sensors-pub -- publish local sensors to mqtt
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /home/USER/src/sensors-mqtt/sensors-pub.py --username MQTTUSER --password MQTTPASS --port MQTTPORT --host MQTTHOST
    Restart=on-failure
    SuccessExitStatus=3 4
    RestartForceExitStatus=3 4

    [Install]
    WantedBy=default.target

You would then

    cp sensors-pub.service /home/USER/.config/systemd/user/
    systemctl --user enable sensors-pub.service
    systemctl --user start sensors-pub.service



#!/bin/bash

model=$(tr -d '\0' < /proc/device-tree/model)

if [ "${model}" = "NVIDIA Jetson Nano Developer Kit" ]; then
    cat /sys/devices/57000000.gpu/devfreq/57000000.gpu/cur_freq
elif [ "${model}" = "NVIDIA Jetson Xavier NX Developer Kit" ]; then
    cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/cur_freq
elif [ "${model}" = "Jetson-AGX" ]; then
    cat /sys/devices/17000000.gv11b/devfreq/17000000.gv11b/cur_freq
else
    echo "This is not a Jetson"
fi

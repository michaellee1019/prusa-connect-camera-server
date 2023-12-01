#!/usr/bin/env bash
cd `dirname $0`
set -eux

sudo apt-get update
sudo apt-get install -y python3-pip python3-venv i2c-tools
sudo pip install -r requirements.txt
sudo raspi-config nonint do_i2c 0

# Be sure to use `exec` so that termination signals reach the python process,
# or handle forwarding termination signals manually
exec python3 src/main.py $@
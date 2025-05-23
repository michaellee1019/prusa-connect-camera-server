#!/bin/bash
UNAME=$(uname -s)

if [ "$UNAME" = "Linux" ]
then
    echo "Installing venv on Linux"
    sudo apt-get install -y python3.11-venv
fi
if [ "$UNAME" = "Darwin" ]
then
    echo "Installing Python 3.11 on macOS"
    brew install python@3.11
fi
python3 -m venv .venv && . .venv/bin/activate && pip3 install -r requirements.txt && python3 -m PyInstaller --onefile --hidden-import="googleapiclient" src/main.py
tar -czvf dist/archive.tar.gz dist/main meta.json
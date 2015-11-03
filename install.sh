#!/bin/bash

USER_HOME=$(eval echo ~${SUDO_USER})

# Copy files to path
mkdir -p /usr/share/PyAudioSelector
chmod +x PyAudioSelector.py
cp PyAudioSelector.py /usr/local/bin/PyAudioSelector
cp config.ini /usr/share/PyAudioSelector

# Copy the autostart entry
mkdir -p ${USER_HOME}/.config/autostart
cp PyAudioSelector.desktop ${USER_HOME}/.config/autostart/

echo "Installation completed"

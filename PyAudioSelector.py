#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from re import findall
from ConfigParser import SafeConfigParser
from subprocess import Popen, PIPE

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, GLib, GObject, Gdk

try:
       from gi.repository import AppIndicator3 as AppIndicator
except:
       from gi.repository import AppIndicator


class AudioSelector:

    def __init__(self, config):

        # Parse the config file
        self.retrieve_config()

        # Create the indicator
        self.ind = AppIndicator.Indicator.new("PyAudioSelector",
                        self.indicator_icon,AppIndicator.IndicatorCategory.OTHER)
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        # Get PulseAudio status
        self.default_device, self.avaiable_devices, self.inputs = self.get_audio_status()

        # Create the menu accordingly, and check periodically for changes
        self.create_menu()
        GLib.timeout_add_seconds(self.refresh_interval, self.handler_check_refresh)

    def get_audio_status(self):
        default_device, avaiable_devices = getPulseAudioDevices()
        inputs = getPulseAudioInputs()
        return (default_device, avaiable_devices, inputs)

    def retrieve_config(self):
        self.refresh_interval  = int(config.get('constants', 'refresh_interval'))
        self.connected_icon    = config.get('constants', 'connected_icon')
        self.disconnected_icon = config.get('constants', 'disconnected_icon')
        self.indicator_icon    = config.get('constants', 'indicator_icon')
        self.settings_command  = config.get('constants', 'settings_command')

    def create_menu(self):
        self.menu = Gtk.Menu()

        # Create the applications section (if any)
        if self.inputs:

            # Applications label
            item = Gtk.MenuItem("‣ Applications")
            item.set_sensitive(False)
            item.show()
            self.menu.append(item)

            # Add a menu entry for each audio input
            for in_id, in_name, in_sink in self.inputs:
                item = Gtk.ImageMenuItem.new_from_stock(in_name, None)
                item.set_label(in_name.title())

                # Add a submenu to select audio device
                submenu = Gtk.Menu()
                item.set_submenu(submenu)

                # Applications label
                sub_item = Gtk.MenuItem("Play on...")
                sub_item.set_sensitive(False)
                sub_item.show()
                submenu.append(sub_item)

                for dev_id, dev_name in self.avaiable_devices:
                    sub_item = Gtk.ImageMenuItem.new_from_stock(self.disconnected_icon, None)
                    sub_item.set_label(dev_name)
                    sub_item.connect("activate", lambda w, iid, did: self.handler_switch_in(iid, did), in_id, dev_id)
                    sub_item.show()
                    submenu.append(sub_item)

                    # Disable current device
                    if dev_id == in_sink:
                        sub_item.set_sensitive(False)
                        sub_item.set_image(Gtk.Image.new_from_stock(self.connected_icon, Gtk.IconSize.MENU))

                item.show()
                self.menu.append(item)

            # Separator
            item = Gtk.SeparatorMenuItem()
            item.show()
            self.menu.append(item)

        # Devices label
        if self.avaiable_devices:
            item = Gtk.MenuItem("‣ Devices")
            item.set_sensitive(False)
            item.show()
            self.menu.append(item)

        # Add a menu entry for each audio device
        for dev_id, dev_name in self.avaiable_devices:
            item = Gtk.ImageMenuItem.new_from_stock(self.disconnected_icon, None)
            item.set_label(dev_name)
            item.connect("activate", lambda w, did: self.handler_switch_all(did), dev_id)
            item.show()
            self.menu.append(item)

            if self.inputs:
                # Disable device if all inputs are set to this device and it's the default_device
                has_all_inputs = all(in_sink == dev_id for in_sink in [inp[2] for inp in self.inputs])
                if has_all_inputs and dev_id == self.default_device:
                    item.set_sensitive(False)
                    item.set_image(Gtk.Image.new_from_stock(self.connected_icon, Gtk.IconSize.MENU))
            else:
                # If there is no inputs, set the connected icon to the default device
                if dev_id == self.default_device:
                    item.set_sensitive(False)
                    item.set_image(Gtk.Image.new_from_stock(self.connected_icon, Gtk.IconSize.MENU))

        # Separator
        item = Gtk.SeparatorMenuItem()
        item.show()
        self.menu.append(item)

        # Open the sound settings
        item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_PREFERENCES, None)
        item.connect("activate", lambda w: self.handler_open_settings())
        item.show()
        self.menu.append(item)

        # Refresh the menu
        item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_REFRESH, None)
        item.connect("activate", lambda w: self.handler_refresh_menu())
        item.show()
        self.menu.append(item)

        # Exit the app
        item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_QUIT, None)
        item.connect("activate", lambda w: self.handler_menu_exit())
        item.show()
        self.menu.append(item)

        # Show the indicator
        self.menu.show()
        self.ind.set_menu(self.menu)

    def handler_switch_in(self, in_id, dev_id):
        # Move sink input to the selected device
        cmd = 'pactl move-sink-input ' + in_id + ' ' + dev_id
        print 'PulseAudio:   ' + cmd
        Popen(cmd, shell=True, stdout=PIPE).communicate()
        self.handler_refresh_menu()

    def handler_switch_all(self, dev_id):
        # Move all sink inputs to the selected device
        for input_id,_,_ in getPulseAudioInputs():
            cmd = 'pactl move-sink-input ' + input_id + ' ' + dev_id
            print 'PulseAudio:   ' + cmd
            Popen(cmd, shell=True, stdout=PIPE).communicate()

        # Set selected device as default
        cmd = 'pacmd set-default-sink ' + dev_id
        print 'PulseAudio:   ' + cmd
        Popen(cmd, shell=True, stdout=PIPE).communicate()

        self.handler_refresh_menu()

    def handler_refresh_menu(self):
        self.default_device, self.avaiable_devices, self.inputs = self.get_audio_status()
        self.menu.destroy()
        self.create_menu()

    def handler_check_refresh(self):
        # Get current status
        tmp_dd, tmp_ad, tmp_i = self.get_audio_status()

        # If something changed, refresh the menu
        if(tmp_dd != self.default_device or
           tmp_ad != self.avaiable_devices or
           tmp_i  != self.inputs):
            self.default_device, self.avaiable_devices, self.inputs = tmp_dd, tmp_ad, tmp_i
            self.menu.destroy()
            self.create_menu()

        # Finally, reset the timer
        GLib.timeout_add_seconds(self.refresh_interval, self.handler_check_refresh)

    def handler_open_settings(self):
         Popen(self.settings_command, shell=True, stdout=PIPE).communicate()

    def handler_menu_exit(self):
        Gtk.main_quit()

    def main(self):
        Gtk.main()


def getPulseAudioDevices():
    raw, _ = Popen('pacmd list-sinks', shell=True, stdout=PIPE).communicate()

    raw_devices = findall(r"(\*?) index: (\d+)", str(raw))
    names = findall(r"device.description = \"(\S.+)\"", str(raw))

    devices = [tup[1] for tup in raw_devices]
    default = [x[1] for x in raw_devices if x[0] is '*'][0]

    return (default, zip(devices, names))


def getPulseAudioInputs():
    raw_inputs, _ = Popen('pacmd list-sink-inputs', shell=True, stdout=PIPE).communicate()

    input_id = findall(r"index: (\d+)", str(raw_inputs))
    input_app_name = findall(r"application.process.binary = \"(\S.+)\"", str(raw_inputs))
    #input_app_icon = findall(r"application.icon_name = \"(\S.+)\"", str(raw_inputs))
    input_sink = findall(r"sink: (\d+)", str(raw_inputs))

    return zip(input_id, input_app_name, input_sink)

if __name__ == "__main__":

    if os.path.dirname(__file__) == "/usr/local/bin":
        config_file = "/usr/share/PyAudioSelector/config.ini"
    elif os.path.dirname(__file__) == ".":
        config_file = "config.ini"
    else:
        print "You don't have a working installation of PyAudioSelector"
        print "See the installation procedure in the README file"
        sys.exit(1)

    config = SafeConfigParser()
    config.read(config_file)

    ind = AudioSelector(config)
    ind.main()

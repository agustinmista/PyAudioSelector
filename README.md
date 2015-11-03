# PyAudioSelector
Python written GTK3 AppIndicator for easy switch between audio devices for
all or some of the audio sources, you even can set different sources to
different audio outputs!

![alt tag](http://i.imgur.com/jtHG9ic.png)

## Instalation
At the moment, you have to clone this repository, and run the installer script as root:

```bash
git clone https://github.com/agustinmista/PyAudioSelector.git
cd PyAudioSelector
sudo sh install.sh
```
If you don't see any icons on the menus, next command should do the trick:

```bash
gsettings set org.gnome.desktop.interface menus-have-icons true
```

It will automatically add the indicator to the autostart folder, so you don't have to start it mannualy every time

## ToDo
* Create an Ubuntu PPA
* Add a section for input devices
* Unninstaller script
* A fancier Readme ;-)

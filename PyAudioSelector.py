from re import findall
from ConfigParser import SafeConfigParser
from subprocess import Popen, PIPE
from gi.repository import Gtk, GLib, GObject, Gdk

try:
       from gi.repository import AppIndicator3 as AppIndicator
except:
       from gi.repository import AppIndicator


class AudioSelector:
    def __init__(self, parser):
        
        self.parser = parser
        self.parse_config()
        
        self.ind = AppIndicator.Indicator.new(
            "PyAudioSelector",                      # Identifier
            self.indicator_icon,                    # Icon
            AppIndicator.IndicatorCategory.OTHER    # Category
        )

        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        
        self.default_device, self.avaiable_devices = getPulseAudioStatus()
        self.inputs = getPulseAudioInputs()
        
        #########################  <MENU>  #########################
        self.menu = Gtk.Menu()
        
        # Add a menu entry for each audio input
        for in_id, in_name, in_icon, in_sink in self.inputs:
            item = Gtk.ImageMenuItem.new_from_stock(in_icon, None)
            item.set_label(in_name.title())
            
            # Add a submenu to select audio device
            submenu = Gtk.Menu()
            item.set_submenu(submenu)
            
            for dev_id, dev_name in self.avaiable_devices:
                sub_item = Gtk.ImageMenuItem.new_from_stock(self.disconnected_icon, None)
                sub_item.set_label(dev_name)
                sub_item.connect("activate", self.handler_switch_in, in_id, dev_id)
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
        
        # Add a menu entry for each audio device
        for dev_id, dev_name in self.avaiable_devices:
            item = Gtk.ImageMenuItem.new_from_stock(self.disconnected_icon, None)
            item.set_label(dev_name)
            item.connect("activate", self.handler_switch_all, dev_id)
            item.show()
            self.menu.append(item)
            
            # Disable device if all inputs are seted to this device
            if all(in_sink == dev_id for in_sink in [inp[3] for inp in self.inputs]):
                item.set_sensitive(False)
                item.set_image(Gtk.Image.new_from_stock(self.connected_icon, Gtk.IconSize.MENU))
            
            # Bracket enclosing default device
            if dev_id == self.default_device:
                item.set_label(self.open_char + dev_name + self.close_char)
                
        # Separator
        item = Gtk.SeparatorMenuItem()
        item.show()
        self.menu.append(item)

        # Refresh the menu
        item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_REFRESH, None)
        item.connect("activate", self.handler_refresh_menu)
        item.show()
        self.menu.append(item)
        
        # Exit the app
        item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_QUIT, None)
        item.connect("activate", self.handler_menu_exit)
        item.show()
        self.menu.append(item)
		
		# Show the indicator
        self.menu.show()
        self.ind.set_menu(self.menu)
        ########################  </MENU>  #########################
        
        # Refresh periodically to catch new inputs/devices
        GLib.timeout_add_seconds(self.refresh_interval, self.refresh)
    
    def parse_config(self):
        self.refresh_interval  = int(parser.get('constants', 'refresh_interval'))
        self.open_char         = parser.get('constants', 'default_device_opening_seq')
        self.close_char        = parser.get('constants', 'default_device_closing_seq')
        self.connected_icon    = parser.get('constants', 'connected_icon')
        self.disconnected_icon = parser.get('constants', 'disconnected_icon')
        self.indicator_icon    = parser.get('constants', 'indicator_icon')
        
    def refresh(self):
        self.handler_refresh_menu(self)
        
    def handler_refresh_menu(self, item):
        self.menu.destroy()
        self.__init__(self.parser)
        
    def handler_switch_in(self, item, in_id, dev_id):
        # Move sink input to the selected device
        cmd = 'pactl move-sink-input ' + in_id + ' ' + dev_id
        Popen(cmd, shell=True, stdout=PIPE).communicate()
        self.handler_refresh_menu(self)

    def handler_switch_all(self, item, dev_id):
        # Move sink inputs to the selected device
        for input_id,_,_,_ in getPulseAudioInputs():
            cmd = 'pactl move-sink-input ' + input_id + ' ' + dev_id
            Popen(cmd, shell=True, stdout=PIPE).communicate()
        
        # Set selected device as default
        cmd = 'pacmd set-default-sink ' + dev_id
        Popen(cmd, shell=True, stdout=PIPE).communicate()
        
        self.handler_refresh_menu(self)

    def handler_menu_exit(self, evt):
        Gtk.main_quit()
		
    def main(self):
        Gtk.main()


def getPulseAudioStatus():
    raw, _ = Popen('pacmd list-sinks', shell=True, stdout=PIPE).communicate()
    
    raw_devices = findall(r"(\*?) index: (\d+)", str(raw))
    names = findall(r"alsa.card_name = \"(\S.+)\"", str(raw))
    
    devices = [tup[1] for tup in raw_devices]
    default = [x[1] for x in raw_devices if x[0] is '*'][0]
    
    return (default, zip(devices, names))


def getPulseAudioInputs():
    raw_inputs, _ = Popen('pacmd list-sink-inputs', shell=True, stdout=PIPE).communicate()
    
    input_id = findall(r"index: (\d+)", str(raw_inputs))
    input_app_name = findall(r"application.process.binary = \"(\S.+)\"", str(raw_inputs))
    input_app_icon = findall(r"application.icon_name = \"(\S.+)\"", str(raw_inputs))
    input_sink = findall(r"sink: (\d+)", str(raw_inputs))

    return zip(input_id, input_app_name, input_app_icon, input_sink)

if __name__ == "__main__":
    
    parser = SafeConfigParser()
    parser.read('config.ini')

    ind = AudioSelector(parser)
    ind.main()

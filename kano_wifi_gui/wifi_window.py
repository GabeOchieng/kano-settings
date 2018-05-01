#
# wifi_window.py
#
# Copyright (C) 2016 - 2018 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Functions for generating the WiFi GUI class
#

import os
import sys

from gi import require_version
require_version('Gtk', '3.0')

from gi.repository import Gtk

from kano.network import is_internet, is_ethernet_plugged, is_device
from kano_networking.ifaces import get_wlan_device
from kano.gtk3.top_bar import TopBar
from kano.gtk3.apply_styles import apply_common_to_screen, \
    apply_styling_to_screen
from kano_settings.get_window import get_window_class


from kano_wifi_gui.RefreshNetworks import RefreshNetworks
from kano_wifi_gui.paths import css_dir, img_dir
from kano_wifi_gui.Template import Template


def create_wifi_gui(is_plug, socket_id, no_confirm_ether=False):
    base_class = get_window_class(is_plug)
    wifi_gui = get_wifi_gui(base_class)

    iface = get_wlan_device()  # this is now redundant, moved to _launch_application
    win = wifi_gui(socket_id=socket_id, wiface=iface, no_confirm_ether=no_confirm_ether)
    win.show_all()
    Gtk.main()


def get_wifi_gui(base_class):

    class KanoWifiGui(base_class):

        CSS_PATH = os.path.join(css_dir, 'kano_wifi_gui.css')
        width = 350
        height = 450

        def __init__(self, wiface='wlan0', socket_id=0, no_confirm_ether=False):

            self.wiface = wiface
            self.network_list = []
            self.no_confirm_ether = no_confirm_ether

            # Default basic styling
            apply_common_to_screen()

            # Attach specific styling
            apply_styling_to_screen(self.CSS_PATH)

            # Set window
            base_class.__init__(
                self,
                _("Kano WiFi"),
                self.width,
                self.height,
                socket_id
            )

            self.top_bar = TopBar(_("Kano WiFi"))
            self.top_bar.set_prev_callback(self.refresh_networks)
            self.top_bar.set_close_callback(Gtk.main_quit)
            self.prev_handler = None
            self.connect('delete-event', Gtk.main_quit)
            self.set_keep_above(True)
            self.set_icon_name('kano-settings')
            self.set_decorated(True)

            if self._base_name == "Window":
                self.set_titlebar(self.top_bar)

            self._launch_application()

        def _launch_application(self, widget=None):
            # Decide whether application prompts user to plug in WiFi dongle
            # or tell them they have ethernet.
            # Don't want to call this function more than once
            self.wiface = get_wlan_device()

            has_internet = is_internet()
            ethernet_plugged = is_ethernet_plugged()
            dongle_is_plugged_in = is_device(self.wiface)

            if has_internet and ethernet_plugged and self.no_confirm_ether:
                sys.exit(0)

            # For testing
            # dongle_is_plugged_in = False
            # ethernet_plugged = True
            # has_internet = False

            if has_internet and ethernet_plugged:
                self._you_are_connected_via_ethernet()

            elif dongle_is_plugged_in:
                if has_internet:
                    self._you_have_internet_screen(self.wiface)
                else:
                    # Refresh the networks list
                    self.refresh_networks()

            else:
                self._plug_in_wifi_dongle()

        def refresh_networks(self, widget=None, event=None):
            RefreshNetworks(self)

        def _plug_in_wifi_dongle(self):
            self.remove_main_widget()
            title = _("You don't seem to have a WiFi dongle\nplugged in.")
            description = _("Plug one in and try again")
            buttons = [
                {
                    'label': ""
                },
                {
                    'label': _("TRY AGAIN"),
                    'color': 'green',
                    'callback': self._launch_application,
                    'type': 'KanoButton',
                    'focus': True
                },
                {
                    'label': _("Skip"),
                    'callback': Gtk.main_quit,
                    'type': 'OrangeButton'
                }
            ]

            img_path = os.path.join(img_dir, "dongle2.png")

            screen = Template(
                title,
                description,
                buttons,
                self.is_plug(),
                img_path
            )
            self.set_main_widget(screen)
            screen.button_grab_focus()
            screen.show_all()

        def _you_are_connected_via_ethernet(self):
            self.remove_main_widget()
            title = _("You are already connected via ethernet.")
            description = _("Do you still want to connect with WiFi?")

            # Decide which callback to use depending on if wifi dongle is
            # plugged in
            buttons = [
                {
                    'label': _("NO"),
                    'color': 'red',
                    'callback': Gtk.main_quit,
                    'type': 'KanoButton'
                },
                {
                    'label': _("YES"),
                    'color': 'green',
                    'callback': self._ethernet_next_step,
                    'type': 'KanoButton',
                    'focus': True
                }
            ]

            img_path = os.path.join(img_dir, "ethernet-2.png")

            screen = Template(
                title,
                description,
                buttons,
                self.is_plug(),
                img_path
            )
            self.set_main_widget(screen)
            screen.button_grab_focus()
            screen.show_all()

        def _ethernet_next_step(self, widget=None):
            dongle_is_plugged_in = is_device(self.wiface)
            if dongle_is_plugged_in:
                self.refresh_networks()
            else:
                self._plug_in_wifi_dongle()

        def _you_have_internet_screen(self, wiface):
            self.remove_main_widget()
            title = _("You already have internet!")
            description = _("Do you want to change network?")
            buttons = [
                {
                    'label': _("NO"),
                    'color': 'red',
                    'callback': Gtk.main_quit,
                    'type': 'KanoButton'
                },
                {
                    'label': _("YES"),
                    'color': 'green',
                    'callback': self.refresh_networks,
                    'type': 'KanoButton',
                    'focus': True
                }
            ]
            img_path = os.path.join(img_dir, "internet.png")

            screen = Template(
                title,
                description,
                buttons,
                self.is_plug(),
                img_path
            )
            self.set_main_widget(screen)
            screen.button_grab_focus()
            screen.show_all()

        def _decide(self):
            if is_device(self.wiface):
                self.refresh_networks()
            else:
                self._plug_in_wifi_dongle()

    return KanoWifiGui

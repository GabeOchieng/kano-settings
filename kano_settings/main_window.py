#
# main_window
#
# Copyright (C) 2015-2018 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Main window class
#

import os
import sys

from gi import require_version
require_version('Gtk', '3.0')

from gi.repository import Gtk

from kano.network import is_internet
from kano.gtk3.apply_styles import apply_styling_to_screen, \
    apply_common_to_screen
from kano.gtk3.kano_combobox import KanoComboBox
from kano.gtk3.scrolled_window import ScrolledWindow
from kano.gtk3.top_bar import TopBar
from kano.gtk3.kano_dialog import KanoDialog
from kano_profile.tracker import track_data

import kano_settings.common as common
from kano_settings.home_screen import HomeScreen
from kano_settings.system.audio import is_HDMI
from kano_settings.config_file import get_setting
from kano_settings.system.display import get_status
from kano_settings.get_window import get_window_class


def generate_main_window(plug, socket_id, screen_id, screen_name,
                         onescreen):
    base_class = get_window_class(plug)
    window_class = get_main_window(base_class)
    window = window_class(screen_id, screen_name, socket_id,
                          onescreen)
    window.show_all()


def get_main_window(base_class):

    class MainWindow(base_class):
        state = 0
        last_level_visited = 0
        width = 680
        height = 405
        CSS_PATH = os.path.join(common.css_dir, 'style.css')

        def __init__(self, screen_number=None, screen_name=None,
                     socket_id=0, onescreen=False):
            # Check for internet, if screen is 12 means no internet
            if screen_number == 12 or screen_name == 'no-internet':
                common.has_internet = False
            else:
                common.has_internet = is_internet()

            # Set combobox styling to the screen
            # Is done here so we don't attach the styling multiple times when
            # switching screens
            apply_styling_to_screen(self.CSS_PATH)
            apply_common_to_screen()
            KanoComboBox.apply_styling_to_screen()
            ScrolledWindow.apply_styling_to_screen(wide=True)

            # Set window
            base_class.__init__(self, _("Settings"), self.width,
                                self.height, socket_id)

            self.set_decorated(True)
            self.top_bar = TopBar(_("Settings"))
            self.top_bar.set_close_callback(self.close_window)
            self.prev_handler = None
            self.set_icon_name('kano-settings')

            if self._base_name == "Window":
                self.set_titlebar(self.top_bar)

            self._onescreen = onescreen

            self.connect('delete-event', Gtk.main_quit)
            # In case we are called from kano-world-launcher, terminate splash
            os.system('kano-stop-splash')
            # Init to Home Screen
            HomeScreen(self, screen_number=screen_number, screen_name=screen_name)

        def clear_win(self):
            self.remove_main_widget()

        def go_to_home(self, widget=None, event=None):
            self.clear_win()

            if self._onescreen:
                sys.exit(0)

            HomeScreen(self)

        def change_prev_callback(self, callback):
            # first time, no event attached
            self.remove_prev_callback()
            self.prev_handler = self.top_bar.prev_button.connect(
                'button-release-event', callback
            )

        def remove_prev_callback(self):
            if self.prev_handler:
                self.top_bar.prev_button.disconnect(self.prev_handler)
                self.prev_handler = None

        def _trigger_tracking_event(self):
            """ Generate a tracker event with some hardware settings.

                This will send a track_date event called 'user-settings'
                with the audio setting, parental lock level and display
                configuration.
            """

            track_data('user-settings', {
                'audio': 'hdmi' if is_HDMI() else 'analog',
                'parental-lock-level': get_setting('Parental-level'),
                'display': get_status()
            })

        # On closing window, will alert if any of the listed booleans are True
        def close_window(self, button, event):
            if common.need_reboot:
                kdialog = KanoDialog(
                    _("Reboot?"),
                    _("Your Kano needs to reboot for changes to apply"),
                    [
                        {
                            'label': _("LATER"),
                            'color': 'grey',
                            'return_value': False
                        },
                        {
                            'label': _("REBOOT NOW"),
                            'color': 'orange',
                            'return_value': True
                        }
                    ],
                    parent_window=self.get_toplevel()
                )

                kdialog.set_action_background('grey')
                do_reboot_now = kdialog.run()
                if do_reboot_now:
                    os.system("sudo systemctl reboot")

            self._trigger_tracking_event()

            Gtk.main_quit()

    return MainWindow

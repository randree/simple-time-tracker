import datetime
import time
from gi.repository import Gtk, GLib
from utils.format import Format
import gi
gi.require_version("Gtk", "3.0")


class StartButton(Gtk.Button):
    def __init__(self, on_start_button_clicked, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_start_button_clicked = on_start_button_clicked

        self.running = False

        self.set_label("Start")
        self.connect("clicked", self.on_button_clicked)

    def set_button_color(self, color_class):
        style_context = self.get_style_context()
        if color_class == "start":
            style_context.remove_class("stop")
            style_context.add_class("start")
        elif color_class == "stop":
            style_context.remove_class("start")
            style_context.add_class("stop")

    def on_button_clicked(self, widget):
        self.on_start_button_clicked(widget)
        if not self.running:
            self.running = True
            self.set_label("Stop")
            self.set_button_color("start")
        else:
            self.running = False
            self.set_label("Start")
            self.set_button_color("stop")
